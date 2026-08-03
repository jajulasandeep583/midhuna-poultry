"""Which sheds are earning and which are standing empty.

Downtime between flocks is a real biosecurity requirement and a real cost; a
shed that sits empty for three weeks between cycles loses most of a batch a
year.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	today = getdate(nowdate())

	conds = {}
	if filters.farm:
		conds["farm"] = filters.farm

	sheds = frappe.get_all(
		"Shed", filters=conds,
		fields=["name", "farm", "shed_code", "capacity", "housing_system", "status",
		        "current_flock", "last_depleted_on", "last_cleaned_on"],
		order_by="farm asc, shed_code asc",
	)

	data = []
	for s in sheds:
		flock = None
		if s.current_flock:
			flock = frappe.db.get_value(
				"Flock", s.current_flock,
				["flock_name", "flock_type", "opening_qty", "current_qty", "age_days",
				 "placement_date"], as_dict=True,
			)
		downtime = 0
		if s.status in ("Empty", "Cleaning") and s.last_depleted_on:
			downtime = (today - getdate(s.last_depleted_on)).days

		cycles = frappe.db.count("Flock", {"shed": s.name})
		occupancy = (flt(flock.current_qty) / cint(s.capacity) * 100.0) if (
			flock and cint(s.capacity)) else 0

		data.append({
			"shed": s.name,
			"farm": s.farm,
			"capacity": s.capacity,
			"housing_system": s.housing_system,
			"status": s.status,
			"flock": s.current_flock,
			"flock_type": flock.flock_type if flock else None,
			"birds": flock.current_qty if flock else 0,
			"occupancy_pct": occupancy,
			"age_days": flock.age_days if flock else 0,
			"placed_on": flock.placement_date if flock else None,
			"last_depleted_on": s.last_depleted_on,
			"downtime_days": downtime,
			"cycles_run": cycles,
		})

	columns = [
		{"label": _("Shed"), "fieldname": "shed", "fieldtype": "Link", "options": "Shed",
		 "width": 180},
		{"label": _("Farm"), "fieldname": "farm", "fieldtype": "Link", "options": "Farm",
		 "width": 160},
		{"label": _("Capacity"), "fieldname": "capacity", "fieldtype": "Int", "width": 90},
		{"label": _("Housing"), "fieldname": "housing_system", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 95},
		{"label": _("Flock"), "fieldname": "flock", "fieldtype": "Link", "options": "Flock",
		 "width": 120},
		{"label": _("Type"), "fieldname": "flock_type", "fieldtype": "Data", "width": 85},
		{"label": _("Birds"), "fieldname": "birds", "fieldtype": "Int", "width": 85},
		{"label": _("Occupancy %"), "fieldname": "occupancy_pct", "fieldtype": "Percent",
		 "width": 110},
		{"label": _("Age"), "fieldname": "age_days", "fieldtype": "Int", "width": 60},
		{"label": _("Placed On"), "fieldname": "placed_on", "fieldtype": "Date", "width": 100},
		{"label": _("Depleted On"), "fieldname": "last_depleted_on", "fieldtype": "Date",
		 "width": 105},
		{"label": _("Downtime Days"), "fieldname": "downtime_days", "fieldtype": "Int",
		 "width": 120},
		{"label": _("Cycles Run"), "fieldname": "cycles_run", "fieldtype": "Int", "width": 100},
	]
	return columns, data
