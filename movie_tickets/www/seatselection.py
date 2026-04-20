import frappe
from frappe.utils import flt


def get_context(context):
	show_name = frappe.form_dict.get("show")

	if not show_name:
		context.error = "No show specified"
		return

	show = frappe.get_doc("Show", show_name)

	if show.available_seats == 0:
		context.error = "Show is sold out"
		return

	context.show_name = show_name
	context.movie_title = show.movie_title
	context.theater = show.theater
	context.screen = show.screen
	context.show_date = str(show.show_date)
	context.start_time = str(show.start_time)
	context.ticket_price = flt(show.ticket_price)
	context.available_seats = show.available_seats
	context.total_seats = show.total_seats

	screen_doc = frappe.get_doc("Screen", show.screen)
	context.seat_rows = screen_doc.seat_rows
	context.seats_per_row = screen_doc.seats_per_row

	context.user_logged_in = frappe.session.user != "Guest"
	if frappe.session.user != "Guest":
		context.customer_name = frappe.session.data.user_fullname or ""
		context.customer_email = frappe.session.data.user_email or ""
