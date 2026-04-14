# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


class Screen(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		base_price: DF.Currency
		is_active: DF.Check
		screen_name: DF.Data
		screen_type: DF.Literal["Standard", "IMAX", "3D", "4DX"]
		seat_rows: DF.Int
		seats_per_row: DF.Int
		theater: DF.Link
		total_seats: DF.Int
	# end: auto-generated types

	def validate(self):
		self.validate_total_seats()
	
	def after_insert(self):
		self.update_theater_screen_count()

	def on_update(self):
		self.update_theater_screen_count()

	def on_trash(self):
		self.update_theater_screen_count()

	def validate_total_seats(self):
		if self.seat_rows and self.seats_per_row:
			expected = self.seat_rows * self.seats_per_row
			
			if self.total_seats != expected:
				frappe.throw(
                    f"Total Seats must be {expected} (seat_rows × seats_per_row)"
                )
	
	def update_theater_screen_count(self):
		if self.theater:
			count = frappe.db.count("Screen",{"theater" : self.theater})

			frappe.db.set_value("Theater" , self.theater , "total_screens" , count)

	def autoname(self):
		if not self.theater or not self.screen_name:
			frappe.throw("Theater and Screen Name are required")

		theater = cstr(self.theater).strip()
		screen_name = cstr(self.screen_name).strip()
		base_name = f"{theater}-{screen_name}"

        # Ensure unique name
		self.name = base_name