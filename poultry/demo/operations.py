"""Operational demo data: flocks, daily entries, health records, closures, sales.

Numbers are generated off each flock's own snapshotted breed standard with a
little noise, so the dataset behaves like a real farm - the variance reports
have something to show and the alert rules genuinely fire.
"""

import random

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from poultry.poultry_utils import recompute_flock, standard_row

COMPANY = "Midhuna Poultry"
ABBR = "MP"
TODAY = getdate(nowdate())

random.seed(20260803)


def wh(n):
	return f"{n} - {ABBR}"


def acc(n):
	return f"{n} - {ABBR}"


# ------------------------------------------------------------------ fiscal
def ensure_fiscal_years():
	for name, start, end in [
		("2024-2025", "2024-04-01", "2025-03-31"),
		("2025-2026", "2025-04-01", "2026-03-31"),
	]:
		if frappe.db.exists("Fiscal Year", name):
			continue
		fy = frappe.get_doc({"doctype": "Fiscal Year", "year": name,
		                     "year_start_date": start, "year_end_date": end})
		fy.flags.ignore_permissions = True
		fy.insert()
		print("  + fiscal year:", name)


# ------------------------------------------------------------------ feed stock
FEED_LOAD = {
	"Broiler": [("FEED-BPS", 3000), ("FEED-BST", 10000), ("FEED-BFN", 26000)],
	"Layer": [("FEED-LP1", 40000), ("FEED-LP2", 40000), ("FEED-CHM", 4000), ("FEED-GRW", 8000)],
	"Rearing": [("FEED-CHM", 10000), ("FEED-GRW", 25000)],
}


# A farm buys feed continuously; a single opening balance runs dry mid-cycle and
# is not how the ledger should read anyway. These are real purchases from real
# suppliers, so Accounts Payable and feed cost per kg have something behind them.
FEED_BUY = {
	"Broiler": [("FEED-BPS", 4000), ("FEED-BST", 15000), ("FEED-BFN", 55000)],
	"Layer": [("FEED-CHM", 6000), ("FEED-GRW", 10000), ("FEED-LP1", 110000), ("FEED-LP2", 30000)],
	"Rearing": [("FEED-CHM", 22000), ("FEED-GRW", 45000)],
}

FEED_SUPPLIER = {
	"Ramgundam Broiler Farm": "Godrej Agrovet Feed",
	"Siddipet Layer Farm": "SKM Animal Feeds",
	"Zaheerabad Rearing Unit": "Godrej Agrovet Feed",
}


def buy_feed(posting_date):
	"""One Purchase Receipt per farm, landed before the first daily entry."""
	made = 0
	for farm in frappe.get_all("Farm", fields=["name", "farm_type"]):
		if frappe.db.exists("Purchase Receipt", {"docstatus": 1, "remarks": f"Feed supply {farm.name}"}):
			continue
		pr = frappe.get_doc({
			"doctype": "Purchase Receipt",
			"company": COMPANY,
			"supplier": FEED_SUPPLIER.get(farm.name, "Godrej Agrovet Feed"),
			"posting_date": posting_date,
			"set_posting_time": 1,
			"remarks": f"Feed supply {farm.name}",
			"items": [],
		})
		for shed in frappe.get_all("Shed", filters={"farm": farm.name},
		                           fields=["name", "warehouse"]):
			for item, qty in FEED_BUY.get(farm.farm_type, []):
				rate = flt(frappe.db.get_value("Item", item, "valuation_rate"))
				pr.append("items", {
					"item_code": item, "qty": qty, "rate": rate,
					"warehouse": shed.warehouse, "received_qty": qty,
				})
		if not pr.items:
			continue
		pr.flags.ignore_permissions = True
		pr.insert()
		pr.submit()
		made += 1
		print(f"  + purchase receipt {pr.name} for {farm.name}: {len(pr.items)} rows")
	frappe.db.commit()
	return made


def load_feed_stock(posting_date):
	if frappe.db.exists("Stock Reconciliation", {"docstatus": 1, "purpose": "Opening Stock"}):
		print("  = feed stock already loaded")
		return
	sr = frappe.get_doc({
		"doctype": "Stock Reconciliation",
		"company": COMPANY,
		"purpose": "Opening Stock",
		"posting_date": posting_date,
		"set_posting_time": 1,
		"expense_account": acc("Temporary Opening"),
		"items": [],
	})
	for shed in frappe.get_all("Shed", fields=["name", "farm", "warehouse"]):
		ftype = frappe.db.get_value("Farm", shed.farm, "farm_type")
		for item, qty in FEED_LOAD.get(ftype, []):
			rate = flt(frappe.db.get_value("Item", item, "valuation_rate"))
			sr.append("items", {
				"item_code": item, "warehouse": shed.warehouse,
				"qty": qty, "valuation_rate": rate,
			})
	sr.flags.ignore_permissions = True
	sr.insert()
	sr.submit()
	print(f"  + opening feed stock: {len(sr.items)} rows")


# ------------------------------------------------------------------ flocks
# (shed, name, type, strain, bird item, placed days ago, qty, entry window days)
FLOCKS = [
	("Ramgundam Broiler Farm-SH-01", "Broiler Cycle 11", "Broiler", "Cobb 500", "BIRD-BRL", 44, 11500, 42),
	("Ramgundam Broiler Farm-SH-02", "Broiler Cycle 12", "Broiler", "Ross 308", "BIRD-BRL", 35, 11800, 35),
	("Ramgundam Broiler Farm-SH-03", "Broiler Cycle 13", "Broiler", "Cobb 500", "BIRD-BRL", 22, 9800, 22),
	("Ramgundam Broiler Farm-SH-04", "Broiler Cycle 14", "Broiler", "Vencobb 430", "BIRD-BRL", 11, 9600, 11),
	("Siddipet Layer Farm-LH-01", "Layer Batch 07", "Layer", "BV-300", "BIRD-LYR", 262, 19500, 30),
	("Siddipet Layer Farm-LH-02", "Layer Batch 08", "Layer", "Hy-Line W-36", "BIRD-LYR", 191, 19200, 30),
	("Siddipet Layer Farm-LH-03", "Layer Batch 09", "Layer", "BV-300", "BIRD-LYR", 151, 17600, 26),
	("Zaheerabad Rearing Unit-RH-01", "Pullet Batch 05", "Rearing", "BV-300", "BIRD-LYR", 71, 14500, 30),
	("Zaheerabad Rearing Unit-RH-02", "Pullet Batch 06", "Rearing", "Hy-Line W-36", "BIRD-LYR", 30, 14200, 30),
]

FEED_FOR_TYPE = {
	"Broiler": [(1, 10, "Broiler Pre-Starter"), (11, 24, "Broiler Starter"), (25, 99, "Broiler Finisher")],
	"Layer": [(1, 56, "Chick Mash"), (57, 126, "Grower Mash"), (127, 350, "Layer Phase-1"),
	          (351, 999, "Layer Phase-2")],
	"Rearing": [(1, 56, "Pullet Chick Mash"), (57, 999, "Pullet Grower Mash")],
}


def feed_type_for(flock_type, age):
	for lo, hi, name in FEED_FOR_TYPE[flock_type]:
		if lo <= age <= hi:
			return name
	return FEED_FOR_TYPE[flock_type][-1][2]


def create_flocks():
	from poultry.poultry_management.doctype.flock.flock import place_flock

	made = []
	for shed, name, ftype, strain, item, ago, qty, window in FLOCKS:
		if frappe.db.exists("Flock", {"flock_name": name}):
			made.append(frappe.db.get_value("Flock", {"flock_name": name}, "name"))
			continue
		farm = frappe.db.get_value("Shed", shed, "farm")
		breed = frappe.db.get_value("Strain", strain, "breed")
		placement = add_days(TODAY, -ago)
		doc = frappe.get_doc({
			"doctype": "Flock",
			"flock_name": name,
			"farm": farm,
			"shed": shed,
			"flock_type": ftype,
			"breed": breed,
			"strain": strain,
			"source": "Purchased DOC",
			"supplier": frappe.db.get_value("Strain", strain, "supplier"),
			"placement_date": placement,
			"hatch_date": add_days(placement, -1),
			"bird_item": item,
			"opening_qty": qty,
			"parent_flock_age_weeks": random.choice([32, 38, 45, 52, 58]),
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		place_flock(doc.name)
		made.append(doc.name)
		print(f"  + flock {doc.name} {name} ({ftype}, {qty} birds, placed {placement})")
	frappe.db.commit()
	return made


# ------------------------------------------------------------------ daily entries
EGG_MIX = [("S", 0.10), ("M", 0.34), ("L", 0.38), ("XL", 0.12), ("CR", 0.06)]


def generate_entries():
	total = 0
	failed = []
	for shed, name, ftype, strain, item, ago, qty, window in FLOCKS:
		flock_name = frappe.db.get_value("Flock", {"flock_name": name}, "name")
		flock = frappe.get_doc("Flock", flock_name)
		start_age = max(1, ago - window + 1)

		# A flock older than its entry window gets one catch-up row carrying the
		# losses that happened before the system went live (§11.6).
		if start_age > 1:
			total += make_catchup(flock, start_age)

		# +2 so today's own entry is written: a demo where every "today" card
		# reads zero looks broken even though the history is fine
		for age in range(start_age, ago + 2):
			d = add_days(getdate(flock.placement_date), age - 1)
			if getdate(d) > TODAY:
				break
			if frappe.db.exists("Daily Flock Entry",
			                    {"flock": flock.name, "posting_date": d, "docstatus": ["<", 2]}):
				continue
			try:
				make_entry(flock, age, d)
				total += 1
			except Exception as e:
				# one bad day must not abandon the rest of the run
				frappe.db.rollback()
				failed.append((flock.name, str(d), str(e).split("\n")[0][:160]))
				continue
			if total % 25 == 0:
				frappe.db.commit()
				print(f"    ... {total} daily entries")
	frappe.db.commit()
	print("  + daily entries:", total)
	if failed:
		print("  ! failed:", len(failed))
		for row in failed[:10]:
			print("    -", row)
	return total


def make_catchup(flock, start_age):
	"""One row for everything that happened before the window opened."""
	d = add_days(getdate(flock.placement_date), start_age - 2)
	if frappe.db.exists("Daily Flock Entry", {"flock": flock.name, "posting_date": d}):
		return 0
	std = standard_row(flock.name, start_age - 1)
	mort_pct = flt(std.std_cumulative_mortality_pct) if std else 2.0
	losses = int(cint(flock.opening_qty) * mort_pct / 100.0)
	culls = int(losses * 0.35)
	doc = frappe.get_doc({
		"doctype": "Daily Flock Entry",
		"flock": flock.name,
		"posting_date": d,
		"entry_source": "Catch-up",
		"mortality_qty": losses - culls,
		"cull_qty": culls,
		"remarks": f"Catch-up: losses recorded up to day {start_age - 1} before go-live",
	})
	doc.append("mortality_details", {"reason": "Chick Mortality (First Week)",
	                                 "qty": losses - culls})
	doc.append("mortality_details", {"reason": "Runt / Weak Bird Culled", "qty": culls})
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	return 1


def make_entry(flock, age, d):
	std = standard_row(flock.name, age)
	birds = cint(flock.opening_qty)
	alive = frappe.db.sql(
		"""select coalesce(sum(mortality_qty),0)+coalesce(sum(cull_qty),0)
		   from `tabDaily Flock Entry` where flock=%s and docstatus=1""", flock.name)[0][0]
	alive = birds - cint(alive)

	doc = frappe.get_doc({
		"doctype": "Daily Flock Entry",
		"flock": flock.name,
		"posting_date": d,
		"entry_source": random.choice(["Desk", "Field App", "Field App", "Field App", "Bot"]),
	})

	# --- mortality: a low daily base with the odd bad day
	base = 0.00035 if flock.flock_type == "Broiler" else 0.00018
	if age <= 7:
		base *= 2.4
	spike = random.random() < 0.06
	rate = base * (random.uniform(0.4, 1.7) if not spike else random.uniform(4.0, 9.0))
	deaths = max(0, int(alive * rate))
	culls = int(deaths * 0.3)
	doc.mortality_qty = deaths - culls
	doc.cull_qty = culls
	if deaths - culls > 0:
		doc.append("mortality_details", {
			"reason": random.choice(["Ascites", "Colibacillosis", "Coccidiosis", "Heat Stress",
			                         "Chick Mortality (First Week)", "Unknown"]),
			"qty": deaths - culls,
		})
	if culls > 0:
		doc.append("mortality_details", {"reason": "Runt / Weak Bird Culled", "qty": culls})

	# --- feed: standard grams per bird, with real-world scatter
	g = flt(std.std_daily_feed_g) if std else 90
	feed_kg = alive * g * random.uniform(0.94, 1.06) / 1000.0
	ft = feed_type_for(flock.flock_type, age)
	bag = flt(frappe.db.get_value("Feed Type", ft, "bag_weight_kg")) or 50
	doc.append("feed_details", {"feed_type": ft, "bags": round(feed_kg / bag, 1)})

	# --- water, weight
	doc.water_litres = round(feed_kg * random.uniform(1.7, 2.05), 1)
	if std and (age % 7 == 0 or flock.flock_type == "Broiler"):
		doc.avg_body_weight_g = round(flt(std.std_body_weight_g) * random.uniform(0.95, 1.05), 1)
		doc.sample_size = 100
		doc.uniformity_pct = round(random.uniform(78, 92), 1)

	# --- eggs
	if flock.flock_type == "Layer" and std and flt(std.std_hd_production_pct) > 0:
		hdp = flt(std.std_hd_production_pct) * random.uniform(0.95, 1.03)
		eggs = int(alive * hdp / 100.0)
		for grade, share in EGG_MIX:
			q = int(eggs * share)
			if q:
				doc.append("egg_details", {"egg_grade": grade, "trays": round(q / 30.0, 2)})
		doc.avg_egg_weight_g = round(random.uniform(55, 61), 1)
		doc.floor_eggs = int(eggs * random.uniform(0.002, 0.01))

	# --- environment
	doc.min_temp = round(random.uniform(21, 26), 1)
	doc.max_temp = round(random.uniform(31, 38), 1)
	doc.humidity_pct = round(random.uniform(48, 76), 1)
	doc.litter_condition = random.choice(["Dry", "Friable", "Friable", "Damp"])
	doc.light_hours = 16 if flock.flock_type == "Layer" else 23

	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()


# ------------------------------------------------------------------ health
def generate_health():
	made = 0
	for plan in frappe.get_all("Flock Vaccination Plan", fields=["name", "flock"]):
		doc = frappe.get_doc("Flock Vaccination Plan", plan.name)
		for row in doc.plan_details:
			if row.status == "Done" or not row.due_date:
				continue
			if getdate(row.due_date) > TODAY:
				continue
			# leave the most recent couple of doses undone so compliance
			# reporting has real overdue rows to show
			if getdate(row.due_date) > add_days(TODAY, -4):
				continue
			if frappe.db.exists("Vaccination Entry",
			                    {"flock": plan.flock, "vaccine": row.vaccine, "docstatus": 1}):
				continue
			ve = frappe.get_doc({
				"doctype": "Vaccination Entry",
				"flock": plan.flock,
				"posting_date": row.due_date,
				"vaccine": row.vaccine,
				"route": row.route,
				"dose_per_bird": row.dose_per_bird or 1,
				"vial_batch": f"VB{random.randint(10000, 99999)}",
				"vial_serial": f"SL-{random.randint(100, 999)}",
				"diluent": "Chilled distilled water" if row.route == "Drinking Water" else "",
				"wastage_pct": round(random.uniform(1, 6), 1),
				"operator": random.choice(["K. Srinivas", "M. Ramesh", "P. Anjaiah", "Dr. Latha"]),
			})
			ve.flags.ignore_permissions = True
			ve.insert()
			ve.submit()
			made += 1
	frappe.db.commit()
	print("  + vaccination entries:", made)

	meds = 0
	for flock_name, med, days_ago, dur in [
		(_flock("Broiler Cycle 13"), "Enrofloxacin 10%", 6, 3),
		(_flock("Broiler Cycle 12"), "Toltrazuril 2.5%", 19, 2),
		(_flock("Layer Batch 08"), "Vitamin AD3E + C", 9, 4),
		(_flock("Pullet Batch 05"), "Amoxicillin Soluble", 14, 4),
	]:
		if not flock_name or frappe.db.exists("Medication Entry",
		                                      {"flock": flock_name, "medication": med}):
			continue
		start = add_days(TODAY, -days_ago)
		me = frappe.get_doc({
			"doctype": "Medication Entry",
			"flock": flock_name,
			"medication": med,
			"start_date": start,
			"end_date": add_days(start, dur),
			"dose": frappe.db.get_value("Poultry Medication", med, "dose"),
			"route": "Drinking Water",
			"reason": random.choice(["E. coli suspected", "Wet litter and loose droppings",
			                         "Post-vaccination support", "Coccidiosis control"]),
			"prescriber": "Dr. Latha Reddy, Veterinarian",
		})
		me.flags.ignore_permissions = True
		me.insert()
		me.submit()
		meds += 1
	frappe.db.commit()
	print("  + medication entries:", meds)


def _flock(flock_name):
	return frappe.db.get_value("Flock", {"flock_name": flock_name}, "name")


def generate_weighings():
	made = 0
	for shed, name, ftype, strain, item, ago, qty, window in FLOCKS:
		flock_name = _flock(name)
		flock = frappe.get_doc("Flock", flock_name)
		start_age = max(7, ago - window + 1)
		for age in range(start_age, ago + 1):
			if age % 7:
				continue
			d = add_days(getdate(flock.placement_date), age - 1)
			if getdate(d) > TODAY or frappe.db.exists(
					"Bird Weighing", {"flock": flock.name, "posting_date": d, "docstatus": 1}):
				continue
			std = standard_row(flock.name, age)
			if not std:
				continue
			sample = 100
			avg = flt(std.std_body_weight_g) * random.uniform(0.94, 1.06)
			bw = frappe.get_doc({
				"doctype": "Bird Weighing",
				"flock": flock.name,
				"posting_date": d,
				"sample_size": sample,
				"total_weight_g": round(avg * sample, 1),
				"uniformity_pct": round(random.uniform(76, 92), 1),
				"cv_pct": round(random.uniform(6, 12), 1),
			})
			bw.flags.ignore_permissions = True
			bw.insert()
			bw.submit()
			made += 1
	frappe.db.commit()
	print("  + bird weighings:", made)


# ------------------------------------------------------------------ closure
def close_finished():
	from poultry.poultry_management.doctype.flock.flock import close_flock

	flock_name = _flock("Broiler Cycle 11")
	if not flock_name:
		return
	flock = frappe.get_doc("Flock", flock_name)
	if flock.status == "Closed":
		print("  = already closed")
		return
	live_kg = flt(flock.current_qty) * flt(flock.avg_body_weight_g) / 1000.0
	revenue = live_kg * 118.0
	close_flock(flock_name, closure_date=add_days(TODAY, -2),
	            total_live_weight_kg=round(live_kg, 2), total_revenue=round(revenue, 2))
	frappe.db.commit()
	print("  + closed flock:", flock_name)


# ------------------------------------------------------------------ sales
def generate_sales():
	made = 0
	if frappe.db.exists("Sales Invoice", {"docstatus": 1, "company": COMPANY}):
		print("  = sales already generated")
		return
	customers = ["Hyderabad Egg Mandi", "Sri Lakshmi Poultry Traders", "Metro Fresh Retail"]
	prices = {"EGG-SML": 5.10, "EGG-MED": 5.85, "EGG-LRG": 6.60, "EGG-JUM": 7.20, "EGG-CRK": 2.40}

	for i in range(9):
		d = add_days(TODAY, -(i * 3 + 1))
		cust = customers[i % len(customers)]
		si = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": cust,
			"company": COMPANY,
			"posting_date": d,
			"set_posting_time": 1,
			"update_stock": 1,
			"set_warehouse": wh("Egg Cold Store"),
			"items": [],
		})
		for code in ("EGG-MED", "EGG-LRG"):
			bal = get_balance(code, wh("Egg Cold Store"), d)
			if bal < 2000:
				continue
			qty = min(int(bal * 0.35), random.randint(9000, 20000))
			if qty < 500:
				continue
			si.append("items", {"item_code": code, "qty": qty, "rate": prices[code],
			                    "warehouse": wh("Egg Cold Store")})
		if not si.items:
			continue
		si.flags.ignore_permissions = True
		si.insert()
		si.submit()
		made += 1
	frappe.db.commit()
	print("  + egg sales invoices:", made)


def get_balance(item, warehouse, upto):
	bal = frappe.db.sql(
		"""select coalesce(sum(actual_qty),0) from `tabStock Ledger Entry`
		   where item_code=%s and warehouse=%s and posting_date<=%s and is_cancelled=0""",
		(item, warehouse, upto))[0][0]
	return flt(bal)


# ------------------------------------------------------------------ run
def run(step=None):
	if step in (None, "base"):
		print("--- fiscal years ---"); ensure_fiscal_years()
		print("--- feed stock ---");   load_feed_stock(add_days(TODAY, -300))
		print("--- feed purchases ---"); buy_feed(add_days(TODAY, -50))
		print("--- flocks ---");       create_flocks()
		frappe.db.commit()
	if step == "feed":
		buy_feed(add_days(TODAY, -50))
	if step in (None, "entries"):
		print("--- daily entries ---"); generate_entries()
	if step in (None, "health"):
		print("--- weighings ---");     generate_weighings()
		print("--- health ---");        generate_health()
	if step in (None, "finish"):
		print("--- closure ---");       close_finished()
		print("--- sales ---");         generate_sales()
		print("--- recompute ---")
		for f in frappe.get_all("Flock", pluck="name"):
			recompute_flock(f)
		frappe.db.commit()
	print("OPS STEP DONE:", step or "all")
