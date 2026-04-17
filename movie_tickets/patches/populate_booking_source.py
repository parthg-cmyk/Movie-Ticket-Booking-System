import frappe

def execute():
    bookings = frappe.get_all(
        "Ticket Booking",
        filters={
            "booked_by": ["in", ["", None]]
        },
        fields=["name"]
    )

    for b in bookings:
        frappe.db.set_value(
            "Ticket Booking",
            b.name,
            "booked_by",
            "Counter"
        )

    frappe.db.commit()