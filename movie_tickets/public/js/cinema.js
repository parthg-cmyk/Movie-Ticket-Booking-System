frappe.after_ajax(() => {
    console.log("🎬 Movie Tickets App Loaded");

    document.addEventListener("keydown", function (e) {
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "b") {
            frappe.msgprint("Opening New Booking Form...");
            frappe.new_doc("Ticket Booking");
        }
    });
});