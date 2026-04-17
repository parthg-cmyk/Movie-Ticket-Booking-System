import frappe
from frappe.utils import flt

def execute():
    # 🔹 Get booked seats per show
    bookings = frappe.db.sql("""
        SELECT
            tb.show,
            SUM(tb.number_of_seats) AS booked_seats
        FROM `tabTicket Booking` tb
        WHERE tb.docstatus = 1
          AND tb.booking_status = 'Confirmed'
        GROUP BY tb.show
    """, as_dict=True)

    booking_map = {b.show: flt(b.booked_seats) for b in bookings}

    shows = frappe.get_all("Show", fields=["name", "total_seats"])

    for show in shows:
        booked_seats = booking_map.get(show.name, 0)
        total_seats = flt(show.total_seats)

        available_seats = max(total_seats - booked_seats, 0)

        frappe.db.set_value(
            "Show",
            show.name,
            {
                "booked_seats": booked_seats,
                "available_seats": available_seats
            }
        )

    frappe.db.commit()