import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from poultry.poultry_utils import age_days, eef, recompute_flock


class FlockClosure(Document):
	"""Final settlement with frozen KPIs. After closure the flock's numbers no
	longer move, whatever happens to the shed next."""

	def validate(self):
		flock = recompute_flock(self.flock, update_status=False)

		self.placed_qty = cint(flock.opening_qty)
		self.total_mortality = cint(flock.cumulative_mortality)
		self.total_culls = cint(flock.cumulative_culls)
		self.total_sold = cint(flock.cumulative_sold) or cint(flock.current_qty)
		self.age_days = age_days(flock.placement_date, self.closure_date)
		self.livability_pct = flt(flock.livability_pct)
		self.cumulative_feed_kg = flt(flock.cumulative_feed_kg)
		self.cumulative_eggs = cint(flock.cumulative_eggs)
		self.total_cost = flt(flock.total_cost)

		if not flt(self.total_live_weight_kg):
			# fall back to standing live weight when nothing was weighed out
			self.total_live_weight_kg = flt(flock.current_qty) * flt(flock.avg_body_weight_g) / 1000.0

		sold = self.total_sold or flt(flock.current_qty)
		self.avg_sale_weight_kg = (flt(self.total_live_weight_kg) / sold) if sold else 0.0
		self.fcr = (
			flt(self.cumulative_feed_kg) / flt(self.total_live_weight_kg)
			if flt(self.total_live_weight_kg) else 0.0
		)
		self.adg_g = (
			flt(self.avg_sale_weight_kg) * 1000.0 / self.age_days if self.age_days else 0.0
		)
		self.eef = eef(self.livability_pct, flt(self.avg_sale_weight_kg) * 1000.0,
		               self.age_days, self.fcr)

		self.cost_per_bird = (flt(self.total_cost) / sold) if sold else 0.0
		self.cost_per_kg_live = (
			flt(self.total_cost) / flt(self.total_live_weight_kg)
			if flt(self.total_live_weight_kg) else 0.0
		)
		self.margin = flt(self.total_revenue) - flt(self.total_cost)

	def on_submit(self):
		flock = frappe.get_doc("Flock", self.flock)
		flock.status = "Closed"
		flock.closure_date = self.closure_date
		flock.total_live_weight_kg = self.total_live_weight_kg
		flock.total_revenue = self.total_revenue
		flock.margin = self.margin
		flock.flags.ignore_permissions = True
		flock.save(ignore_permissions=True)

		# shed goes to cleaning; downtime accrues from today (§7.3)
		frappe.db.set_value("Shed", flock.shed, {
			"status": "Cleaning",
			"current_flock": None,
			"last_depleted_on": self.closure_date,
		})
		if flock.project:
			frappe.db.set_value("Project", flock.project, "status", "Completed")

	def on_cancel(self):
		flock = frappe.get_doc("Flock", self.flock)
		flock.status = "Depleting"
		flock.closure_date = None
		flock.flags.ignore_permissions = True
		flock.save(ignore_permissions=True)
		frappe.db.set_value("Shed", flock.shed, {"status": "Occupied", "current_flock": flock.name})
