# 🎬 Movie Tickets Booking System (Frappe App)

A complete cinema ticket booking backend system built using the Frappe Framework.  
This app handles movie shows, seat booking, validations, cancellations, and refund logic.

---

## 🚀 Features

- 🎥 Movie & Show Management
- 🪑 Seat Booking System
- ❌ Duplicate Seat Prevention
- 🚫 Booking Restriction for Cancelled Shows
- 🎟️ Max 10 Seats per Booking
- 💰 Refund Logic:
  - Full refund (≥ 6 hours before show)
  - 50% refund (3–6 hours before show)
  - No refund (< 3 hours)
- ⏱️ Show Conflict Detection (same screen/date)
- 🔄 Seat Restoration on Cancellation
- 📊 Seat Count Auto Management

---

## 🛠️ Tech Stack

- Frappe Framework
- Python
- MariaDB
- REST API (Frappe Whitelisted Methods)

---

## 📦 Installation & Setup

### 1. Create a bench
```bash
bench init cinema-bench
cd cinema-bench
```

### 2. Get the app
```bash
bench get-app movie_tickets
```

### 3. Create a site
```bash
bench new-site cinema.local
```

### 4. Install app
```bash
bench --site cinema.local install-app movie_tickets
```

### 5. Start server
```bash
bench start
```

---

## 📚 DocTypes

### 🎬 Movie
- movie_name
- duration (minutes)

### 🏢 Theater
- theater_name
- city

### 🖥️ Screen
- theater (Link)
- total_seats

### 🎟️ Show
- movie
- screen
- show_date
- start_time
- end_time (auto-calculated)
- available_seats
- booked_seats
- status

### 🧾 Ticket Booking
- show
- number_of_seats
- total_amount
- refund_amount
- status (Draft / Confirmed / Cancelled)

---

## 🔌 API Endpoints (Examples)

### Book Ticket
```python
frappe.call({
    method: "movie_tickets.api.book_ticket",
    args: {
        show: "SHW-0001",
        seats: 2
    }
})
```

### Cancel Ticket
```python
frappe.call({
    method: "movie_tickets.api.cancel_ticket",
    args: {
        booking: "BKG-0001"
    }
})
```

---

## 🧪 Running Tests

Run all tests:

```bash
bench --site cinema.local run-tests --app movie_tickets
```

---

## ✅ Test Coverage

### Booking Logic
- ✔ test_booking_decreases_available_seats  
- ✔ test_cannot_book_already_taken_seat  
- ✔ test_cannot_book_for_cancelled_show  
- ✔ test_max_seats_per_booking_limit  

### Refund Logic
- ✔ test_full_refund_on_early_cancellation  
- ✔ test_partial_refund_on_late_cancellation  
- ✔ test_no_refund_on_very_late_cancellation  

### Show Validation
- ✔ test_show_conflict_validation  

### Cancellation Logic
- ✔ test_cancel_restores_seats  

---

## ⚙️ Business Rules

### 🎟️ Booking
- Max 10 seats per booking
- Cannot book already reserved seats
- Cannot book cancelled/completed shows

### 💰 Refund Policy
| Time Before Show | Refund |
|----------------|--------|
| ≥ 6 hours      | 100%   |
| 3–6 hours      | 50%    |
| < 3 hours      | 0%     |

### 🎬 Show Rules
- No overlapping shows on same screen/date
- End time auto-calculated using movie duration

---

## ⚠️ Assumptions

- Seat numbering is abstracted (count-based system)
- Single price per show
- No payment gateway integration
- No user authentication layer (can be extended)

---

## 🚧 Limitations

- No seat-level UI (row/column layout not implemented)
- No real-time seat locking
- No concurrency handling for high traffic
- No multi-pricing (VIP, Premium, etc.)
- No frontend (React/UI not included)

---

## 🔮 Future Improvements

- 🎨 React-based booking UI
- 🔐 Authentication & User Accounts
- 💳 Payment Gateway Integration
- 🪑 Seat Layout (Grid System)
- ⚡ Real-time seat locking (WebSockets)
- 📈 Analytics Dashboard

---

## 👨‍💻 Author

Built as part of a backend system design & Frappe learning project.

---

## 📄 License

MIT License