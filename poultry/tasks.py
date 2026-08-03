"""Scheduled jobs. Alerts are pushed, not reported (§11.4)."""

import frappe
from frappe.utils import date_diff, getdate, nowdate

from poultry.poultry_utils import recompute_flock


def flag_overdue_vaccinations():
	"""Daily check of every plan against today, so an overdue dose surfaces
	without anyone opening a report."""
	for plan in frappe.get_all("Flock Vaccination Plan", pluck="name"):
		doc = frappe.get_doc("Flock Vaccination Plan", plan)
		before = doc.overdue_count
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
		if doc.overdue_count > (before or 0):
			notify_managers(
				f"{doc.overdue_count} vaccination(s) overdue on flock {doc.flock}",
				"Flock Vaccination Plan", doc.name,
			)
	frappe.db.commit()


def update_shed_downtime():
	"""Shed downtime is a biosecurity KPI, so it has to accrue on its own."""
	for shed in frappe.get_all(
		"Shed", filters={"status": ["in", ["Empty", "Cleaning"]]},
		fields=["name", "last_depleted_on"]
	):
		if not shed.last_depleted_on:
			continue
		days = max(0, date_diff(getdate(nowdate()), getdate(shed.last_depleted_on)))
		frappe.db.set_value("Shed", shed.name, "downtime_days", days, update_modified=False)
	frappe.db.commit()


def refresh_open_flocks():
	"""Age and the metrics derived from it move every day even when nobody
	posts anything."""
	for flock in frappe.get_all(
		"Flock", filters={"status": ["not in", ["Draft", "Closed"]]}, pluck="name"
	):
		try:
			recompute_flock(flock)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Poultry: recompute failed for {flock}")
	frappe.db.commit()


def notify_managers(subject, doctype, name):
	users = frappe.get_all(
		"Has Role", filters={"role": ["in", ["Poultry Manager", "Farm Manager"]], "parenttype": "User"},
		pluck="parent", distinct=True,
	)
	for user in users:
		if user in ("Administrator", "Guest"):
			continue
		frappe.get_doc({
			"doctype": "Notification Log",
			"for_user": user,
			"type": "Alert",
			"document_type": doctype,
			"document_name": name,
			"subject": subject,
		}).insert(ignore_permissions=True)
