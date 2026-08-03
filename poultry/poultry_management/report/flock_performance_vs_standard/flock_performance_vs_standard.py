"""Day-by-day actual against the standard the flock was measured on.

This is the single most valuable output of a poultry ERP (§3.8): the standard
comes from the flock's own snapshot, so editing a master later cannot rewrite
what a historical flock is compared against.
"""

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.flock:
		frappe.throw(_("Select a flock."))

	std = {
		r.age_days: r
		for r in frappe.get_all(
			"Breed Standard Detail",
			filters={"parent": filters.flock, "parenttype": "Flock"},
			fields=["age_days", "std_body_weight_g", "std_cumulative_feed_g",
			        "std_cumulative_mortality_pct", "std_hd_production_pct", "std_water_feed_ratio"],
		)
	}

	entries = frappe.get_all(
		"Daily Flock Entry",
		filters={"flock": filters.flock, "docstatus": 1},
		fields=["posting_date", "age_days", "opening_qty", "mortality_qty", "cull_qty",
		        "closing_qty", "cumulative_mortality_pct", "total_feed_kg", "cumulative_feed_kg",
		        "avg_body_weight_g", "water_feed_ratio", "total_eggs", "hd_production_pct",
		        "has_alert", "alert_message"],
		order_by="posting_date asc",
	)

	placed = flt(frappe.db.get_value("Flock", filters.flock, "opening_qty"))
	data = []
	for e in entries:
		s = std.get(e.age_days) or frappe._dict()
		std_cum_feed_kg = flt(s.std_cumulative_feed_g) * placed / 1000.0 if s else 0
		wt_var = 0.0
		if flt(e.avg_body_weight_g) and flt(s.std_body_weight_g):
			wt_var = (flt(e.avg_body_weight_g) - flt(s.std_body_weight_g)) / flt(
				s.std_body_weight_g) * 100.0
		data.append({
			"posting_date": e.posting_date,
			"age_days": e.age_days,
			"closing_qty": e.closing_qty,
			"losses": (e.mortality_qty or 0) + (e.cull_qty or 0),
			"cumulative_mortality_pct": e.cumulative_mortality_pct,
			"std_cumulative_mortality_pct": s.std_cumulative_mortality_pct,
			"total_feed_kg": e.total_feed_kg,
			"cumulative_feed_kg": e.cumulative_feed_kg,
			"std_cumulative_feed_kg": std_cum_feed_kg,
			"avg_body_weight_g": e.avg_body_weight_g,
			"std_body_weight_g": s.std_body_weight_g,
			"weight_variance_pct": wt_var,
			"hd_production_pct": e.hd_production_pct,
			"std_hd_production_pct": s.std_hd_production_pct,
			"alert": e.alert_message,
		})

	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Age"), "fieldname": "age_days", "fieldtype": "Int", "width": 60},
		{"label": _("Birds"), "fieldname": "closing_qty", "fieldtype": "Int", "width": 80},
		{"label": _("Losses"), "fieldname": "losses", "fieldtype": "Int", "width": 70},
		{"label": _("Cum Mort %"), "fieldname": "cumulative_mortality_pct",
		 "fieldtype": "Percent", "width": 100},
		{"label": _("Std Mort %"), "fieldname": "std_cumulative_mortality_pct",
		 "fieldtype": "Percent", "width": 100},
		{"label": _("Feed kg"), "fieldname": "total_feed_kg", "fieldtype": "Float", "width": 90},
		{"label": _("Cum Feed kg"), "fieldname": "cumulative_feed_kg", "fieldtype": "Float",
		 "width": 110},
		{"label": _("Std Cum Feed kg"), "fieldname": "std_cumulative_feed_kg",
		 "fieldtype": "Float", "width": 130},
		{"label": _("Body Wt g"), "fieldname": "avg_body_weight_g", "fieldtype": "Float",
		 "width": 100},
		{"label": _("Std Wt g"), "fieldname": "std_body_weight_g", "fieldtype": "Float",
		 "width": 100},
		{"label": _("Wt Var %"), "fieldname": "weight_variance_pct", "fieldtype": "Percent",
		 "width": 95},
		{"label": _("HDP %"), "fieldname": "hd_production_pct", "fieldtype": "Percent", "width": 85},
		{"label": _("Std HDP %"), "fieldname": "std_hd_production_pct", "fieldtype": "Percent",
		 "width": 95},
		{"label": _("Alert"), "fieldname": "alert", "fieldtype": "Small Text", "width": 260},
	]

	chart = {
		"data": {
			"labels": [d["age_days"] for d in data],
			"datasets": [
				{"name": _("Actual Weight"), "values": [flt(d["avg_body_weight_g"]) for d in data]},
				{"name": _("Standard Weight"), "values": [flt(d["std_body_weight_g"]) for d in data]},
			],
		},
		"type": "line",
		"lineOptions": {"hideDots": 1, "regionFill": 0},
	}
	return columns, data, None, chart
