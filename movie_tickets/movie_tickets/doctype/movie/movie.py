# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate,getdate
import re

class Movie(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cast_details: DF.SmallText | None
		director: DF.Data | None
		duration_minutes: DF.Int
		end_date: DF.Date | None
		genre: DF.Link
		language: DF.Literal["English", "Hindi", "Gujarati", "Tamil", "Telugu", "Other"]
		movie_status: DF.Literal["Upcoming", "Now Showing", "Ended"]
		poster: DF.AttachImage | None
		rating: DF.Literal["U", "UA", "A", "S"]
		release_date: DF.Date
		slug: DF.Data | None
		synopsis: DF.TextEditor | None
		title: DF.Data
		trailer_url: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		self.generate_slug()
		self.set_movie_status()

	def validate(self):
		self.validate_dates()
		self.validate_duration()

	def generate_slug(self):
		if self.title:
			slug = self.title.lower()
			slug = re.sub(r'[^a-z0-9]+', '-', slug) 
			slug = slug.strip('-')             
			self.slug = slug

	def set_movie_status(self):
		today = getdate(nowdate())

		if not self.release_date:
			self.movie_status = "Draft"
			return

		release_date = getdate(self.release_date)
		end_date = getdate(self.end_date) if self.end_date else None

		if today < release_date:
			self.movie_status = "Upcoming"
		elif end_date and today > end_date:
			self.movie_status = "Ended"
		else:
			self.movie_status = "Now Showing"

	def validate_dates(self):
		if self.release_date and self.end_date:
			if getdate(self.end_date) <= getdate(self.release_date):
				frappe.throw("End Date must be greater than Release Date")
				
	def validate_duration(self):
		if self.duration_minutes:
			if not (1 <= self.duration_minutes <= 600):
				frappe.throw("Duration must be between 1 and 600 minutes")

	
