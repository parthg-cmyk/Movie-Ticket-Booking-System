frappe.query_reports["Box Office Collection Report"] = {
	"filters": [
		{
			"fieldname": "theater",
			"label": "Theater",
			"fieldtype": "Link",
			"options": "Theater"
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date"
		},
		{
			"fieldname": "genre",
			"label": "Genre",
			"fieldtype": "Link",
			"options": "Movie Genre"
		},
		{
			"fieldname": "language",
			"label": "Language",
			"fieldtype": "Select",
			"options": ["", "Hindi", "English", "Gujarati", "Tamil", "Telugu"]
		},
		{
			fieldname: "chart_type",
			label: "Chart Type",
			fieldtype: "Select",
			options: ["Top Movies", "Screen Type Revenue"],
			default: "Top Movies"
		}
	]
};