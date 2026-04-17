// Copyright (c) 2026, Parth Godhani and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Movie", {
// 	refresh(frm) {

// 	},
// });
frappe.listview_settings['Movie'] = {

    // 📋 Default Columns
    add_fields: ["language", "genre", "rating", "release_date", "movie_status"],

    // 🎨 Indicators (status colors)
    get_indicator: function (doc) {
        const map = {
            "Now Showing": "green",
            "Upcoming": "blue",
            "Ended": "gray"
        };

        return [doc.movie_status, map[doc.movie_status], `movie_status,=,${doc.movie_status}`];
    }
};

frappe.ui.form.on('Movie', {
    refresh(frm) {
        frm.add_custom_button('Bulk Create Shows', () => {

            let dialog = new frappe.ui.Dialog({
                title: 'Bulk Show Creator',
                fields: [

                    {
                        label: 'Screens',
                        fieldname: 'screens',
                        fieldtype: 'MultiSelectList',
                        reqd: 1,
                        get_data: function (txt) {
                            return frappe.db.get_link_options('Screen', txt);
                        }
                    },

                    {
                        label: 'From Date',
                        fieldname: 'from_date',
                        fieldtype: 'Date',
                        reqd: 1
                    },

                    {
                        label: 'To Date',
                        fieldname: 'to_date',
                        fieldtype: 'Date',
                        reqd: 1
                    },

                    {
                        label: 'Show Times',
                        fieldname: 'show_times',
                        fieldtype: 'Small Text',
                        description: 'Comma separated (e.g. 10:00,14:00,18:00)',
                        reqd: 1
                    }

                ],

                primary_action(values) {

                    let show_times = values.show_times
                        .split(',')
                        .map(t => t.trim());

                    frappe.call({
                        method: "movie_tickets.api.create_bulk_shows",
                        args: {
                            movie: frm.doc.name,
                            screens: values.screens,
                            from_date: values.from_date,
                            to_date: values.to_date,
                            show_times: show_times
                        },
                        callback: function (r) {
                            frappe.msgprint(r.message.message);
                        }
                    });

                    dialog.hide();
                }
            });

            dialog.show();

            // ✅ Listen for realtime completion
            frappe.realtime.on("bulk_show_creation_done", (data) => {
                frappe.msgprint(
                    `Created: ${data.created}, Skipped: ${data.skipped}`
                );
            });

        });
    }
});