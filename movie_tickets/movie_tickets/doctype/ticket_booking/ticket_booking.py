# Copyright (c) 2026, Parth Godhani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re
from frappe.utils import now_datetime, get_datetime
from datetime import timedelta


class TicketBooking(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from movie_tickets.movie_tickets.doctype.booked_seat.booked_seat import (
            BookedSeat,
        )

        amended_from: DF.Link | None
        booked_by: DF.Link | None
        booking_status: DF.Literal["Pending", "Confirmed", "Cancelled", "Expired"]
        booking_time: DF.Datetime | None
        cancellation_reason: DF.SmallText | None
        cancellation_time: DF.Datetime | None
        customer_email: DF.Data
        customer_name: DF.Data
        customer_phone: DF.Data
        movie_title: DF.Data | None
        number_of_seats: DF.Int
        payment_status: DF.Literal["Unpaid", "Paid", "Refunded"]
        price_per_seat: DF.Currency
        refund_amount: DF.Currency
        screen: DF.Data | None
        seats: DF.Table[BookedSeat]
        show: DF.Link
        show_date: DF.Date | None
        start_time: DF.Time | None
        theater: DF.Data | None
        total_amount: DF.Currency
    # end: auto-generated types

    def validate(self):
        self.validate_show_status()
        self.validate_seat_availability()
        self.validate_duplicate_seats()
        self.validate_seat_format_and_range()
        self.calculate_totals()
        self.validate_seat_limits()

    def on_submit(self):
        self.update_booking_status()
        self.update_show_seats()

    def update_show_seats(self):
        if not self.show or not self.number_of_seats:
            return

        frappe.db.sql(
            """
                UPDATE `tabShow`
                SET
                    booked_seats = COALESCE(booked_seats, 0) + %s,
                    available_seats = COALESCE(available_seats, 0) - %s
                WHERE name = %s """,
            (self.number_of_seats, self.number_of_seats, self.show),
        )

    def update_booking_status(self):
        self.booking_status = "Confirmed"
        self.payment_status = "Paid"

    def validate_show_status(self):
        show_status = frappe.db.get_value("Show", self.show, "show_status")

        if not (show_status == "Scheduled" or show_status == "Now Playing"):
            frappe.throw(f"Cannot book tickets for a {show_status.lower()} show")

    def validate_duplicate_seats(self):
        seats = [d.seat_label for d in self.seats if d.seat_label]

        if len(seats) != len(set(seats)):
            frappe.throw("Duplicate seats selected in booking")

    def validate_seat_format_and_range(self):
        if not self.screen:
            return

        screen = frappe.get_doc("Screen", self.screen)

        max_rows = screen.seat_rows
        max_cols = screen.seats_per_row

        pattern = re.compile(r"^[A-Z]-\d+$")

        for d in self.seats:
            if not d.seat_label:
                continue

            if not pattern.match(d.seat_label):
                frappe.throw(f"Invalid seat format: {d.seat_label}. Use format A-12")

            row_letter, seat_number = d.seat_label.split("-")
            seat_number = int(seat_number)

            # Convert row letter → number (A=1, B=2...)
            row_index = ord(row_letter) - ord("A") + 1

            if row_index < 1 or row_index > max_rows:
                frappe.throw(f"Row {row_letter} exceeds screen row limit ({max_rows})")

            if seat_number < 1 or seat_number > max_cols:
                frappe.throw(
                    f"Seat number {seat_number} exceeds per row limit ({max_cols})"
                )

    def validate_seat_availability(self):
        if not self.show or not self.seats:
            return

        selected_seats = [d.seat_label for d in self.seats if d.seat_label]

        if not selected_seats:
            return

        conflict = frappe.db.sql(
            """
            SELECT bs.seat_label
            FROM `tabBooked Seat` bs
            JOIN `tabTicket Booking` b ON b.name = bs.parent
            WHERE b.show = %s
              AND b.booking_status IN ('Pending', 'Confirmed')
              AND bs.seat_label IN %s
              AND b.name != %s
        """,
            (self.show, tuple(selected_seats), self.name),
            as_dict=1,
        )

        if conflict:
            frappe.throw(
                f"Seat {conflict[0].seat_label} is already booked for this show."
            )

    def calculate_totals(self):
        self.number_of_seats = len(self.seats or [])

        if self.price_per_seat:
            self.total_amount = self.number_of_seats * self.price_per_seat
        else:
            self.total_amount = 0

    def validate_seat_limits(self):
        if self.number_of_seats < 1:
            frappe.throw("At least 1 seat must be selected")

        if self.number_of_seats > 10:
            frappe.throw("Maximum 10 seats allowed per booking")

    def on_cancel(self):
        self.handle_cancellation()

    def handle_cancellation(self):
        cancellation_time = now_datetime()

        self.calculate_refund()

        # Persist values safely
        self.db_set(
            {
                "booking_status": "Cancelled",
                "cancellation_time": cancellation_time,
                "refund_amount": self.refund_amount,
                "payment_status": self.payment_status,
            }
        )

        # 4. Update show seats
        self.update_show_seats_on_cancel()

    def calculate_refund(self):
        if not self.show:
            self.refund_amount = 0
            self.payment_status = "No Refund"
            return

        show = frappe.get_doc("Show", self.show)

        if not show.show_date or not show.start_time:
            self.refund_amount = 0
            self.payment_status = "No Refund"
            return

        show_datetime = get_datetime(f"{show.show_date} {show.start_time}")
        now = now_datetime()

        diff = show_datetime - now
        hours_left = diff.total_seconds() / 3600

        if hours_left > 4:
            refund = self.total_amount
            self.payment_status = "Refunded"

        elif 2 <= hours_left <= 4:
            refund = self.total_amount * 0.5
            self.payment_status = "Partially Refunded"

        else:
            refund = 0
            self.payment_status = "No Refund"

        self.refund_amount = refund

    def update_show_seats_on_cancel(self):
        if not self.show or not self.number_of_seats:
            return

        frappe.db.sql(
            """
            UPDATE `tabShow`
            SET
                booked_seats = COALESCE(booked_seats, 0) - %s,
                available_seats = COALESCE(available_seats, 0) + %s
            WHERE name = %s
        """,
            (self.number_of_seats, self.number_of_seats, self.show),
        )
