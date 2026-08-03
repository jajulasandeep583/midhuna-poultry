frappe.query_reports["Hatchery Performance"] = {
	filters: [
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today()},

		{fieldname: "source_flock", label: __("Source Flock"), fieldtype: "Link",
		 options: "Flock"},
		{fieldname: "setter", label: __("Setter"), fieldtype: "Link",
		 options: "Hatchery Machine"},
	],
};
