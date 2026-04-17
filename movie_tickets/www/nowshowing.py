import frappe


def get_context(context):

    genre = frappe.form_dict.get("genre")
    language = frappe.form_dict.get("language")

    # ✅ SAFE FILTER (matches your schema exactly)
    filters = [["movie_status", "=", "Now Showing"]]

    if genre:
        filters.append(["genre", "=", genre])

    if language:
        filters.append(["language", "=", language])

    # ✅ Correct field names (IMPORTANT FIX)
    context.movies = frappe.get_all(
        "Movie",
        filters=filters,
        fields=[
            "name",
            "title",
            "language",
            "genre",
            "rating",
            "duration_minutes",   # ✅ FIXED
            "poster",
            "movie_status"
        ],
        order_by="release_date desc"
    )

    # ✅ Filters dropdown (clean unique values)
    context.genres = list(set(frappe.get_all("Movie", pluck="genre")))
    context.languages = list(set(frappe.get_all("Movie", pluck="language")))
