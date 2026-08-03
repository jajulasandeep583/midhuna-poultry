import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate, nowdate

from poultry.poultry_utils import age_days, recompute_flock, settings


class Flock(Document):
	def validate(self):
		self.validate_shed_occupancy()
		self.warn_on_overcrowding()
		if not self.cost_center:
			self.cost_center = frappe.db.get_value("Farm", self.farm, "cost_center")
		if self.placement_date:
			self.age_days = age_days(self.placement_date, self.closure_date or nowdate())
		if not self.breed_standard and self.strain:
			self.breed_standard = frappe.db.get_value(
				"Breed Standard", {"strain": self.strain, "is_default": 1}, "name"
			) or frappe.db.get_value("Breed Standard", {"strain": self.strain}, "name")

	def validate_shed_occupancy(self):
		"""One active flock per shed. All-in all-out is a biosecurity
		requirement, not a preference (§7.3)."""
		if not self.shed or self.status == "Closed":
			return
		other = frappe.db.get_value(
			"Flock",
			{"shed": self.shed, "status": ["not in", ["Draft", "Closed"]], "name": ["!=", self.name or ""]},
			"name",
		)
		if other:
			frappe.throw(
				_("Shed {0} already holds active flock {1}. All-in all-out is enforced.").format(
					frappe.bold(self.shed), frappe.bold(other)
				)
			)

	def warn_on_overcrowding(self):
		"""Overcrowding is a business decision, not a data error - warn, never
		block (§7.3)."""
		if not self.shed or not self.opening_qty:
			return
		capacity = cint(frappe.db.get_value("Shed", self.shed, "capacity"))
		if capacity and cint(self.opening_qty) > capacity:
			frappe.msgprint(
				_("Placing {0} birds in a shed rated for {1}.").format(
					cint(self.opening_qty), capacity
				),
				title=_("Above Shed Capacity"),
				indicator="orange",
			)

	def on_trash(self):
		if frappe.db.exists("Daily Flock Entry", {"flock": self.name}):
			frappe.throw(_("Flock has daily entries and cannot be deleted."))


@frappe.whitelist()
def place_flock(flock_name, create_stock=None):
	"""Draft -> Placed (§6.1): batch, standard snapshot, costing container,
	vaccination plan, shed occupancy, and the day-old-chick stock receipt."""
	flock = frappe.get_doc("Flock", flock_name)
	if flock.status != "Draft":
		frappe.throw(_("Flock {0} is already placed.").format(flock_name))

	cfg = settings()
	create_stock = cint(cfg.create_stock_entries) if create_stock is None else cint(create_stock)

	flock.batch_no = make_batch(flock)
	snapshot_standard(flock)
	make_costing_container(flock, cfg)

	flock.status = "Placed"
	flock.current_qty = flock.opening_qty
	flock.age_days = age_days(flock.placement_date, nowdate())
	if not flock.expected_end_date and flock.strain:
		cycle = cint(frappe.db.get_value("Strain", flock.strain, "typical_cycle_days"))
		if cycle:
			flock.expected_end_date = add_days(getdate(flock.placement_date), cycle)
	flock.flags.ignore_permissions = True
	flock.save(ignore_permissions=True)

	frappe.db.set_value("Shed", flock.shed, {"status": "Occupied", "current_flock": flock.name,
	                                         "downtime_days": 0})

	if cint(cfg.auto_create_vaccination_plan):
		make_vaccination_plan(flock)

	if create_stock and flock.bird_item:
		receive_chicks(flock)

	return flock.name


def make_batch(flock):
	"""Batch equals flock (§3.3) - a retail egg traces back to its flock."""
	if not flock.bird_item:
		return None
	if not frappe.db.get_value("Item", flock.bird_item, "has_batch_no"):
		return None
	if frappe.db.exists("Batch", flock.name):
		return flock.name
	batch = frappe.get_doc({
		"doctype": "Batch",
		"batch_id": flock.name,
		"item": flock.bird_item,
		"batch_qty": flock.opening_qty,
		"manufacturing_date": flock.placement_date,
	})
	batch.flags.ignore_permissions = True
	batch.insert()
	return batch.name


def snapshot_standard(flock):
	"""Freeze the standard at placement so a later master edit cannot rewrite
	what a historical flock was measured against (§3.8)."""
	if not flock.breed_standard:
		return
	flock.set("standard_snapshot", [])
	rows = frappe.get_all(
		"Breed Standard Detail",
		filters={"parent": flock.breed_standard, "parenttype": "Breed Standard"},
		fields=["*"],
		order_by="age_days asc",
	)
	for r in rows:
		flock.append("standard_snapshot", {
			k: r.get(k) for k in (
				"age_days", "age_weeks", "std_body_weight_g", "std_daily_feed_g",
				"std_cumulative_feed_g", "std_fcr", "std_cumulative_mortality_pct",
				"std_hd_production_pct", "std_egg_weight_g", "std_uniformity_pct",
				"std_water_feed_ratio",
			)
		})


def make_costing_container(flock, cfg):
	"""Broiler = Work Order shaped; layer/breeder = Project, because a 70+ week
	cycle with continuous output cannot be expressed as a Work Order (§3.4)."""
	if flock.project:
		return
	project = frappe.get_doc({
		"doctype": "Project",
		"project_name": f"{flock.name} {flock.flock_name}",
		"company": flock.company,
		"status": "Open",
		"expected_start_date": flock.placement_date,
		"cost_center": flock.cost_center,
	})
	project.flags.ignore_permissions = True
	project.insert()
	flock.project = project.name


def make_vaccination_plan(flock):
	if frappe.db.exists("Flock Vaccination Plan", {"flock": flock.name}):
		return
	template = frappe.db.get_value(
		"Vaccination Schedule Template",
		{"strain": flock.strain, "is_default": 1}, "name"
	) or frappe.db.get_value(
		"Vaccination Schedule Template", {"flock_type": flock.flock_type, "is_default": 1}, "name"
	)
	if not template:
		return
	plan = frappe.get_doc({
		"doctype": "Flock Vaccination Plan",
		"flock": flock.name,
		"template": template,
		"placement_date": flock.placement_date,
	})
	for row in frappe.get_all(
		"Vaccination Schedule Detail",
		filters={"parent": template},
		fields=["age_days", "vaccine", "route", "dose_per_bird", "is_mandatory"],
		order_by="age_days asc",
	):
		plan.append("plan_details", {
			"age_days": row.age_days,
			"vaccine": row.vaccine,
			"route": row.route,
			"dose_per_bird": row.dose_per_bird,
			"is_mandatory": row.is_mandatory,
			# day 1 is placement day, so a day-N vaccination falls on placement + N-1
			"due_date": add_days(getdate(flock.placement_date), cint(row.age_days) - 1),
			"status": "Pending",
		})
	plan.flags.ignore_permissions = True
	plan.insert()
	return plan.name


def receive_chicks(flock):
	"""Day-old chicks into the shed warehouse. This is what puts a real
	valuation behind cost per bird."""
	shed_wh = frappe.db.get_value("Shed", flock.shed, "warehouse")
	if not shed_wh:
		return
	rate = flt(frappe.db.get_value("Item", flock.bird_item, "valuation_rate")) or 32.0
	se = frappe.get_doc({
		"doctype": "Stock Entry",
		"stock_entry_type": "Material Receipt",
		"purpose": "Material Receipt",
		"company": flock.company,
		"posting_date": flock.placement_date,
		"set_posting_time": 1,
		"poultry_flock": flock.name,
		"project": flock.project,
		"items": [{
			"item_code": flock.bird_item,
			"qty": flock.opening_qty,
			"uom": frappe.db.get_value("Item", flock.bird_item, "stock_uom"),
			"t_warehouse": shed_wh,
			"basic_rate": rate,
			"allow_zero_valuation_rate": 0,
			"batch_no": flock.batch_no,
			"cost_center": flock.cost_center,
		}],
	})
	se.flags.ignore_permissions = True
	se.insert()
	se.submit()
	return se.name


@frappe.whitelist()
def close_flock(flock_name, closure_date=None, total_live_weight_kg=0, total_revenue=0):
	"""Depleting -> Closed (§6.1): freeze KPIs, complete the project, send the
	shed to cleaning so downtime starts accruing."""
	flock = frappe.get_doc("Flock", flock_name)
	if flock.status == "Closed":
		frappe.throw(_("Flock {0} is already closed.").format(flock_name))
	closure_date = closure_date or nowdate()

	recompute_flock(flock_name, update_status=False)
	flock.reload()

	closure = frappe.get_doc({
		"doctype": "Flock Closure",
		"flock": flock.name,
		"closure_date": closure_date,
		"total_live_weight_kg": flt(total_live_weight_kg),
		"total_revenue": flt(total_revenue),
	})
	closure.flags.ignore_permissions = True
	closure.insert()
	closure.submit()
	return closure.name
