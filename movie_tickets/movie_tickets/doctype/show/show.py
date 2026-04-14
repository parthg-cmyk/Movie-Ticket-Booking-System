# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import getdate,nowdate


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

    def before_save(self):
        self.set_end_time()
        
    def validate(self):
        self.validate_show_date()
        self.validate_movie_status()
        self.validate_show_conflicts()
        
    def on_update(self):
        self.handle_show_cancellation()


    def set_end_time(self):
        if self.movie:
            duration_minutes = frappe.db.get_value(
                "Movie", self.movie, "duration_minutes"
            )
            if self.start_time and duration_minutes:
                            start = datetime.strptime(str(self.start_time), "%H:%M:%S")
                            
                            end = start + timedelta(minutes=duration_minutes)
                            
                            self.end_time = end.time()
                            
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

        # Convert current show time to datetime
        current_start = datetime.strptime(str(self.start_time), "%H:%M:%S")
        current_end = datetime.strptime(str(self.end_time), "%H:%M:%S")

        # Fetch existing shows on same screen + date
        existing_shows = frappe.get_all(
            "Show",
            filters={
                "screen": self.screen,
                "show_date": self.show_date,
                "name": ["!=", self.name]  # exclude self (for update)
            },
            fields=["name", "start_time", "end_time"]
        )

        for show in existing_shows:
            existing_start = datetime.strptime(str(show.start_time), "%H:%M:%S")
            existing_end = datetime.strptime(str(show.end_time), "%H:%M:%S")

            # Overlap condition
            if (current_start < existing_end) and (current_end > existing_start):
                frappe.throw(
                    f"Screen {self.screen} already has a show scheduled "
                    f"from {show.start_time} to {show.end_time} on {self.show_date}."
                )
                
    def handle_show_cancellation(self):
        # Check if status changed to Cancelled
        if self.show_status != "Cancelled":
            return

        # Get previous value (important)
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.show_status == "Cancelled":
            return  # already cancelled before

        # Fetch affected bookings
        bookings = frappe.get_all(
            "Booking",
            filters={
                "show": self.name,
                "booking_status": ["in", ["Pending", "Confirmed"]]
            },
            fields=["name", "total_amount"]
        )

        for b in bookings:
            booking = frappe.get_doc("Booking", b.name)

            # Update booking fields
            booking.booking_status = "Cancelled"
            booking.cancellation_reason = "Show Cancelled"
            booking.refund_amount = booking.total_amount
            booking.payment_status = "Refunded"

            booking.save(ignore_permissions=True)