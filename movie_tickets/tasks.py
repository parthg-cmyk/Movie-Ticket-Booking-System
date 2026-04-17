import frappe
from frappe.utils import now_datetime, add_to_date
from frappe.utils import nowdate, nowtime


def expire_unpaid_bookings():

    expiry_minutes = 15

    cutoff_time = add_to_date(now_datetime(), minutes=-expiry_minutes)

    bookings = frappe.get_all(
        "Ticket Booking",
        filters={
            "booking_status": "Pending",
            "payment_status": "Unpaid",
            "booking_time": ["<", cutoff_time],
        },
        fields=["name", "show", "number_of_seats"],
    )

    for b in bookings:
        try:
            doc = frappe.get_doc("Ticket Booking", b.name)

            doc.booking_status = "Expired"
            doc.save(ignore_permissions=True)

            # 🎬 Release seats
            frappe.db.sql(
                """
                UPDATE `tabShow`
                SET 
                    booked_seats = GREATEST(COALESCE(booked_seats, 0) - %s, 0),
                    available_seats = COALESCE(available_seats, 0) + %s
                WHERE name = %s
            """,
                (doc.number_of_seats, doc.number_of_seats, doc.show),
            )

        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Expire Booking Failed: {b.name}")

    frappe.db.commit()


def update_movie_status():
    today = nowdate()

    movies = frappe.get_all("Movie", fields=["name", "release_date", "end_date"])

    for m in movies:
        try:
            status = "Upcoming"

            if m.release_date and m.end_date:
                if today < str(m.release_date):
                    status = "Upcoming"

                elif str(m.release_date) <= today <= str(m.end_date):
                    status = "Now Showing"

                elif today > str(m.end_date):
                    status = "Ended"

            # 🔄 Update only if changed
            frappe.db.set_value("Movie", m.name, "movie_status", status)

        except Exception:
            frappe.log_error(
                frappe.get_traceback(), f"Movie Status Update Failed: {m.name}"
            )


def update_show_status():
    today = nowdate()
    current_time = nowtime()

    shows = frappe.get_all(
        "Show", fields=["name", "show_date", "start_time", "end_time", "show_status"]
    )

    for s in shows:
        try:
            new_status = "Scheduled"

            # ✅ Past date → Completed
            if s.show_date and str(s.show_date) < today:
                new_status = "Completed"

            # ✅ Today logic
            elif s.show_date and str(s.show_date) == today:

                if s.start_time and s.end_time:

                    if str(s.start_time) <= current_time <= str(s.end_time):
                        new_status = "Now Playing"

                    elif current_time > str(s.end_time):
                        new_status = "Completed"

                    else:
                        new_status = "Scheduled"

            # ✅ Update only if changed
            if s.show_status != new_status:
                frappe.db.set_value("Show", s.name, "show_status", new_status)

        except Exception:
            frappe.log_error(
                frappe.get_traceback(), f"Show Status Update Failed: {s.name}"
            )


def send_daily_revenue_digest():

    today = nowdate()

    try:
        # 📊 Get Revenue Data
        data = frappe.db.sql(
            """
            SELECT
                COUNT(tb.name) as total_bookings,
                SUM(tb.total_amount) as total_revenue,
                SUM(tb.number_of_seats) as total_seats_sold
            FROM `tabTicket Booking` tb
            WHERE tb.booking_status = 'Confirmed'
              AND DATE(tb.booking_time) = %s
        """,
            (today,),
            as_dict=True,
        )[0]

        # 🎬 Top Movie
        top_movie = frappe.db.sql(
            """
            SELECT
                tb.movie_title,
                SUM(tb.total_amount) as revenue
            FROM `tabTicket Booking` tb
            WHERE tb.booking_status = 'Confirmed'
              AND DATE(tb.booking_time) = %s
            GROUP BY tb.movie_title
            ORDER BY revenue DESC
            LIMIT 1
        """,
            (today,),
            as_dict=True,
        )

        top_movie_name = top_movie[0].movie_title if top_movie else "N/A"
        top_movie_revenue = top_movie[0].revenue if top_movie else 0

        # 🧾 Safe values
        total_bookings = data.total_bookings or 0
        total_revenue = data.total_revenue or 0
        total_seats = data.total_seats_sold or 0

        # 📧 Get Cinema Managers
        recipients = frappe.get_all(
            "Has Role", filters={"role": "Cinema Manager"}, pluck="parent"
        )

        if not recipients:
            return

        # 🎨 HTML Email
        message = f"""
        <div style="font-family:Arial;padding:20px;">
            <h2>📊 Daily Revenue Report ({today})</h2>

            <table style="border-collapse:collapse;width:100%;margin-top:15px;">
                <tr>
                    <td><b>Total Bookings</b></td>
                    <td>{total_bookings}</td>
                </tr>
                <tr>
                    <td><b>Total Revenue</b></td>
                    <td>₹{total_revenue}</td>
                </tr>
                <tr>
                    <td><b>Total Seats Sold</b></td>
                    <td>{total_seats}</td>
                </tr>
                <tr>
                    <td><b>Top Movie</b></td>
                    <td>{top_movie_name} (₹{top_movie_revenue})</td>
                </tr>
            </table>

            <br>
            <p style="color:gray;">Auto-generated report from Movie Ticket System</p>
        </div>
        """

        # 📧 Send Email
        frappe.sendmail(
            recipients=recipients,
            subject=f"🎬 Daily Revenue Digest - {today}",
            message=message,
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Daily Revenue Digest Failed")
