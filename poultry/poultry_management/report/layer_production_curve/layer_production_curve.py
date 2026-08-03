"""Hen-day production against standard, by week of age.

Persistency - how well production holds after peak - is what separates a good
layer flock from an average one, and it only shows up on a curve.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.flock:
		frappe.throw(_("Select a layer flock."))

	std = {
		cint(r.age_days): r
		for r in frappe.get_all(
			"Breed Standard Detail",
			filters={"parent": filters.flock, "parenttype": "Flock"},
			fields=["age_days", "std_hd_production_pct", "std_egg_weight_g"],
		)
	}

	entries = frappe.get_all(
		"Daily Flock Entry",
		filters={"flock": filters.flock, "docstatus": 1},
		fields=["posting_date", "age_days", "closing_qty", "total_eggs", "hd_production_pct",
		        "avg_egg_weight_g", "floor_eggs"],
		order_by="age_days asc",
	)

	weeks = {}
	for e in entries:
		wk = max(1, (cint(e.age_days) + 6) // 7)
		w = weeks.setdefault(wk, {"week": wk, "days": 0, "eggs": 0, "bird_days": 0,
		                          "egg_weight": [], "floor": 0, "age_days": e.age_days})
		w["days"] += 1
		w["eggs"] += cint(e.total_eggs)
		w["bird_days"] += cint(e.closing_qty)
		w["floor"] += cint(e.floor_eggs)
		w["age_days"] = max(w["age_days"], e.age_days)
		if flt(e.avg_egg_weight_g):
			w["egg_weight"].append(flt(e.avg_egg_weight_g))

	placed = flt(frappe.db.get_value("Flock", filters.flock, "opening_qty"))
	data = []
	cum_eggs = 0
	for wk in sorted(weeks):
		w = weeks[wk]
		hdp = (w["eggs"] / w["bird_days"] * 100.0) if w["bird_days"] else 0
		egg_wt = sum(w["egg_weight"]) / len(w["egg_weight"]) if w["egg_weight"] else 0
		cum_eggs += w["eggs"]
		s = _nearest(std, w["age_days"])
		data.append({
			"week": wk,
			"days": w["days"],
			"eggs": w["eggs"],
			"hd_production_pct": hdp,
			"std_hd_production_pct": flt(s.std_hd_production_pct) if s else 0,
			"variance_pct": hdp - flt(s.std_hd_production_pct) if s else 0,
			"avg_egg_weight_g": egg_wt,
			"egg_mass_g": hdp / 100.0 * egg_wt,
			"floor_eggs": w["floor"],
			"eggs_per_bird_housed": (cum_eggs / placed) if placed else 0,
		})

	columns = [
		{"label": _("Week"), "fieldname": "week", "fieldtype": "Int", "width": 70},
		{"label": _("Days"), "fieldname": "days", "fieldtype": "Int", "width": 70},
		{"label": _("Eggs"), "fieldname": "eggs", "fieldtype": "Int", "width": 100},
		{"label": _("HDP %"), "fieldname": "hd_production_pct", "fieldtype": "Percent",
		 "width": 100},
		{"label": _("Std HDP %"), "fieldname": "std_hd_production_pct", "fieldtype": "Percent",
		 "width": 110},
		{"label": _("Variance"), "fieldname": "variance_pct", "fieldtype": "Percent", "width": 100},
		{"label": _("Egg Wt g"), "fieldname": "avg_egg_weight_g", "fieldtype": "Float",
		 "width": 100},
		{"label": _("Egg Mass g/bird/day"), "fieldname": "egg_mass_g", "fieldtype": "Float",
		 "width": 160},
		{"label": _("Floor Eggs"), "fieldname": "floor_eggs", "fieldtype": "Int", "width": 100},
		{"label": _("Eggs / Bird Housed"), "fieldname": "eggs_per_bird_housed",
		 "fieldtype": "Float", "precision": 2, "width": 150},
	]

	chart = {
		"data": {
			"labels": [f"W{d['week']}" for d in data],
			"datasets": [
				{"name": _("Actual HDP"), "values": [flt(d["hd_production_pct"], 1) for d in data]},
				{"name": _("Standard HDP"),
				 "values": [flt(d["std_hd_production_pct"], 1) for d in data]},
			],
		},
		"type": "line",
		"lineOptions": {"hideDots": 1},
	}
	return columns, data, None, chart


def _nearest(std, age):
	best = None
	for a in sorted(std):
		if a <= cint(age):
			best = std[a]
		else:
			break
	return best
