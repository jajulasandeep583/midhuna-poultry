import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class FlockVaccinationPlan(Document):
	def validate(self):
		pending = overdue = 0
		today = getdate(nowdate())
		for row in self.plan_details:
			if row.status == "Done":
				continue
			if row.due_date and getdate(row.due_date) < today:
				row.status = "Overdue"
				overdue += 1
			elif row.status != "Skipped":
				row.status = "Pending"
				pending += 1
		self.pending_count = pending
		self.overdue_count = overdue
