frappe.query_reports["Broiler Batch Summary"] = {
	filters: [
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "status", label: __("Status"), fieldtype: "Select",
		 options: ["", "Placed", "Growing", "Depleting", "Closed"]},
	],
};
