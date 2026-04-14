# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr
from frappe.model.naming import make_autoname 



class Theater(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText
		city: DF.Data
		is_active: DF.Check
		phone: DF.Data | None
		theater_name: DF.Data
		total_screens: DF.Int
	# end: auto-generated types

	def autoname(self):
		if not self.theater_name or not self.city:
			frappe.throw("Theater Name and City are required")

		theater = cstr(self.theater_name).strip()
		city = cstr(self.city).strip()
		base_name = f"{theater} - {city}"

        # Ensure unique name
		self.name = base_name
