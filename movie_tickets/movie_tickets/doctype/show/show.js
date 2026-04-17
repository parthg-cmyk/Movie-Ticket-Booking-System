// Copyright (c) 2026, Parth Godhani and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Show", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Show', {

    // 🎬 On selecting Screen → fetch ticket price
    screen(frm) {
        if (!frm.doc.screen) return;

        frappe.db.get_value('Screen', frm.doc.screen, 'base_price')
            .then(r => {
                if (r.message && r.message.base_price) {
                    frm.set_value('ticket_price', r.message.base_price);
                }
            });
    },


    // 🎥 On selecting Movie → show duration + end time
    movie(frm) {
        if (!frm.doc.movie || !frm.doc.start_time) return;

        frappe.db.get_value('Movie', frm.doc.movie, ['duration'])
            .then(r => {
                let duration = r.message.duration;

                if (duration) {
                    let start = moment(frm.doc.start_time, "HH:mm:ss");
                    let end = start.clone().add(duration, 'minutes');

                    let end_time = end.format("HH:mm:ss");

                    frm.set_value("end_time", end_time);

                    frappe.msgprint(
                        `Movie Duration: ${duration} mins<br>
                         End Time: ${end_time}`
                    );
                }
            });
    },


    // 🔄 Also recalc if start_time changes
    start_time(frm) {
        if (frm.doc.movie) {
            frm.trigger("movie");
        }
    },


    // 🔘 Custom Buttons + Dashboard
    refresh(frm) {

        // 📋 View Bookings Button
        if (frm.doc.name) {
            frm.add_custom_button("View Bookings", () => {
                frappe.set_route("List", "Ticket Booking", {
                    show: frm.doc.name
                });
            });
        }

        // 📊 Dashboard Indicators
        set_dashboard_indicators(frm);
    }
});

function set_dashboard_indicators(frm) {

    if (!frm.doc.total_seats) return;

    // ✅ Prevent duplicate indicators
    if (frm._indicators_set) return;
    frm._indicators_set = true;

    let booked = frm.doc.booked_seats || 0;
    let available = frm.doc.available_seats || 0;
    let total = frm.doc.total_seats;

    let occupancy = total ? (booked / total) * 100 : 0;

    // 🔵 Booked
    frm.dashboard.add_indicator(
        `Booked: ${booked}`,
        "blue"
    );

    // 🟢 Available
    frm.dashboard.add_indicator(
        `Available: ${available}`,
        "green"
    );

    // 🎨 Occupancy color
    let color = "green";

    if (occupancy >= 100) {
        color = "red";
    } else if (occupancy > 80) {
        color = "orange";
    }

    // 🟠 / 🔴 Occupancy
    frm.dashboard.add_indicator(
        `Occupancy: ${occupancy.toFixed(1)}%`,
        color
    );

    // 🧠 Optional headline
    frm.dashboard.set_headline(
        `🎟 ${booked}/${total} seats booked`
    );
}
frappe.listview_settings['Show'] = {

    // 📋 Default Columns (modern useful fields)
    add_fields: [
        "movie_title",
        "screen",
        "show_date",
        "start_time",
        "available_seats",
        "show_status"
    ],

    // 🎨 Status Indicators
    get_indicator: function (doc) {

        const status_map = {
            "Scheduled": "green",
            "Now Playing": "orange",
            "Completed": "gray",
            "Cancelled": "red"
        };

        return [
            doc.show_status || "Unknown",
            status_map[doc.show_status] || "gray",
            `show_status,=,${doc.show_status}`
        ];
    },

    // 🔍 Optional: Default Filters (Modern UX)
    filters: [
        ["show_status", "!=", "Completed"]
    ],

    // ⚡ Row Formatting (Modern Feel)
    formatters: {

        available_seats(value, field, doc) {

            if (!doc.total_seats) return value;

            let percent = (value / doc.total_seats) * 100;

            if (percent < 20) {
                return `<span style="color:red;font-weight:bold">${value}</span>`;
            }

            if (percent < 50) {
                return `<span style="color:orange;font-weight:bold">${value}</span>`;
            }

            return `<span style="color:green">${value}</span>`;
        }
    }
};  