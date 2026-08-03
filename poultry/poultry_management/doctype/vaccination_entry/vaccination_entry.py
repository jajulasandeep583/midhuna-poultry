import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from poultry.poultry_utils import age_days


class VaccinationEntry(Document):
	def validate(self):
		flock = frappe.get_doc("Flock", self.flock)
		self.age_days = age_days(flock.placement_date, self.posting_date)
		if self.vaccine and not self.route:
			self.route = frappe.db.get_value("Vaccine", self.vaccine, "route")
		if not cint(self.birds_covered):
			self.birds_covered = cint(flock.current_qty)

	def on_submit(self):
		self.update_plan("Done")

	def on_cancel(self):
		self.update_plan("Pending")

	def update_plan(self, status):
		"""Close off the matching planned dose so compliance reporting is real
		rather than a parallel tick-list."""
		plan = frappe.db.get_value("Flock Vaccination Plan", {"flock": self.flock}, "name")
		if not plan:
			return
		doc = frappe.get_doc("Flock Vaccination Plan", plan)
		for row in doc.plan_details:
			matched = (
				row.vaccine == self.vaccine
				and (row.status != "Done" if status == "Done" else row.vaccination_entry == self.name)
			)
			if matched:
				row.status = status
				row.done_on = self.posting_date if status == "Done" else None
				row.vaccination_entry = self.name if status == "Done" else None
				break
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
