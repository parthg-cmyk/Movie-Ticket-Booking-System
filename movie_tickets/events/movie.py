import frappe
from frappe.utils import nowdate
import re

def before_save_movie(doc, method):
    # 🔹 Auto-generate slug
    if doc.title:
        slug = doc.title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
        doc.slug = slug

    # 🔹 Update movie status
    today = nowdate()

    if doc.release_date and doc.end_date:
        if doc.release_date > today:
            doc.movie_status = "Upcoming"
        elif doc.release_date <= today <= doc.end_date:
            doc.movie_status = "Now Showing"
        else:
            doc.movie_status = "Expired"