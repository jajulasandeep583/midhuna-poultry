"""Flocks that cannot legally be sold today, and the date each clears.

Sales reads this before committing a load. The same rule is enforced on the
Delivery Note itself, so this report is the warning and the document is the
hard stop.
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	as_on = getdate(filters.as_on or nowdate())

	rows = frappe.db.sql(
		"""
		select
			me.name, me.flock, me.medication, me.start_date, me.end_date,
			me.withdrawal_days, me.withdrawal_clear_date, me.birds_treated, me.reason,
			f.flock_name, f.farm, f.shed, f.flock_type, f.status, f.current_qty
		from `tabMedication Entry` me
		inner join `tabFlock` f on f.name = me.flock
		where me.docstatus = 1 and me.withdrawal_clear_date >= %(as_on)s
		order by me.withdrawal_clear_date asc
		""",
		{"as_on": as_on}, as_dict=True,
	)

	data = []
	for r in rows:
		data.append({
			"flock": r.flock,
			"flock_name": r.flock_name,
			"farm": r.farm,
			"shed": r.shed,
			"flock_type": r.flock_type,
			"birds": r.current_qty,
			"medication": r.medication,
			"treated_from": r.start_date,
			"treated_to": r.end_date,
			"withdrawal_days": r.withdrawal_days,
			"clears_on": r.withdrawal_clear_date,
			"days_to_go": (getdate(r.withdrawal_clear_date) - as_on).days,
			"reason": r.reason,
			"entry": r.name,
		})

	columns = [
		{"label": _("Flock"), "fieldname": "flock", "fieldtype": "Link", "options": "Flock",
		 "width": 120},
		{"label": _("Name"), "fieldname": "flock_name", "fieldtype": "Data", "width": 130},
		{"label": _("Farm"), "fieldname": "farm", "fieldtype": "Link", "options": "Farm",
		 "width": 160},
		{"label": _("Shed"), "fieldname": "shed", "fieldtype": "Link", "options": "Shed",
		 "width": 170},
		{"label": _("Birds"), "fieldname": "birds", "fieldtype": "Int", "width": 85},
		{"label": _("Medication"), "fieldname": "medication", "fieldtype": "Link",
		 "options": "Poultry Medication", "width": 160},
		{"label": _("From"), "fieldname": "treated_from", "fieldtype": "Date", "width": 95},
		{"label": _("To"), "fieldname": "treated_to", "fieldtype": "Date", "width": 95},
		{"label": _("Withdrawal Days"), "fieldname": "withdrawal_days", "fieldtype": "Int",
		 "width": 130},
		{"label": _("Clears On"), "fieldname": "clears_on", "fieldtype": "Date", "width": 100},
		{"label": _("Days to Go"), "fieldname": "days_to_go", "fieldtype": "Int", "width": 100},
		{"label": _("Reason"), "fieldname": "reason", "fieldtype": "Data", "width": 220},
	]
	return columns, data
