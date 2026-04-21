import frappe
from frappe.utils import today


@frappe.whitelist()
def get_dashboard_data():
    return {
        "kpis": get_kpis(),
        "occupancy": get_today_occupancy(),
        "revenue": get_30_day_revenue(),
        "timeslot": get_timeslot_distribution(),
        "top_movies": get_top_movies(),
    }


# 🎯 KPI DATA
def get_kpis():
    data = frappe.db.sql(
        """
        SELECT 
            COUNT(*) AS bookings,
            SUM(total_amount) AS revenue
        FROM `tabTicket Booking`
        WHERE docstatus = 1
          AND DATE(creation) = CURDATE()
    """,
        as_dict=True,
    )[0]

    occupancy = (
        frappe.db.sql(
            """
        SELECT 
            SUM(tb.number_of_seats) / SUM(s.total_seats) * 100 AS occupancy
        FROM `tabShow` s
        LEFT JOIN `tabTicket Booking` tb 
            ON tb.show = s.name AND tb.docstatus = 1
        WHERE s.show_date >= CURDATE()
    """,
            as_dict=True,
        )[0].occupancy
        or 0
    )

    return {
        "bookings": data.bookings or 0,
        "revenue": round(data.revenue or 0),
        "occupancy": round(occupancy, 2),
    }


# 📊 Chart 1
def get_today_occupancy():
    data = frappe.db.sql(
        """
        SELECT 
            s.theater,
            SUM(tb.number_of_seats) AS booked,
            SUM(s.total_seats) AS total
        FROM `tabShow` s
       LEFT JOIN `tabTicket Booking` tb 
    ON tb.show = s.name AND tb.docstatus = 1
        WHERE s.show_date >= CURDATE()
        GROUP BY s.theater
    """,
        as_dict=True,
    )
    print(data)
    if not data:
        return {
            "data": {
                "labels": ["No Data"],
                "datasets": [{"name": "Occupancy %", "values": [0]}],
            },
            "type": "bar",
        }

    return {
        "data": {
            "labels": [d.theater for d in data],
            "datasets": [
                {
                    "name": "Occupancy %",
                    "values": [
                        (
                            round((d.booked or 0) / (d.total or 1) * 100, 2)
                            if d.total
                            else 0
                        )
                        for d in data
                    ],
                }
            ],
        },
        "type": "bar",
    }


# 📈 Chart 2
def get_30_day_revenue():
    data = frappe.db.sql(
        """
        SELECT 
            DATE(creation) AS date,
            SUM(total_amount) AS revenue
        FROM `tabTicket Booking`
        WHERE docstatus = 1
          AND creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(creation)
        ORDER BY date
    """,
        as_dict=True,
    )

    return {
        "data": {
            "labels": [str(d.date) for d in data],
            "datasets": [{"name": "Revenue", "values": [d.revenue for d in data]}],
        },
        "type": "line",
    }


# ⏰ Chart 3
def get_timeslot_distribution():
    data = frappe.db.sql(
        """
        SELECT 
            HOUR(start_time) AS hour,
            COUNT(*) AS bookings
        FROM `tabTicket Booking`
        WHERE docstatus = 1
        GROUP BY hour
        ORDER BY hour
    """,
        as_dict=True,
    )

    return {
        "data": {
            "labels": [f"{d.hour}:00" for d in data],
            "datasets": [{"name": "Bookings", "values": [d.bookings for d in data]}],
        },
        "type": "bar",
    }


# 🥧 Chart 4
def get_top_movies():
    data = frappe.db.sql(
        """
        SELECT 
            movie_title,
            COUNT(*) AS bookings
        FROM `tabTicket Booking`
        WHERE docstatus = 1
        GROUP BY movie_title
        ORDER BY bookings DESC
        LIMIT 5
    """,
        as_dict=True,
    )

    return {
        "data": {
            "labels": [d.movie_title for d in data],
            "datasets": [{"name": "Bookings", "values": [d.bookings for d in data]}],
        },
        "type": "percentage",
    }
