import frappe
from collections import defaultdict


def get_context(context):

    movie = frappe.form_dict.get("movie")

    if not movie:
        context.shows_grouped = {}
        return

    # 🎬 Fetch shows
    shows = frappe.get_all(
        "Show",
        filters={
            "movie": movie,
            "show_status": ["in", ["Scheduled", "Now Playing"]]
        },
        fields=[
            "name",
            "theater",
            "screen",
            "show_date",
            "start_time",
            "ticket_price",
            "available_seats"
        ],
        order_by="show_date asc, start_time asc"
    )

    # 🔥 Group by Theater → Date
    grouped = defaultdict(lambda: defaultdict(list))

    for s in shows:
        grouped[s.theater][str(s.show_date)].append(s)

    context.shows_grouped = grouped

    # 🎬 Movie Info
    context.movie = frappe.get_doc("Movie", movie)