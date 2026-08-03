frappe.query_reports["Layer Production Curve"] = {
	filters: [
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock", reqd: 1,
		 get_query: () => ({filters: {flock_type: ["in", ["Layer", "Breeder"]]}})},
	],
};
