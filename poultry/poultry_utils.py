"""Shared poultry calculations.

Two rules from the design document drive everything here:
  - derived, never entered  (§3.6)
  - recomputed, never incremented  (§3.7)

Flock running totals are therefore always re-aggregated from submitted Daily
Flock Entries. A cancelled or amended entry self-corrects; an incremented
counter would drift within weeks of the first correction.
"""

import frappe
from frappe.utils import cint, date_diff, flt, getdate, nowdate

EGGS_PER_TRAY_FALLBACK = 30


def settings():
	return frappe.get_cached_doc("Poultry Settings")


def eggs_per_tray():
	return cint(settings().eggs_per_tray) or EGGS_PER_TRAY_FALLBACK


def age_days(placement_date, on_date):
	"""A chick placed today is day 1 (§7.1)."""
	if not placement_date or not on_date:
		return 0
	return date_diff(getdate(on_date), getdate(placement_date)) + 1


def standard_row(flock_name, age):
	"""Snapshotted standard at or below this age. Never reads the live master -
	editing a master must not rewrite history (§3.8)."""
	rows = frappe.get_all(
		"Breed Standard Detail",
		filters={"parent": flock_name, "parenttype": "Flock"},
		fields=["age_days", "std_body_weight_g", "std_daily_feed_g", "std_cumulative_feed_g",
		        "std_fcr", "std_cumulative_mortality_pct", "std_hd_production_pct",
		        "std_egg_weight_g", "std_uniformity_pct", "std_water_feed_ratio"],
		order_by="age_days asc",
	)
	best = None
	for r in rows:
		if cint(r.age_days) <= cint(age):
			best = r
		else:
			break
	return best


def eef(livability_pct, avg_weight_g, age, fcr):
	"""European Efficiency Factor (§7.1). Below 250 poor, 350+ good."""
	if not (age and fcr):
		return 0.0
	return flt(livability_pct) * (flt(avg_weight_g) / 1000.0) / (flt(age) * flt(fcr)) * 100.0


def flock_cost(flock_name):
	"""Cost pool = day-old-chick receipt value + feed issued to the flock.

	Read from Stock Entries tagged with the flock, so the number always agrees
	with the stock ledger rather than being a parallel accumulator.
	"""
	rows = frappe.db.sql(
		"""
		select purpose, total_incoming_value, total_outgoing_value
		from `tabStock Entry`
		where docstatus = 1 and poultry_flock = %s
		""",
		flock_name,
		as_dict=True,
	)
	cost = 0.0
	for r in rows:
		if r.purpose == "Material Receipt":
			cost += flt(r.total_incoming_value)
		elif r.purpose == "Material Issue":
			cost += flt(r.total_outgoing_value)
	return cost


def recompute_flock(flock_name, update_status=True):
	"""Re-aggregate every derived number on a Flock from its submitted entries."""
	flock = frappe.get_doc("Flock", flock_name)

	agg = frappe.db.sql(
		"""
		select
			coalesce(sum(mortality_qty), 0)   as mortality,
			coalesce(sum(cull_qty), 0)        as culls,
			coalesce(sum(total_feed_kg), 0)   as feed_kg,
			coalesce(sum(total_eggs), 0)      as eggs,
			coalesce(max(hd_production_pct), 0) as peak_hdp,
			max(posting_date)                 as last_date,
			count(name)                       as entries
		from `tabDaily Flock Entry`
		where flock = %s and docstatus = 1
		""",
		flock_name,
		as_dict=True,
	)[0]

	# latest measured body weight: a dedicated weighing outranks a daily estimate
	weight = frappe.db.sql(
		"""
		select avg_body_weight_g from `tabBird Weighing`
		where flock = %s and docstatus = 1 and coalesce(avg_body_weight_g, 0) > 0
		order by posting_date desc, creation desc limit 1
		""",
		flock_name,
	)
	if not weight:
		weight = frappe.db.sql(
			"""
			select avg_body_weight_g from `tabDaily Flock Entry`
			where flock = %s and docstatus = 1 and coalesce(avg_body_weight_g, 0) > 0
			order by posting_date desc, creation desc limit 1
			""",
			flock_name,
		)
	avg_bw = flt(weight[0][0]) if weight else 0.0

	latest_hdp = frappe.db.sql(
		"""
		select hd_production_pct from `tabDaily Flock Entry`
		where flock = %s and docstatus = 1 and coalesce(total_eggs, 0) > 0
		order by posting_date desc, creation desc limit 1
		""",
		flock_name,
	)

	placed = cint(flock.opening_qty)
	sold = cint(flock.cumulative_sold)
	flock.cumulative_mortality = cint(agg.mortality)
	flock.cumulative_culls = cint(agg.culls)
	flock.current_qty = placed - cint(agg.mortality) - cint(agg.culls) - sold
	flock.cumulative_feed_kg = flt(agg.feed_kg, 3)
	flock.cumulative_eggs = cint(agg.eggs)

	as_of = flock.closure_date or nowdate()
	flock.age_days = age_days(flock.placement_date, as_of)

	losses = cint(agg.mortality) + cint(agg.culls)
	flock.mortality_pct = (losses / placed * 100.0) if placed else 0.0
	flock.livability_pct = 100.0 - flt(flock.mortality_pct)

	flock.avg_body_weight_g = avg_bw
	live_weight_kg = flt(flock.current_qty) * avg_bw / 1000.0
	flock.fcr = (flt(agg.feed_kg) / live_weight_kg) if live_weight_kg else 0.0
	flock.adg_g = (avg_bw / flock.age_days) if flock.age_days else 0.0
	flock.eef = eef(flock.livability_pct, avg_bw, flock.age_days, flock.fcr)

	flock.hd_production_pct = flt(latest_hdp[0][0]) if latest_hdp else 0.0
	flock.peak_production_pct = flt(agg.peak_hdp)
	flock.eggs_per_bird_housed = (cint(agg.eggs) / placed) if placed else 0.0

	flock.total_cost = flock_cost(flock_name)
	flock.cost_per_bird = (flt(flock.total_cost) / flock.current_qty) if flock.current_qty else 0.0
	flock.cost_per_kg_live = (flt(flock.total_cost) / live_weight_kg) if live_weight_kg else 0.0

	if update_status and flock.status not in ("Draft", "Closed"):
		flock.status = derive_status(flock, cint(agg.eggs))

	flock.flags.ignore_permissions = True
	flock.flags.ignore_validate_update_after_submit = True
	flock.save(ignore_permissions=True)
	return flock


def derive_status(flock, total_eggs):
	"""Layers move to Laying on the first recorded egg, never on a calendar
	date - onset of lay varies by weeks and a date rule falsifies the curve."""
	if flock.flock_type in ("Layer", "Breeder") and cint(total_eggs) > 0:
		return "Laying"
	if cint(flock.age_days) > 1:
		return "Growing"
	return flock.status or "Placed"


def active_withdrawals(flock_name, on_date=None):
	"""Medications whose withdrawal window still covers on_date (§6.4)."""
	on_date = getdate(on_date or nowdate())
	return frappe.get_all(
		"Medication Entry",
		filters={
			"flock": flock_name,
			"docstatus": 1,
			"withdrawal_clear_date": [">=", on_date],
		},
		fields=["name", "medication", "withdrawal_clear_date"],
	)
