frappe.query_reports["Feed Consumption and FCR Trend"] = {
	filters: [
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today()},

		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
	],
};
