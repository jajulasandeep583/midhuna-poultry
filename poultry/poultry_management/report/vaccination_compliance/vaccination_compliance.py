"""Planned against done, per flock, with what is overdue right now.

Compliance is read from the plan rows a Vaccination Entry actually closed, not
from a parallel tick-list, so it cannot drift from what was recorded.
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	today = getdate(nowdate())

	conds = {}
	if filters.farm:
		conds["farm"] = filters.farm
	if filters.flock:
		conds["flock"] = filters.flock

	plans = frappe.get_all("Flock Vaccination Plan", filters=conds,
	                       fields=["name", "flock", "farm", "template"])
	data = []
	for p in plans:
		flock_status = frappe.db.get_value("Flock", p.flock, "status")
		if filters.only_active and flock_status in ("Closed", "Draft"):
			continue
		rows = frappe.get_all(
			"Flock Vaccination Plan Detail",
			filters={"parent": p.name},
			fields=["age_days", "vaccine", "route", "due_date", "status", "done_on",
			        "vaccination_entry", "is_mandatory"],
			order_by="age_days asc",
		)
		for r in rows:
			overdue_by = 0
			if r.status != "Done" and r.due_date and getdate(r.due_date) < today:
				overdue_by = (today - getdate(r.due_date)).days
			delay = 0
			if r.status == "Done" and r.done_on and r.due_date:
				delay = (getdate(r.done_on) - getdate(r.due_date)).days
			if filters.status_filter == "Overdue only" and not overdue_by:
				continue
			if filters.status_filter == "Done only" and r.status != "Done":
				continue
			data.append({
				"flock": p.flock,
				"farm": p.farm,
				"flock_status": flock_status,
				"age_days": r.age_days,
				"vaccine": r.vaccine,
				"route": r.route,
				"due_date": r.due_date,
				"status": r.status,
				"done_on": r.done_on,
				"delay_days": delay,
				"overdue_days": overdue_by,
				"vaccination_entry": r.vaccination_entry,
				"mandatory": r.is_mandatory,
			})

	data.sort(key=lambda d: (-cint(d["overdue_days"]), d["flock"], cint(d["age_days"])))

	columns = [
		{"label": _("Flock"), "fieldname": "flock", "fieldtype": "Link", "options": "Flock",
		 "width": 120},
		{"label": _("Farm"), "fieldname": "farm", "fieldtype": "Link", "options": "Farm",
		 "width": 160},
		{"label": _("Flock Status"), "fieldname": "flock_status", "fieldtype": "Data",
		 "width": 100},
		{"label": _("Age"), "fieldname": "age_days", "fieldtype": "Int", "width": 60},
		{"label": _("Vaccine"), "fieldname": "vaccine", "fieldtype": "Link", "options": "Vaccine",
		 "width": 160},
		{"label": _("Route"), "fieldname": "route", "fieldtype": "Data", "width": 130},
		{"label": _("Due"), "fieldname": "due_date", "fieldtype": "Date", "width": 95},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Done On"), "fieldname": "done_on", "fieldtype": "Date", "width": 95},
		{"label": _("Delay (days)"), "fieldname": "delay_days", "fieldtype": "Int", "width": 100},
		{"label": _("Overdue (days)"), "fieldname": "overdue_days", "fieldtype": "Int",
		 "width": 120},
		{"label": _("Entry"), "fieldname": "vaccination_entry", "fieldtype": "Link",
		 "options": "Vaccination Entry", "width": 140},
	]
	return columns, data
