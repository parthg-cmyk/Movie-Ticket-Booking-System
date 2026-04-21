frappe.pages['cinema-dashboard'].on_page_load = function (wrapper) {

    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '🎬 Cinema Dashboard',
        single_column: true
    });

    // ✅ Use page.body (IMPORTANT FIX)
    let $body = $(page.body);
    
    page.set_title("🔥 Live Cinema Dashboard");

    // 🎨 CSS (scoped properly)
    $body.append(`
        <style>
            .dash-wrapper {
                padding: 20px;
            }

            .kpi-row {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }

            .kpi {
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                font-weight: 600;
                text-align: center;
            }

            .chart-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }

            .chart-card {
                background: white;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                height: 320px;
            }

            .chart-title {
                font-weight: 600;
                margin-bottom: 10px;
            }
        </style>
    `);

    // 🧱 Layout
    $body.append(`
        <div class="dash-wrapper">

            <div class="kpi-row">
                <div class="kpi" id="kpi_revenue">💰 Revenue Today: ...</div>
                <div class="kpi" id="kpi_bookings">🎟 Bookings: ...</div>
                <div class="kpi" id="kpi_occupancy">📊 Occupancy: ...</div>
            </div>

            <div class="chart-grid">
                <div class="chart-card" id="occupancy_chart"></div>
                <div class="chart-card" id="revenue_chart"></div>
                <div class="chart-card" id="timeslot_chart"></div>
                <div class="chart-card" id="top_movies_chart"></div>
            </div>

        </div>
    `);

    load_dashboard(page);
};


// 🚀 Load Data
function load_dashboard(page) {

    frappe.call({
        method: "movie_tickets.movie_tickets.page.cinema_dashboard.cinema_dashboard.get_dashboard_data",
        callback: function (r) {

            let data = r.message;

            // KPI
            $("#kpi_revenue").text(`💰 Revenue Today: ₹${data.kpis.revenue}`);
            $("#kpi_bookings").text(`🎟 Bookings: ${data.kpis.bookings}`);
            $("#kpi_occupancy").text(`📊 Occupancy: ${data.kpis.occupancy}%`);

            // Charts
            render_chart("occupancy_chart", data.occupancy, "🎭 Occupancy by Theater");
            render_chart("revenue_chart", data.revenue, "📈 30-Day Revenue");
            render_chart("timeslot_chart", data.timeslot, "⏰ Time Slot Bookings");
            render_chart("top_movies_chart", data.top_movies, "🎬 Top Movies");
        }
    });

    // Refresh button
    page.add_action_item("Refresh", () => load_dashboard(page));
}


// 📊 Chart Renderer
function render_chart(id, chart_data, title) {
    let container = document.getElementById(id);

    container.innerHTML = `
        <div class="chart-title">${title}</div>
        <div class="chart-body" id="${id}_chart"></div>
    `;

    new frappe.Chart(`#${id}_chart`, {
        data: chart_data.data,
        type: chart_data.type,
        height: 250
    });
}