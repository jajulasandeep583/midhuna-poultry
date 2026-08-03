frappe.query_reports["Withdrawal Period Alert"] = {
	filters: [
		{fieldname: "as_on", label: __("As On"), fieldtype: "Date",
		 default: frappe.datetime.get_today(), reqd: 1},
	],
};
