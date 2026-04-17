import frappe
from frappe import _

@frappe.whitelist()
def get_count(doctype, filters=None, debug=False, cache=False):
    """
    Wrapper around frappe.client.get_count

    Adds logging for monitoring/debugging purposes while preserving original behavior.
    """

    frappe.logger("api").info({
        "event": "get_count_called",
        "doctype": doctype,
        "filters": filters,
        "user": frappe.session.user
    })

    count = frappe.db.count(doctype, filters=filters, cache=cache)

    if debug:
        frappe.logger("api").debug({
            "event": "get_count_result",
            "count": count
        })

    return count