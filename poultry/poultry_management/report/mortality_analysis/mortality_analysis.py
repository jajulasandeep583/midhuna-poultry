"""Where birds are dying, and of what.

Grouped by reason, age band, shed or farm - a vet reads this by reason, a
manager by shed.
"""

import frappe
from frappe import _
from frappe.utils import flt


def age_band(age):
	age = int(age or 0)
	if age <= 7:
		return "1. Day 1-7 (brooding)"
	if age <= 21:
		return "2. Day 8-21"
	if age <= 42:
		return "3. Day 22-42"
	if age <= 126:
		return "4. Day 43-126 (rearing)"
	return "5. Day 127+ (production)"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	group_by = filters.group_by or "Reason"

	conds = ["dfe.docstatus = 1"]
	params = {}
	if filters.from_date:
		conds.append("dfe.posting_date >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.to_date:
		conds.append("dfe.posting_date <= %(to_date)s")
		params["to_date"] = filters.to_date
	if filters.farm:
		conds.append("dfe.farm = %(farm)s")
		params["farm"] = filters.farm
	if filters.flock:
		conds.append("dfe.flock = %(flock)s")
		params["flock"] = filters.flock

	rows = frappe.db.sql(
		"""
		select
			dfe.name, dfe.flock, dfe.farm, dfe.shed, dfe.age_days, dfe.posting_date,
			dfe.mortality_qty, dfe.cull_qty,
			md.reason, md.qty as detail_qty,
			mr.category, mr.is_culling
		from `tabDaily Flock Entry` dfe
		left join `tabFlock Mortality Detail` md on md.parent = dfe.name
		left join `tabMortality Reason` mr on mr.name = md.reason
		where {conds}
		""".format(conds=" and ".join(conds)),
		params, as_dict=True,
	)

	placed = {
		f.name: f.opening_qty
		for f in frappe.get_all("Flock", fields=["name", "opening_qty"])
	}

	buckets = {}
	for r in rows:
		qty = flt(r.detail_qty) if r.reason else (flt(r.mortality_qty) + flt(r.cull_qty))
		if not qty:
			continue
		if group_by == "Reason":
			key = r.reason or _("Not specified")
		elif group_by == "Category":
			key = r.category or _("Not specified")
		elif group_by == "Age Band":
			key = age_band(r.age_days)
		elif group_by == "Shed":
			key = r.shed
		elif group_by == "Flock":
			key = r.flock
		else:
			key = r.farm
		b = buckets.setdefault(key, {"group": key, "qty": 0, "culls": 0, "flocks": set()})
		b["qty"] += qty
		if r.is_culling:
			b["culls"] += qty
		b["flocks"].add(r.flock)

	total_placed = sum(flt(placed.get(f)) for f in {r.flock for r in rows if r.flock})
	total_qty = sum(b["qty"] for b in buckets.values())

	data = []
	for b in sorted(buckets.values(), key=lambda x: x["qty"], reverse=True):
		data.append({
			"group": b["group"],
			"birds": int(b["qty"]),
			"culls": int(b["culls"]),
			"flocks": len(b["flocks"]),
			"share_pct": (b["qty"] / total_qty * 100.0) if total_qty else 0,
			"of_placed_pct": (b["qty"] / total_placed * 100.0) if total_placed else 0,
		})

	columns = [
		{"label": _(group_by), "fieldname": "group", "fieldtype": "Data", "width": 230},
		{"label": _("Birds Lost"), "fieldname": "birds", "fieldtype": "Int", "width": 110},
		{"label": _("of which Culls"), "fieldname": "culls", "fieldtype": "Int", "width": 120},
		{"label": _("Flocks"), "fieldname": "flocks", "fieldtype": "Int", "width": 80},
		{"label": _("Share of Losses %"), "fieldname": "share_pct", "fieldtype": "Percent",
		 "width": 150},
		{"label": _("% of Birds Placed"), "fieldname": "of_placed_pct", "fieldtype": "Percent",
		 "width": 150},
	]

	chart = {
		"data": {
			"labels": [d["group"] for d in data[:10]],
			"datasets": [{"name": _("Birds Lost"), "values": [d["birds"] for d in data[:10]]}],
		},
		"type": "bar",
	}
	return columns, data, None, chart
