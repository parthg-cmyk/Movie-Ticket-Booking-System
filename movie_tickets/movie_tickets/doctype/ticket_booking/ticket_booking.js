// Copyright (c) 2026, Parth Godhani and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Ticket Booking", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Ticket Booking', {
    show: function (frm) {
        if (!frm.doc.show) return;

        frappe.db.get_doc('Show', frm.doc.show)
            .then(show => {

                frm.set_intro(`
                    🎬 <b>${show.movie}</b><br>
                    🏢 ${show.theater} | 📺 ${show.screen}<br>
                    📅 ${show.show_date} | ⏰ ${show.start_time}<br>
                    💰 ₹${show.ticket_price} | 🎟️ Seats: ${show.available_seats}
                `, 'green');


                frm.dashboard.set_headline(
                    `🎬 ${show.movie} | Seats: ${show.available_seats}`
                );

                if (show.available_seats < 5) {
                    frappe.msgprint({
                        title: 'Low Availability',
                        message: `⚠️ Only ${show.available_seats} seats remaining!`,
                        indicator: 'orange'
                    });
                }

                if (show.available_seats <= 0) {
                    frappe.throw("No seats available for this show!");
                }
            });
    }
});


frappe.ui.form.on('Ticket Booking', {
    refresh: function (frm) {

        // 🎟 Select Seats (only in draft)
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button('Select Seats', () => {
                open_seat_dialog(frm);
            });
        }

        // 📩 Send Booking Confirmation (after submit)
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Send Booking Confirmation', () => {
                frappe.call({
                    method: "movie_tickets.api.send_booking_confirmation",
                    args: {
                        booking: frm.doc.name
                    },
                    callback: function () {
                        frappe.msgprint("Booking confirmation sent ✅");
                    }
                });
            });
        }

        // ❌ Cancel Booking with confirmation
        if (frm.doc.docstatus === 1 && frm.doc.booking_status !== "Cancelled") {
            frm.add_custom_button('Cancel Booking', () => {

                frappe.confirm(
                    `
                    Are you sure you want to cancel this booking?<br><br>
                    
                    <b>Refund Policy:</b><br>
                    • 100% refund if cancelled 2 hours before show<br>
                    • 50% refund within 2 hours<br>
                    • No refund after show start
                    `,

                    () => {
                        frappe.call({
                            method: "movie_tickets.api.cancel_booking",
                            args: {
                                booking: frm.doc.name
                            },
                            callback: function () {
                                frappe.msgprint("Booking Cancelled");
                                frm.reload_doc();
                            }
                        });
                    }
                );
            });
        }
    }
});


// 🎯 MAIN FUNCTION
function open_seat_dialog(frm) {

    if (!frm.doc.show) {
        frappe.msgprint("Please select a Show first");
        return;
    }

    frappe.db.get_doc('Show', frm.doc.show).then(show => {
        return frappe.db.get_doc('Screen', show.screen).then(screen => {
            return { show, screen };
        });
    }).then(data => {

        let { show, screen } = data;
        let rows = screen.seat_rows;
        let cols = screen.seats_per_row;
        let price_per_seat = frm.doc.price_per_seat || 0;

        // 🔥 Fetch booked seats
        frappe.call({
            method: "movie_tickets.api.get_booked_seats",
            args: { show: show.name },
            callback: function (res) {
                render_seat_map(res.message || []);
            }
        });

        function render_seat_map(booked) {

            let selected = [];

            const aisle_after = Math.floor(cols / 2); // center aisle

            let style = `
    <style>
        .cinema-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            font-family: system-ui;
        }

        .screen {
            width: 80%;
            height: 40px;
            background: linear-gradient(to bottom, #f3f2f2, #302e2e);
            border-radius: 50%/100%;
            text-align: center;
            line-height: 40px;
            font-weight: bold;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .seat-grid {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .seat-row {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .row-label {
            width: 20px;
            font-weight: bold;
        }

        .seat {
            width: 34px;
            height: 34px;
            border-radius: 6px;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: 0.2s;
        }

        .seat.available { background: #2ecc71; color: #fff; }
        .seat.booked { background: #e74c3c; cursor: not-allowed; }
        .seat.selected { background: #f1c40f; color: #000; }
        .seat.premium { border: 2px solid #9b59b6; }

        .seat:hover:not(.booked) {
            transform: scale(1.15);
        }

        .aisle {
            width: 20px;
        }

        .legend {
            display: flex;
            gap: 15px;
            font-size: 12px;
        }

        .legend span {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .legend-box {
            width: 15px;
            height: 15px;
            border-radius: 3px;
        }

        .summary {
            font-weight: bold;
            margin-top: 10px;
        }
    </style>
    `;

            let html = `
        ${style}
        <div class="cinema-wrapper">
            <div class="screen">SCREEN</div>

            <div class="legend">
                <span><div class="legend-box" style="background:#2ecc71"></div> Available</span>
                <span><div class="legend-box" style="background:#e74c3c"></div> Booked</span>
                <span><div class="legend-box" style="background:#f1c40f"></div> Selected</span>
                <span><div class="legend-box" style="border:2px solid #9b59b6"></div> Premium</span>
            </div>

            <div class="seat-grid">
    `;

            for (let r = 1; r <= rows; r++) {

                let rowLetter = String.fromCharCode(64 + r);
                html += `<div class="seat-row"><div class="row-label">${rowLetter}</div>`;

                for (let c = 1; c <= cols; c++) {

                    if (c === aisle_after + 1) {
                        html += `<div class="aisle"></div>`;
                    }

                    let seat = `${rowLetter}-${c}`;
                    let isBooked = booked.includes(seat);

                    // 🎯 Premium logic (last 2 rows)
                    let isPremium = r >= rows - 1;

                    html += `
                <div 
                    class="seat 
                    ${isBooked ? 'booked' : 'available'} 
                    ${isPremium ? 'premium' : ''}"
                    data-seat="${seat}"
                    ${isBooked ? "style='pointer-events:none'" : ""}
                >
                    ${c}
                </div>
            `;
                }

                html += `</div>`;
            }

            html += `
            </div>
            <div class="summary">Selected: 0 | Total: ₹0</div>
        </div>
    `;

            let d = new frappe.ui.Dialog({
                title: "Select Seats",
                fields: [{ fieldtype: "HTML", fieldname: "seat_map" }],
                size: "extra-large",
                primary_action_label: "Confirm",
                primary_action() {

                    frm.clear_table("seats");

                    selected.forEach(seat => {
                        let row = frm.add_child("seats");
                        row.seat_label = seat;
                        row.seat_number = seat.split("-")[1];
                        row.row_letter = seat[0]
                        row.seat_price = price_per_seat;
                    });

                    frm.refresh_field("seats");
                    frm.set_value("total_amount", selected.length * price_per_seat);

                    d.hide();
                }
            });

            d.show();
            d.fields_dict.seat_map.$wrapper.html(html);

            // 🎯 Click Logic
            d.$wrapper.on("click", ".seat", function () {

                if ($(this).hasClass("booked")) return;

                let seat = $(this).attr("data-seat");

                if ($(this).hasClass("selected")) {
                    $(this).removeClass("selected").addClass("available");
                    selected = selected.filter(s => s !== seat);
                } else {
                    $(this).removeClass("available").addClass("selected");
                    selected.push(seat);
                }

                let total = selected.length * price_per_seat;

                d.$wrapper.find(".summary").text(
                    `Selected: ${selected.length} | Total: ₹${total}`
                );
            });
        }
    });
}