import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, getdate, nowdate


class Shed(Document):
	def validate(self):
		self.set_downtime()

	def before_save(self):
		# A missing warehouse is the most common cause of failed stock entries
		# in these implementations, so the shed creates its own (§3.2).
		if not self.warehouse:
			self.warehouse = self.create_warehouse()

	def create_warehouse(self):
		company = self.company or frappe.db.get_value("Farm", self.farm, "company")
		abbr = frappe.db.get_value("Company", company, "abbr")
		wh_name = f"{self.farm} {self.shed_code}"
		full = f"{wh_name} - {abbr}"
		if frappe.db.exists("Warehouse", full):
			return full

		parent = frappe.db.get_value("Farm", self.farm, "default_warehouse")
		if not parent:
			parent = ensure_group_warehouse(f"{self.farm}", company)

		wh = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": wh_name,
			"company": company,
			"parent_warehouse": parent,
			"is_group": 0,
		})
		wh.flags.ignore_permissions = True
		wh.insert()
		return wh.name

	def set_downtime(self):
		"""Downtime accrues from depletion until the next placement (§7.3)."""
		if self.status == "Occupied" or not self.last_depleted_on:
			self.downtime_days = 0
		else:
			self.downtime_days = max(0, date_diff(getdate(nowdate()), getdate(self.last_depleted_on)))


def ensure_group_warehouse(name, company):
	abbr = frappe.db.get_value("Company", company, "abbr")
	full = f"{name} - {abbr}"
	if frappe.db.exists("Warehouse", full):
		return full
	root = frappe.db.get_value(
		"Warehouse", {"company": company, "is_group": 1, "parent_warehouse": ["in", ["", None]]}, "name"
	)
	wh = frappe.get_doc({
		"doctype": "Warehouse",
		"warehouse_name": name,
		"company": company,
		"is_group": 1,
		"parent_warehouse": root,
	})
	wh.flags.ignore_permissions = True
	wh.insert()
	return wh.name
