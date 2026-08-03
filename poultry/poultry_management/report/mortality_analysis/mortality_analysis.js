frappe.query_reports["Mortality Analysis"] = {
	filters: [
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today()},

		{fieldname: "group_by", label: __("Group By"), fieldtype: "Select",
		 options: ["Reason", "Category", "Age Band", "Shed", "Farm", "Flock"],
		 default: "Reason", reqd: 1},
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
	],
};
