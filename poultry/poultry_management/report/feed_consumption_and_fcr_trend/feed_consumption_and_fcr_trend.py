"""Feed drawn per flock per week, with feed cost and the FCR it bought.

Feed is 65-70% of the cost of producing a bird, so this is the report the
purchase and production sides argue over.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conds = ["dfe.docstatus = 1"]
	params = {}
	for key, clause in (("farm", "dfe.farm = %(farm)s"), ("flock", "dfe.flock = %(flock)s"),
	                    ("from_date", "dfe.posting_date >= %(from_date)s"),
	                    ("to_date", "dfe.posting_date <= %(to_date)s")):
		if filters.get(key):
			conds.append(clause)
			params[key] = filters.get(key)

	rows = frappe.db.sql(
		"""
		select dfe.flock, dfe.farm, dfe.age_days, dfe.posting_date, dfe.total_feed_kg,
		       dfe.closing_qty, dfe.avg_body_weight_g, dfe.total_eggs,
		       fd.item, fd.qty_kg
		from `tabDaily Flock Entry` dfe
		left join `tabFlock Feed Detail` fd on fd.parent = dfe.name
		where {conds}
		order by dfe.flock, dfe.age_days
		""".format(conds=" and ".join(conds)),
		params, as_dict=True,
	)

	rates = {i.name: flt(i.valuation_rate) for i in frappe.get_all(
		"Item", filters={"item_group": "Poultry"}, fields=["name", "valuation_rate"])}

	buckets = {}
	for r in rows:
		wk = max(1, (cint(r.age_days) + 6) // 7)
		key = (r.flock, wk)
		b = buckets.setdefault(key, {
			"flock": r.flock, "farm": r.farm, "week": wk, "feed_kg": 0.0, "feed_cost": 0.0,
			"eggs": 0, "birds": 0, "days": 0, "weight": 0.0,
		})
		if r.item:
			b["feed_kg"] += flt(r.qty_kg)
			b["feed_cost"] += flt(r.qty_kg) * rates.get(r.item, 0)

	# day-level facts must not be multiplied by the feed-row join
	seen = set()
	for r in rows:
		wk = max(1, (cint(r.age_days) + 6) // 7)
		key = (r.flock, wk)
		day_key = (r.flock, r.posting_date)
		if day_key in seen:
			continue
		seen.add(day_key)
		b = buckets.get(key)
		if not b:
			continue
		b["days"] += 1
		b["eggs"] += cint(r.total_eggs)
		b["birds"] = cint(r.closing_qty)
		if flt(r.avg_body_weight_g):
			b["weight"] = flt(r.avg_body_weight_g)

	data = []
	cum = {}
	for key in sorted(buckets, key=lambda k: (k[0], k[1])):
		b = buckets[key]
		c = cum.setdefault(b["flock"], {"kg": 0.0, "cost": 0.0})
		c["kg"] += b["feed_kg"]
		c["cost"] += b["feed_cost"]
		live_kg = b["birds"] * b["weight"] / 1000.0
		data.append({
			"flock": b["flock"],
			"farm": b["farm"],
			"week": b["week"],
			"days": b["days"],
			"birds": b["birds"],
			"feed_kg": b["feed_kg"],
			"feed_per_bird_g": (b["feed_kg"] * 1000.0 / b["birds"] / b["days"])
			if b["birds"] and b["days"] else 0,
			"feed_cost": b["feed_cost"],
			"cumulative_feed_kg": c["kg"],
			"body_weight_g": b["weight"],
			"fcr_to_date": (c["kg"] / live_kg) if live_kg else 0,
			"eggs": b["eggs"],
			"feed_cost_per_dozen": (b["feed_cost"] / (b["eggs"] / 12.0)) if b["eggs"] else 0,
		})

	columns = [
		{"label": _("Flock"), "fieldname": "flock", "fieldtype": "Link", "options": "Flock",
		 "width": 120},
		{"label": _("Farm"), "fieldname": "farm", "fieldtype": "Link", "options": "Farm",
		 "width": 160},
		{"label": _("Week"), "fieldname": "week", "fieldtype": "Int", "width": 65},
		{"label": _("Days"), "fieldname": "days", "fieldtype": "Int", "width": 65},
		{"label": _("Birds"), "fieldname": "birds", "fieldtype": "Int", "width": 85},
		{"label": _("Feed kg"), "fieldname": "feed_kg", "fieldtype": "Float", "width": 100},
		{"label": _("g/bird/day"), "fieldname": "feed_per_bird_g", "fieldtype": "Float",
		 "precision": 1, "width": 110},
		{"label": _("Feed Cost"), "fieldname": "feed_cost", "fieldtype": "Currency", "width": 120},
		{"label": _("Cum Feed kg"), "fieldname": "cumulative_feed_kg", "fieldtype": "Float",
		 "width": 120},
		{"label": _("Body Wt g"), "fieldname": "body_weight_g", "fieldtype": "Float", "width": 100},
		{"label": _("FCR to Date"), "fieldname": "fcr_to_date", "fieldtype": "Float",
		 "precision": 3, "width": 110},
		{"label": _("Eggs"), "fieldname": "eggs", "fieldtype": "Int", "width": 90},
		{"label": _("Feed Cost / Dozen"), "fieldname": "feed_cost_per_dozen",
		 "fieldtype": "Currency", "width": 150},
	]
	return columns, data
