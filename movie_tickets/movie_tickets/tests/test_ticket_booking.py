import frappe
from frappe.tests.utils import FrappeTestCase
from datetime import timedelta
from frappe.utils import now_datetime,get_datetime

class TestBooking(FrappeTestCase):

    def setUp(self):
        # Create Theater
        unique = frappe.generate_hash(length=6)

        self.theater = frappe.get_doc(
            {
                "doctype": "Theater",
                "theater_name": f"Test Theater {unique}",
                "city": "Test City",
                "address": "Test Address",
            }
        ).insert()

        # Create Screen with 100 seats
        self.screen = frappe.get_doc(
            {
                "doctype": "Screen",
                "screen_name": "Screen 1",
                "theater": self.theater.name,
                "total_seats": 100,
                "seat_rows": 10,
                "seats_per_row": 10,
                "base_price": 200,
            }
        ).insert()

        # Create Movie
        self.movie = frappe.get_doc(
            {
                "doctype": "Movie",
                "title": f"Test Movie {unique}",
                "language": "English",
                "genre": "Action",  # make sure this exists
                "duration_minutes": 120,
                "release_date": "2024-01-01",
            }
        ).insert()

        # Create Show
        self.show = frappe.get_doc(
            {
                "doctype": "Show",
                "movie": self.movie.name,
                "screen": self.screen.name,
                "show_date": "2026-04-20",
                "start_time": "10:00:00",
            }
        ).insert()

    def test_booking_decreases_available_seats(self):
        # Reload show to get fetched values
        show = frappe.get_doc("Show", self.show.name)

        self.assertEqual(show.available_seats, 100)
        self.assertEqual(show.booked_seats, 0)

        # Simulate booking 3 seats
        seats_to_book = 3

        frappe.db.sql(
            """
            UPDATE `tabShow`
            SET
                booked_seats = booked_seats + %s,
                available_seats = available_seats - %s
            WHERE name = %s
        """,
            (seats_to_book, seats_to_book, show.name),
        )

        # Reload and assert
        show.reload()

        self.assertEqual(show.available_seats, 97)
        self.assertEqual(show.booked_seats, 3)
        print(show.available_seats, show.booked_seats)

    def test_cannot_book_already_taken_seat(self):
        # First booking → seat A-1
        booking1 = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "customer_name": "customer1",
                "customer_email": "c1@gmail.com",
                "customer_phone": "12345",
                "number_of_seats": 1,
                "seats": [{"seat_number": "1", "seat_label": "A-1", "row_letter": "A"}],
            }
        ).insert()

        booking1.submit()

        # Second booking → same seat A-1
        booking2 = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "number_of_seats": 1,
                "seats": [{"seat_number": "A-1"}],
            }
        )

        # Expect ValidationError
        self.assertRaises(frappe.ValidationError, booking2.insert)

    def test_cannot_book_for_cancelled_show(self):
        self.show.show_status = "Cancelled"
        self.show.save()

        booking = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "customer_name": "customer1",
                "customer_email": "c1@gmail.com",
                "customer_phone": "12345",
                "number_of_seats": 1,
                "seats": [{"seat_number": "2", "seat_label": "A-2", "row_letter": "A"}],
            }
        )

        with self.assertRaises(frappe.ValidationError) as cm:
            booking.insert()

        print(str(cm.exception))

    def test_max_seats_per_booking_limit(self):
        seats = []

        for i in range(1, 11):
            seats.append(
                {"seat_number": str(i), "seat_label": f"A-{i}", "row_letter": "A"}
            )

        seats.append({"seat_number": "1", "seat_label": "B-1", "row_letter": "B"})

        booking = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "customer_name": "customer1",
                "customer_email": "c1@gmail.com",
                "customer_phone": "12345",
                "seats": seats,
            }
        )

        with self.assertRaises(frappe.ValidationError) as cm:
            booking.insert()

        self.assertIn("Maximum 10 seats allowed per booking", str(cm.exception))


    def test_full_refund_on_early_cancellation(self):
        future_time = now_datetime() + timedelta(hours=6)

        self.show.show_date = future_time.date()
        self.show.start_time = future_time.time()
        self.show.save()

        booking = frappe.get_doc({
            "doctype": "Ticket Booking",
            "show": self.show.name,
            "customer_name": "customer1",
            "customer_email": "c1@gmail.com",
            "customer_phone": "12345",
            "seats": [{"seat_label": "A-1","row_letter":"A", "seat_number":1}],
            "price_per_seat": 200
        }).insert()

        booking.submit()
        booking.cancel()

        self.assertEqual(booking.refund_amount, booking.total_amount)

    def test_partial_refund_on_late_cancellation(self):
        from frappe.utils import now_datetime
        from datetime import timedelta

        # Set show time → 3 hours from now
        future_time = now_datetime() + timedelta(hours=3)

        self.show.show_date = future_time.date()
        self.show.start_time = future_time.time()
        self.show.save()

        # Create booking
        booking = frappe.get_doc({
            "doctype": "Ticket Booking",
            "show": self.show.name,
            "customer_name": "customer1",
            "customer_email": "c1@gmail.com",
            "customer_phone": "12345",
            "price_per_seat": 200,
              "seats": [{"seat_label": "A-1","row_letter":"A", "seat_number":1}],
        }).insert()

        booking.submit()

        # Cancel booking
        booking.cancel()

        # Reload to get updated values
        booking.reload()

        expected_refund = booking.total_amount * 0.5

        self.assertEqual(booking.refund_amount, expected_refund)

    def test_no_refund_on_very_late_cancellation(self):
        from frappe.utils import now_datetime
        from datetime import timedelta

        # Set show to 1 hour in future
        future_time = now_datetime() + timedelta(hours=1)

        self.show.show_date = future_time.date()
        self.show.start_time = future_time.time()
        self.show.show_status = "Scheduled"
        self.show.save()

        # Create booking
        booking = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "customer_name": "customer1",
                "customer_email": "c1@gmail.com",
                "customer_phone": "12345",
                "price_per_seat": 200,
                "seats": [
                    {"seat_label": "A-1", "row_letter": "A", "seat_number": "1"}
                ],
            }
        ).insert()

        booking.submit()

        # Cancel booking
        booking.cancel()
        booking.reload()

        # Assert no refund
        self.assertEqual(booking.refund_amount, 0)

    def test_show_conflict_validation(self):
        # First show: 14:00–16:00 (duration = 120 mins from movie)
        show1 = frappe.get_doc(
            {
                "doctype": "Show",
                "movie": self.movie.name,
                "screen": self.screen.name,
                "show_date": "2026-04-20",
                "start_time": "14:00:00",
            }
        ).insert()

        # Second show: overlaps → 15:00–17:00
        show2 = frappe.get_doc(
            {
                "doctype": "Show",
                "movie": self.movie.name,
                "screen": self.screen.name,
                "show_date": "2026-04-20",
                "start_time": "15:00:00",
            }
        )

        # Expect ValidationError due to overlap
        with self.assertRaises(frappe.ValidationError) as cm:
            show2.insert()

        self.assertIn("already has a show scheduled", str(cm.exception))

    def test_cancel_restores_seats(self):
        # Reload show to ensure fresh values
        show = frappe.get_doc("Show", self.show.name)

        initial_available = show.available_seats
        initial_booked = show.booked_seats

        # Create booking with 4 seats
        booking = frappe.get_doc(
            {
                "doctype": "Ticket Booking",
                "show": self.show.name,
                "customer_name": "customer1",
                "customer_email": "c1@gmail.com",
                "customer_phone": "12345",
                "price_per_seat": 200,
                "seats": [
                    {"seat_label": "A-1", "row_letter": "A", "seat_number": "1"},
                    {"seat_label": "A-2", "row_letter": "A", "seat_number": "2"},
                    {"seat_label": "A-3", "row_letter": "A", "seat_number": "3"},
                    {"seat_label": "A-4", "row_letter": "A", "seat_number": "4"},
                ],
            }
        ).insert()

        booking.submit()

        # Reload show after booking
        show.reload()

        self.assertEqual(show.available_seats, initial_available - 4)
        self.assertEqual(show.booked_seats, initial_booked + 4)

        # Cancel booking
        booking.cancel()

        # Reload show after cancellation
        show.reload()

        # Seats should be restored
        self.assertEqual(show.available_seats, initial_available)
        self.assertEqual(show.booked_seats, initial_booked)