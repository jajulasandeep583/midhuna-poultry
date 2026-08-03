frappe.query_reports["Vaccination Compliance"] = {
	filters: [
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
		{fieldname: "status_filter", label: __("Show"), fieldtype: "Select",
		 options: ["All", "Overdue only", "Done only"], default: "All"},
		{fieldname: "only_active", label: __("Active flocks only"), fieldtype: "Check", default: 1},
	],
};
