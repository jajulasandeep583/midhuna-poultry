import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from poultry.poultry_utils import age_days, recompute_flock, standard_row


class BirdWeighing(Document):
	def validate(self):
		flock = frappe.get_doc("Flock", self.flock)
		self.age_days = age_days(flock.placement_date, self.posting_date)
		if cint(self.sample_size):
			self.avg_body_weight_g = flt(self.total_weight_g) / cint(self.sample_size)

		std = standard_row(self.flock, self.age_days)
		self.std_body_weight_g = flt(std.std_body_weight_g) if std else 0.0
		if self.std_body_weight_g:
			self.variance_pct = (
				(flt(self.avg_body_weight_g) - self.std_body_weight_g) / self.std_body_weight_g * 100.0
			)
		else:
			self.variance_pct = 0.0

	def on_submit(self):
		recompute_flock(self.flock)

	def on_cancel(self):
		recompute_flock(self.flock)
