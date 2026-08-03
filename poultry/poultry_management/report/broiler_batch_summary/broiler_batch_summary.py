"""One line per broiler flock, ranked by EEF.

EEF is the composite score the industry actually manages on: below 250 poor,
around 300 average, 350+ good, 400+ excellent (§7.1).
"""

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conds = {"flock_type": "Broiler"}
	if filters.farm:
		conds["farm"] = filters.farm
	if filters.status:
		conds["status"] = filters.status

	flocks = frappe.get_all(
		"Flock",
		filters=conds,
		fields=["name", "flock_name", "farm", "shed", "strain", "status", "placement_date",
		        "opening_qty", "current_qty", "age_days", "cumulative_mortality",
		        "cumulative_culls", "livability_pct", "cumulative_feed_kg", "avg_body_weight_g",
		        "fcr", "adg_g", "eef", "total_cost", "cost_per_bird", "cost_per_kg_live"],
	)

	data = []
	for f in flocks:
		live_kg = flt(f.current_qty) * flt(f.avg_body_weight_g) / 1000.0
		data.append({
			"flock": f.name,
			"flock_name": f.flock_name,
			"farm": f.farm,
			"shed": f.shed,
			"strain": f.strain,
			"status": f.status,
			"placement_date": f.placement_date,
			"age_days": f.age_days,
			"opening_qty": f.opening_qty,
			"current_qty": f.current_qty,
			"losses": (f.cumulative_mortality or 0) + (f.cumulative_culls or 0),
			"livability_pct": f.livability_pct,
			"cumulative_feed_kg": f.cumulative_feed_kg,
			"avg_body_weight_g": f.avg_body_weight_g,
			"live_weight_kg": live_kg,
			"fcr": f.fcr,
			"adg_g": f.adg_g,
			"eef": f.eef,
			"total_cost": f.total_cost,
			"cost_per_bird": f.cost_per_bird,
			"cost_per_kg_live": f.cost_per_kg_live,
		})

	data.sort(key=lambda r: flt(r["eef"]), reverse=True)

	columns = [
		{"label": _("Flock"), "fieldname": "flock", "fieldtype": "Link", "options": "Flock",
		 "width": 120},
		{"label": _("Name"), "fieldname": "flock_name", "fieldtype": "Data", "width": 130},
		{"label": _("Farm"), "fieldname": "farm", "fieldtype": "Link", "options": "Farm",
		 "width": 160},
		{"label": _("Shed"), "fieldname": "shed", "fieldtype": "Link", "options": "Shed",
		 "width": 170},
		{"label": _("Strain"), "fieldname": "strain", "fieldtype": "Link", "options": "Strain",
		 "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Age"), "fieldname": "age_days", "fieldtype": "Int", "width": 60},
		{"label": _("Placed"), "fieldname": "opening_qty", "fieldtype": "Int", "width": 85},
		{"label": _("Alive"), "fieldname": "current_qty", "fieldtype": "Int", "width": 85},
		{"label": _("Losses"), "fieldname": "losses", "fieldtype": "Int", "width": 80},
		{"label": _("Livability %"), "fieldname": "livability_pct", "fieldtype": "Percent",
		 "width": 105},
		{"label": _("Feed kg"), "fieldname": "cumulative_feed_kg", "fieldtype": "Float",
		 "width": 100},
		{"label": _("Body Wt g"), "fieldname": "avg_body_weight_g", "fieldtype": "Float",
		 "width": 100},
		{"label": _("Live kg"), "fieldname": "live_weight_kg", "fieldtype": "Float", "width": 100},
		{"label": _("FCR"), "fieldname": "fcr", "fieldtype": "Float", "precision": 3, "width": 80},
		{"label": _("ADG g"), "fieldname": "adg_g", "fieldtype": "Float", "precision": 1,
		 "width": 80},
		{"label": _("EEF"), "fieldname": "eef", "fieldtype": "Float", "precision": 1, "width": 80},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency",
		 "width": 120},
		{"label": _("Cost / Bird"), "fieldname": "cost_per_bird", "fieldtype": "Currency",
		 "width": 110},
		{"label": _("Cost / kg Live"), "fieldname": "cost_per_kg_live", "fieldtype": "Currency",
		 "width": 120},
	]

	chart = {
		"data": {
			"labels": [d["flock_name"] for d in data],
			"datasets": [{"name": _("EEF"), "values": [flt(d["eef"]) for d in data]}],
		},
		"type": "bar",
	}
	return columns, data, None, chart
