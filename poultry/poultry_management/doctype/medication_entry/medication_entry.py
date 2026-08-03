import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, getdate


class MedicationEntry(Document):
	"""Withdrawal enforcement is the highest-value control in the system (§5.6).
	Residue violations are what cause consignment rejection and licence action."""

	def validate(self):
		if getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End date is before the start date."))
		if not cint(self.withdrawal_days) and self.medication:
			self.withdrawal_days = cint(
				frappe.db.get_value("Poultry Medication", self.medication, "withdrawal_days")
			)
		self.withdrawal_clear_date = add_days(getdate(self.end_date), cint(self.withdrawal_days))
		if not cint(self.birds_treated):
			self.birds_treated = cint(frappe.db.get_value("Flock", self.flock, "current_qty"))
