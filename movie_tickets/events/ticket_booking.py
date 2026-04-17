import frappe
from movie_tickets.events.qr import generate_booking_qr


def after_insert_booking(doc, method):
    expiry_minutes = (
        frappe.db.get_single_value("Booking Configuration", "booking_expiry_minutes")
        or 10
    )

    subject = f"Booking Received - {doc.name}"
    message = f"""
    <p>Your booking <b>{doc.name}</b> for <b>{doc.movie_title}</b> has been received.</p>
    <p>Please complete payment within <b>{expiry_minutes} minutes</b>.</p>
    """

    frappe.sendmail(recipients=[doc.customer_email], subject=subject, message=message)


def on_submit_booking(doc, method):
    if not doc.customer_email:
        return

    subject = f"Booking Confirmed - {doc.name}"

    file_doc = generate_booking_qr(doc)

    # 🔹 Extract seat numbers from child table
    seat_list = []
    for row in doc.seats:
        seat_list.append(row.seat_label)  # adjust field if different

    seats_str = ", ".join(seat_list)

    # 🔹 Format show datetime
    show_datetime = (
        f"{doc.show_date} {doc.start_time}"
        if doc.show_date and doc.start_time
        else "N/A"
    )

    message = f"""
    <h3>Booking Confirmation</h3>
    <p><b>Booking ID:</b> {doc.name}</p>
    <p><b>Customer:</b> {doc.customer_name}</p>
    <p><b>Movie:</b> {doc.movie_title}</p>
    <p><b>Theater:</b> {doc.theater}</p>
    <p><b>Screen:</b> {doc.screen}</p>
    <p><b>Show Time:</b> {show_datetime}</p>
    <p><b>Seats:</b> {seats_str}</p>
    <p><b>Total Amount:</b> ₹{doc.total_amount}</p>
    <p><b>Payment Status:</b> {doc.payment_status}</p>

    """

    frappe.sendmail(
        recipients=[doc.customer_email],
        subject=subject,
        message=message,
        attachments=[{"fname": file_doc.file_name, "fcontent": file_doc.get_content()}],
        now=False,
    )
