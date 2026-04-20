import frappe


def get_context(context):

    # 🔒 Restrict guest access
    if frappe.session.user == "Guest":
        frappe.msgprint("Please login to view your bookings")
        frappe.redirect('/login')

    # 🎟 Fetch bookings
    bookings = frappe.get_all(
        "Ticket Booking",
        filters={
            "owner": frappe.session.user
        },
        fields=[
            "name",
            "movie_title",
            "show_date",
            "start_time",
            "total_amount",
            "booking_status"
        ],
        order_by="creation desc"
    )

    # 🔥 Get seat details
    for b in bookings:
        seats = frappe.get_all(
            "Booked Seat",
            filters={
                "parent": b.name
            },
            fields=["seat_label"]
        )

        b["seats"] = ", ".join([s.seat_label for s in seats])

    context.bookings = bookings