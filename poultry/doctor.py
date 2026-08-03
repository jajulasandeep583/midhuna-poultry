"""Self-check for the Poultry app. `bench --site <site> execute poultry.doctor.run`"""

import frappe
from frappe.utils import flt

GREEN = "\033[92mPASS\033[0m"
RED = "\033[91mFAIL\033[0m"

results = []


def check(label, ok, detail=""):
	results.append(ok)
	print(f"[{GREEN if ok else RED}] {label}" + (f"  -> {detail}" if detail else ""))


def run():
	global results
	results = []

	# ---------------------------------------------------------- schema
	doctypes = frappe.get_all("DocType", filters={"module": "Poultry Management"}, pluck="name")
	check("doctypes created", len(doctypes) >= 26, f"{len(doctypes)} doctypes")

	for dt in ("Flock", "Daily Flock Entry", "Shed", "Farm"):
		check(f"{dt} table exists", frappe.db.table_exists(dt))
	# Singles have no table of their own - they live in tabSingles
	check("Poultry Settings readable",
	      bool(frappe.get_single("Poultry Settings").get("data_tier")))

	for dt, field in (("Stock Entry", "poultry_flock"), ("Batch", "poultry_flock")):
		check(f"custom field {dt}.{field}",
		      bool(frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field})))

	# ---------------------------------------------------------- data
	counts = {
		"Farm": frappe.db.count("Farm"),
		"Shed": frappe.db.count("Shed"),
		"Flock": frappe.db.count("Flock"),
		"Daily Flock Entry": frappe.db.count("Daily Flock Entry", {"docstatus": 1}),
		"Bird Weighing": frappe.db.count("Bird Weighing", {"docstatus": 1}),
		"Vaccination Entry": frappe.db.count("Vaccination Entry", {"docstatus": 1}),
		"Medication Entry": frappe.db.count("Medication Entry", {"docstatus": 1}),
		"Flock Closure": frappe.db.count("Flock Closure", {"docstatus": 1}),
		"Breed Standard Detail": frappe.db.count("Breed Standard Detail"),
		"Stock Entry": frappe.db.count("Stock Entry", {"docstatus": 1}),
		"Sales Invoice": frappe.db.count("Sales Invoice", {"docstatus": 1}),
		"Purchase Receipt": frappe.db.count("Purchase Receipt", {"docstatus": 1}),
	}
	total = sum(counts.values())
	check("demo records loaded", total >= 300, f"{total} records: " +
	      ", ".join(f"{k} {v}" for k, v in counts.items()))

	# ---------------------------------------------------------- derivations
	flocks = frappe.get_all(
		"Flock",
		fields=["name", "flock_name", "flock_type", "status", "opening_qty", "current_qty",
		        "livability_pct", "cumulative_feed_kg", "avg_body_weight_g", "fcr", "eef",
		        "cumulative_eggs", "total_cost", "cost_per_bird", "cost_per_kg_live"],
		order_by="name",
	)
	check("flocks have derived counts",
	      all(f.current_qty and f.current_qty <= f.opening_qty for f in flocks))
	broilers = [f for f in flocks if f.flock_type == "Broiler"]
	check("broiler FCR in a sane range",
	      all(1.0 < flt(f.fcr) < 2.6 for f in broilers if flt(f.fcr)),
	      ", ".join(f"{f.flock_name}={flt(f.fcr):.2f}" for f in broilers))
	check("broiler EEF computed",
	      all(flt(f.eef) > 0 for f in broilers if flt(f.fcr)),
	      ", ".join(f"{f.flock_name}={flt(f.eef):.0f}" for f in broilers))
	check("cost per bird populated",
	      all(flt(f.cost_per_bird) > 0 for f in flocks if f.status != "Draft"))
	layers = [f for f in flocks if f.flock_type == "Layer"]
	check("layers produced eggs", all(f.cumulative_eggs > 0 for f in layers),
	      ", ".join(f"{f.flock_name}={f.cumulative_eggs}" for f in layers))

	# ---------------------------------------------------------- stock integrity
	linked = frappe.db.count("Stock Entry", {"docstatus": 1, "poultry_flock": ["!=", ""]})
	check("stock entries tagged to flocks", linked > 100, f"{linked} tagged")

	neg = frappe.db.sql(
		"""select count(*) from `tabBin` where actual_qty < 0"""
	)[0][0]
	check("no negative stock", neg == 0, f"{neg} negative bins")

	bird_stock = frappe.db.sql(
		"""select coalesce(sum(actual_qty),0) from `tabBin`
		   where item_code in ('BIRD-BRL','BIRD-LYR')"""
	)[0][0]
	alive = sum(f.current_qty for f in flocks if f.status not in ("Draft", "Closed"))
	closed_alive = sum(f.current_qty for f in flocks if f.status == "Closed")
	expected = alive + closed_alive
	drift = abs(flt(bird_stock) - expected)
	per_flock = []
	for f in flocks:
		shed_wh = frappe.db.get_value("Shed", frappe.db.get_value("Flock", f.name, "shed"),
		                              "warehouse")
		qty = frappe.db.sql(
			"""select coalesce(sum(actual_qty),0) from `tabBin`
			   where warehouse=%s and item_code in ('BIRD-BRL','BIRD-LYR')""", shed_wh)[0][0]
		if abs(flt(qty) - flt(f.current_qty)) >= 1:
			per_flock.append(f"{f.name} stock={flt(qty):.0f} flock={f.current_qty}")
	check("bird stock matches birds alive", drift < 1,
	      f"stock {flt(bird_stock):.0f} vs flocks {expected}"
	      + (f" | mismatched: {'; '.join(per_flock)}" if per_flock else ""))

	# ---------------------------------------------------------- reports
	from frappe.desk.query_report import run as run_report

	a_flock = frappe.db.get_value("Flock", {"flock_type": "Broiler"}, "name")
	a_layer = frappe.db.get_value("Flock", {"flock_type": "Layer"}, "name")
	report_args = {
		"Flock Performance vs Standard": {"flock": a_flock},
		"Broiler Batch Summary": {},
		"Mortality Analysis": {"group_by": "Reason"},
		"Layer Production Curve": {"flock": a_layer},
		"Feed Consumption and FCR Trend": {},
		"Vaccination Compliance": {"status_filter": "All"},
		"Withdrawal Period Alert": {},
		"Shed Utilisation and Downtime": {},
	}
	for name, filters in report_args.items():
		try:
			res = run_report(name, filters=filters, ignore_prepared_report=True)
			rows = len(res.get("result") or [])
			check(f"report: {name}", rows > 0, f"{rows} rows")
		except Exception as e:
			check(f"report: {name}", False, str(e).split("\n")[0][:140])

	# ---------------------------------------------------------- desk objects
	for ws in ("Poultry", "Poultry Setup", "Poultry Health", "Poultry Analytics"):
		check(f"workspace: {ws}", bool(frappe.db.exists("Workspace", ws)))
	check("number cards", frappe.db.count("Number Card", {"module": "Poultry Management"}) >= 8)
	check("dashboard charts",
	      frappe.db.count("Dashboard Chart", {"module": "Poultry Management"}) >= 4)
	check("roles created",
	      all(frappe.db.exists("Role", r) for r in
	          ("Poultry Manager", "Farm Manager", "Farm Supervisor", "Veterinarian")))

	# ---------------------------------------------------------- rules
	from poultry.poultry_utils import active_withdrawals
	withheld = [f.name for f in flocks if active_withdrawals(f.name)]
	check("withdrawal rule has live data", len(withheld) > 0, f"flocks under withdrawal: {withheld}")

	alerts = frappe.db.count("Daily Flock Entry", {"docstatus": 1, "has_alert": 1})
	check("alert engine fired", alerts > 0, f"{alerts} entries carry an alert")

	plans = frappe.db.count("Flock Vaccination Plan")
	check("vaccination plans generated", plans >= 8, f"{plans} plans")

	passed = sum(1 for r in results if r)
	print(f"\n{passed} passed, {len(results) - passed} failed")
	return passed, len(results) - passed
