import frappe
import re

def slugify(text):
    if not text:
        return None

    # lowercase + replace non-alphanumeric with hyphen
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')

    return slug


def execute():
    """
    Generate slug for all Movies where slug is NULL or empty.
    Ensures uniqueness by appending suffix if needed.
    """

    movies = frappe.get_all(
        "Movie",
        fields=["name", "title", "slug"]
    )

    for m in movies:
        if m.slug:  # skip if already exists
            continue

        base_slug = slugify(m.title or m.name)

        if not base_slug:
            continue

        slug = base_slug
        counter = 1

        # 🔹 Ensure uniqueness
        while frappe.db.exists("Movie", {"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1

        frappe.db.set_value("Movie", m.name, "slug", slug)

    frappe.db.commit()

    frappe.logger().info("✅ Movie slugs generated successfully")