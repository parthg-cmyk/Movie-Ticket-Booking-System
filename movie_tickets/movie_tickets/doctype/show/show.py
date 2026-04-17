# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import getdate, nowdate, get_time,now_datetime,get_datetime


class Show(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        available_seats: DF.Int
        booked_seats: DF.Int
        end_time: DF.Time | None
        movie: DF.Link
        movie_title: DF.Data | None
        screen: DF.Link
        show_date: DF.Date
        show_status: DF.Literal["Scheduled", "Now Playing", "Completed", "Cancelled"]
        start_time: DF.Time
        theater: DF.Link
        ticket_price: DF.Currency
        total_seats: DF.Int
    # end: auto-generated types

    def validate(self):
        self.set_end_time()
        self.validate_show_date()
        self.validate_movie_status()
        self.validate_show_conflicts()

    def on_update(self):
        if self.has_value_changed("show_status"):
            self.handle_show_cancellation()
        
    def before_save(self):
      self.update_show_status()

    def update_show_status(self):
        if self.show_status == "Cancelled":
            return  # don't override manual cancel

        if not self.show_date or not self.start_time or not self.end_time:
            return

        now = now_datetime()
        show_start = get_datetime(f"{self.show_date} {self.start_time}")
        show_end = get_datetime(f"{self.show_date} {self.end_time}")

        if now < show_start:
            self.show_status = "Scheduled"
        elif show_start <= now <= show_end:
            self.show_status = "Now Playing"
        else:
            self.show_status = "Completed"

    def set_end_time(self):
        if self.movie and self.start_time:
            duration_minutes = frappe.db.get_value(
                "Movie", self.movie, "duration_minutes"
            )

            if duration_minutes:
                # Convert safely to time object
                start_time_obj = get_time(self.start_time)

                start_dt = datetime.combine(datetime.today(), start_time_obj)
                end_dt = start_dt + timedelta(minutes=duration_minutes)

                self.end_time = end_dt.time()

    def validate_show_date(self):
        if self.show_date:
            if getdate(self.show_date) < getdate(nowdate()):
                frappe.throw("Show Date cannot be in the past")

    def validate_movie_status(self):
        if self.movie:
            status = frappe.db.get_value("Movie", self.movie, "movie_status")

            if status == "Ended":
                frappe.throw("Cannot schedule show for an Ended movie")

    def validate_show_conflicts(self):
        if not (self.screen and self.show_date and self.start_time and self.end_time):
            return

        current_start = datetime.combine(datetime.today(), get_time(self.start_time))
        current_end = datetime.combine(datetime.today(), get_time(self.end_time))

        existing_shows = frappe.get_all(
            "Show",
            filters={
                "screen": self.screen,
                "show_date": self.show_date,
                "name": ["!=", self.name],
            },
            fields=["name", "start_time", "end_time"],
        )

        for show in existing_shows:
            existing_start = datetime.combine(
                datetime.today(), get_time(show.start_time)
            )
            existing_end = datetime.combine(datetime.today(), get_time(show.end_time))

            if (current_start < existing_end) and (current_end > existing_start):
                frappe.throw(
                    f"Screen {self.screen} already has a show scheduled "
                    f"from {show.start_time} to {show.end_time} on {self.show_date}."
                )

    def handle_show_cancellation(self):
        if self.show_status != "Cancelled":
            return

        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.show_status == "Cancelled":
            return

        bookings = frappe.get_all(
            "Ticket Booking",
            filters={
                "show": self.name,
                "booking_status": ["in", ["Pending", "Confirmed"]],
            },
            fields=["name", "total_amount"],
        )

        for b in bookings:
            booking = frappe.get_doc("Ticket Booking", b.name)

            booking.flags.ignore_validate = True  # ✅ ADD THIS

            booking.booking_status = "Cancelled"
            booking.cancellation_reason = "Show Cancelled"
            booking.refund_amount = booking.total_amount
            booking.payment_status = "Refunded"

            booking.save(ignore_permissions=True)
