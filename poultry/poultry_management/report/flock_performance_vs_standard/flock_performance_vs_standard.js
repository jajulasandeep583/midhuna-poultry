frappe.query_reports["Flock Performance vs Standard"] = {
	filters: [
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock",
		 reqd: 1, get_query: () => ({filters: {status: ["!=", "Draft"]}})},
	],
};
