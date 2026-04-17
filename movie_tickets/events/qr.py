import frappe
import qrcode
import io
from frappe.utils.file_manager import save_file


def generate_booking_qr(doc):
    """
    Generate QR code for a Ticket Booking and attach to document
    """

    # 🔹 QR data (keep it concise but useful)
    qr_data = f"""
    Booking ID: {doc.name}
    Movie: {doc.movie_title}
    Show: {doc.show}
    Date: {doc.show_date}
    Time: {doc.start_time}
    Seats: {", ".join([d.seat_label for d in doc.seats])}
    """

    # 🔹 Generate QR image
    qr = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    file_name = f"{doc.name}_qr.png"

    # 🔹 Save as File in Frappe
    file_doc = save_file(
        file_name,
        buffer.getvalue(),
        doc.doctype,
        doc.name,
        is_private=0
    )

    return file_doc