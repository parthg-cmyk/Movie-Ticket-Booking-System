import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    if filters.get("chart_type") == "Screen Type Revenue":
        chart = get_screen_type_chart(filters)
    else:
        chart = get_chart_data(data)

    return columns, data, None, chart


# ✅ Columns
def get_columns():
    return [
        {
            "label": "Movie Title",
            "fieldname": "movie_title",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Genre",
            "fieldname": "genre",
            "fieldtype": "Link",
            "options": "Movie Genre",
            "width": 120,
        },
        {
            "label": "Language",
            "fieldname": "language",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Total Shows",
            "fieldname": "total_shows",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Total Bookings",
            "fieldname": "total_bookings",
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "label": "Seats Sold",
            "fieldname": "seats_sold",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Total Revenue",
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": "Avg Occupancy (%)",
            "fieldname": "avg_occupancy",
            "fieldtype": "Percent",
            "width": 140,
        },
        {
            "label": "Avg Ticket Price",
            "fieldname": "avg_ticket_price",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]


# ✅ Data Query (JOINs)
def get_data(filters):
    conditions = ""

    if filters.get("theater"):
        conditions += " AND s.theater = %(theater)s"

    if filters.get("from_date"):
        conditions += " AND s.show_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND s.show_date <= %(to_date)s"

    if filters.get("genre"):
        conditions += " AND m.genre = %(genre)s"

    if filters.get("language"):
        conditions += " AND m.language = %(language)s"

    data = frappe.db.sql(
        f"""
        SELECT
            m.name AS movie_title,
            m.genre,
            m.language,

            COUNT(DISTINCT s.name) AS total_shows,
            COUNT(DISTINCT tb.name) AS total_bookings,

            SUM(tb.number_of_seats) AS seats_sold,
            SUM(tb.total_amount) AS total_revenue,

            AVG(
                CASE 
                    WHEN s.total_seats > 0 
                    THEN (tb.number_of_seats / s.total_seats) * 100
                    ELSE 0
                END
            ) AS avg_occupancy,

            AVG(
                CASE 
                    WHEN tb.number_of_seats > 0 
                    THEN tb.total_amount / tb.number_of_seats
                    ELSE 0
                END
            ) AS avg_ticket_price

        FROM `tabMovie` m
        LEFT JOIN `tabShow` s ON s.movie = m.name
        LEFT JOIN `tabTicket Booking` tb ON tb.show = s.name AND tb.docstatus = 1

        WHERE 1=1 {conditions}

        GROUP BY m.name
        ORDER BY total_revenue DESC
    """,
        filters,
        as_dict=True,
    )

    return data


# 📊 Chart 1: Top 10 Movies by Revenue
def get_chart_data(data):
    top_movies = sorted(data, key=lambda x: x.total_revenue or 0, reverse=True)[:10]

    return {
        "data": {
            "labels": [d.movie_title for d in top_movies],
            "datasets": [
                {
                    "name": "Revenue",
                    "values": [flt(d.total_revenue) for d in top_movies],
                }
            ],
        },
        "type": "bar",
    }


# 📈 Summary
def get_summary(data):
    total_revenue = sum(flt(d.total_revenue) for d in data)
    total_bookings = sum(flt(d.total_bookings) for d in data)

    return [
        {"value": total_revenue, "indicator": "Green", "label": "Total Revenue"},
        {"value": total_bookings, "indicator": "Blue", "label": "Total Bookings"},
    ]


def get_screen_type_chart(filters):
    conditions = ""

    if filters.get("theater"):
        conditions += " AND s.theater = %(theater)s"

    if filters.get("from_date"):
        conditions += " AND s.show_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND s.show_date <= %(to_date)s"

    data = frappe.db.sql(
        f"""
        SELECT
            sc.screen_type,
            SUM(tb.total_amount) AS revenue
        FROM `tabShow` s
        JOIN `tabScreen` sc ON sc.name = s.screen
        JOIN `tabTicket Booking` tb 
            ON tb.show = s.name AND tb.docstatus = 1
        WHERE 1=1 {conditions}
        GROUP BY sc.screen_type
    """,
        filters,
        as_dict=True,
    )

    return {
        "data": {
            "labels": [d.screen_type for d in data],
            "datasets": [
                {"name": "Revenue Share", "values": [flt(d.revenue) for d in data]}
            ],
        },
        "type": "pie",
    }
