import frappe
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from frappe import _


@frappe.whitelist()
def get_booked_seats(show: str) -> list:

    bookings = frappe.get_all(
        "Ticket Booking", filters={"show": show, "docstatus": 1}, pluck="name"
    )

    if not bookings:
        return []

    seats = frappe.get_all(
        "Booked Seat",
        filters={"parent": ["in", bookings], "parenttype": "Ticket Booking"},
        fields=["row_letter", "seat_number"],
    )

    return [
        f"{s.row_letter}-{s.seat_number}"
        for s in seats
        if s.row_letter and s.seat_number
    ]


@frappe.whitelist()
def send_booking_confirmation(booking: str) -> None:
    doc = frappe.get_doc("Ticket Booking", booking)

    frappe.sendmail(
        recipients=[doc.customer_email],
        subject="Booking Confirmation",
        message=f"""
        Hi {doc.customer_name},<br><br>
        Your booking is confirmed.<br>
        Seats: {', '.join([s.seat_label for s in doc.seats])}<br>
        Total: ₹{doc.total_amount}<br><br>
        Enjoy your movie!
        """,
    )


@frappe.whitelist()
def cancel_booking(booking: str) -> bool:
    doc = frappe.get_doc("Ticket Booking", booking)

    doc.booking_status = "Cancelled"
    doc.cancellation_time = frappe.utils.now()

    # simple refund logic
    doc.refund_amount = doc.total_amount

    doc.save()
    return True


@frappe.whitelist()
def get_seat_availability(show_name: str) -> Dict:
    show = frappe.get_doc("Show", show_name)
    screen = frappe.get_doc("Screen", show.screen)

    rows = screen.seat_rows
    cols = screen.seats_per_row

    # Get booked seats (Confirmed + Pending)
    booked_seats = frappe.db.sql(
        """
        SELECT bs.row_letter, bs.seat_number
        FROM `tabBooked Seat` bs
        JOIN `tabTicket Booking` tb ON bs.parent = tb.name
        WHERE tb.show = %s
        AND tb.docstatus < 2
    """,
        (show_name,),
        as_dict=True,
    )

    booked_set = {f"{s.row_letter}-{s.seat_number}" for s in booked_seats}

    # Build 2D seat map
    seat_map = []

    for r in range(1, rows + 1):
        row_letter = chr(64 + r)
        row_data = []

        for c in range(1, cols + 1):
            seat_label = f"{row_letter}-{c}"

            row_data.append(
                {
                    "seat_label": seat_label,
                    "status": "booked" if seat_label in booked_set else "available",
                }
            )

        seat_map.append(row_data)

    return {"rows": rows, "seats_per_row": cols, "seats": seat_map}


@frappe.whitelist(allow_guest=False)
def create_booking(
    show: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    seats: List[str],
) -> Dict:

    if not seats:
        frappe.throw("Please select at least one seat")

    # 🔒 Lock Show (prevents race condition)
    frappe.db.sql("SELECT name FROM `tabShow` WHERE name=%s FOR UPDATE", show)

    # Check already booked seats
    existing = frappe.db.sql(
        """
        SELECT CONCAT(bs.row_letter, '-', bs.seat_number) AS seat
        FROM `tabBooked Seat` bs
        JOIN `tabTicket Booking` tb ON bs.parent = tb.name
        WHERE tb.show = %s
        AND tb.docstatus < 2
    """,
        (show,),
        as_dict=True,
    )

    booked_set = {d.seat for d in existing}

    conflict = [s for s in seats if s in booked_set]

    if conflict:
        frappe.throw(f"Seats already booked: {', '.join(conflict)}")

    show_doc = frappe.get_doc("Show", show)
    price = show_doc.ticket_price

    # Create booking
    booking = frappe.new_doc("Ticket Booking")
    booking.show = show
    booking.customer_name = customer_name
    booking.customer_email = customer_email
    booking.customer_phone = customer_phone
    booking.number_of_seats = len(seats)
    booking.total_amount = len(seats) * price
    booking.booking_status = "Pending"

    for seat in seats:
        row_letter, seat_number = seat.split("-")

        booking.append(
            "seats",
            {
                "seat_label": seat,
                "row_letter": row_letter,
                "seat_number": int(seat_number),
                "seat_price": price,
            },
        )

    booking.insert(ignore_permissions=True)

    return {
        "success": True,
        "booking_name": booking.name,
        "total_amount": booking.total_amount,
        "message": "Booking created. Complete payment within 15 minutes.",
    }


@frappe.whitelist(allow_guest=True)
def get_shows_for_movie(
    movie: str, city: Optional[str] = None, date: Optional[str] = None
) -> List[Dict]:

    filters = {"movie": movie, "show_status": ["in", ["Scheduled", "Now Playing"]]}

    if date:
        filters["show_date"] = date

    shows = frappe.get_all(
        "Show",
        filters=filters,
        fields=[
            "name as show_name",
            "theater",
            "screen",
            "show_date",
            "start_time",
            "ticket_price",
            "available_seats",
        ],
    )

    # Optional city filter (via Theater)
    if city:
        shows = [
            s
            for s in shows
            if frappe.db.get_value("Theater", s["theater"], "city") == city
        ]

    # Add screen_type
    for s in shows:
        s["screen_type"] = frappe.db.get_value("Screen", s["screen"], "screen_type")

    return shows


@frappe.whitelist()
def get_revenue_summary(
    theater: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict:

    conditions = "WHERE tb.docstatus = 1"
    params = {}

    if theater:
        conditions += " AND s.theater = %(theater)s"
        params["theater"] = theater

    if from_date:
        conditions += " AND s.show_date >= %(from_date)s"
        params["from_date"] = from_date

    if to_date:
        conditions += " AND s.show_date <= %(to_date)s"
        params["to_date"] = to_date

    data = frappe.db.sql(
        f"""
        SELECT 
            COUNT(DISTINCT tb.name) AS total_bookings,
            SUM(tb.total_amount) AS total_revenue,
            SUM(tb.number_of_seats) AS total_seats_sold,
            AVG(
                (tb.number_of_seats / s.total_seats) * 100
            ) AS avg_occupancy_pct
        FROM `tabTicket Booking` tb
        JOIN `tabShow` s ON tb.show = s.name
        {conditions}
    """,
        params,
        as_dict=True,
    )[0]

    # Top movie by revenue
    top_movie = frappe.db.sql(
        f"""
        SELECT s.movie_title, SUM(tb.total_amount) AS revenue
        FROM `tabTicket Booking` tb
        JOIN `tabShow` s ON tb.show = s.name
        {conditions}
        GROUP BY s.movie_title
        ORDER BY revenue DESC
        LIMIT 1
    """,
        params,
        as_dict=True,
    )

    return {
        "total_bookings": data.total_bookings or 0,
        "total_revenue": data.total_revenue or 0,
        "total_seats_sold": data.total_seats_sold or 0,
        "avg_occupancy_pct": round(data.avg_occupancy_pct or 0, 2),
        "top_movie": top_movie[0].movie_title if top_movie else None,
    }


import frappe
from frappe import _
from typing import List, Union
from datetime import datetime, timedelta
from frappe.utils.typing_validations import validate_argument_types

# ==============================
# ✅ WHITELISTED API METHOD
# ==============================


@frappe.whitelist()
@validate_argument_types
def create_bulk_shows(
    movie: str,
    screens: Union[str, List[str]],
    from_date: str,
    to_date: str,
    show_times: Union[str, List[str]],
) -> dict:
    """
    Create bulk shows using background job

    Args:
        movie (str): Movie name
        screens (List[str] or JSON string)
        from_date (str): YYYY-MM-DD
        to_date (str): YYYY-MM-DD
        show_times (List[str] or JSON string): ["10:00", "14:00"]

    Returns:
        dict: status response
    """

    # Handle JSON string input (if any)
    if isinstance(screens, str):
        screens = frappe.parse_json(screens)

    if isinstance(show_times, str):
        show_times = frappe.parse_json(show_times)

    # ✅ Basic Validation
    if not screens:
        frappe.throw(_("Please select at least one screen"))

    if not show_times:
        frappe.throw(_("Please provide show times"))

    if from_date > to_date:
        frappe.throw(_("From Date cannot be greater than To Date"))

    # ✅ Enqueue background job
    frappe.enqueue(
        method="movie_tickets.api.process_bulk_shows",
        queue="long",
        timeout=600,
        movie=movie,
        screens=screens,
        from_date=from_date,
        to_date=to_date,
        show_times=show_times,
    )

    return {"status": "queued", "message": "Bulk show creation started in background"}


# ==============================
# ⚙️ BACKGROUND JOB
# ==============================


def process_bulk_shows(
    movie: str, screens: List[str], from_date: str, to_date: str, show_times: List[str]
):
    """
    Background job to create shows in bulk
    """

    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()

    total_created = 0
    total_skipped = 0

    current_date = from_date_obj

    while current_date <= to_date_obj:

        for screen in screens:

            for time_str in show_times:

                try:
                    start_time = datetime.strptime(time_str, "%H:%M").time()
                except ValueError:
                    frappe.log_error(f"Invalid time format: {time_str}")
                    continue

                # ✅ Avoid duplicate shows
                exists = frappe.db.exists(
                    "Show",
                    {
                        "movie": movie,
                        "screen": screen,
                        "show_date": current_date,
                        "start_time": start_time,
                    },
                )

                if exists:
                    total_skipped += 1
                    continue

                # ✅ Create Show Doc
                doc = frappe.get_doc(
                    {
                        "doctype": "Show",
                        "movie": movie,
                        "screen": screen,
                        "show_date": current_date,
                        "start_time": start_time,
                    }
                )

                doc.insert(ignore_permissions=True)
                total_created += 1

        current_date += timedelta(days=1)

    frappe.db.commit()

    # ✅ Logging
    frappe.logger().info(
        f"Bulk Show Creation Completed | Created: {total_created}, Skipped: {total_skipped}"
    )

    # ✅ Optional: realtime notification
    frappe.publish_realtime(
        event="bulk_show_creation_done",
        message={"created": total_created, "skipped": total_skipped},
    )
