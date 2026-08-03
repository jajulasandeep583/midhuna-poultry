"""Hatchery demo data for an AP/Telangana operation.

Chick types, breeder-farm egg receipts with grading, incubation parameters and
breakout analysis on the hatches that finished. Volumes and percentages sit
where a commercial hatchery in the Hyderabad-Vijayawada belt actually runs.
"""

import random

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

COMPANY = "Midhuna Poultry"
ABBR = "MP"
TODAY = getdate(nowdate())

random.seed(20260805)


def wh(n):
	return f"{n} - {ABBR}"


def _insert(doc):
	d = frappe.get_doc(doc)
	d.flags.ignore_permissions = True
	d.flags.ignore_mandatory = True
	d.insert()
	return d


# what an AP/Telangana hatchery actually sets. Vanaraja, Gramapriya and Rajasri
# are the ICAR-DPR Hyderabad backyard birds the state distributes.
CHICK_TYPES = [
	("Cobb 500 Broiler Chick", "Broiler", "Cobb 500", 93.5, 84.5, 42.0, 21),
	("Vencobb 430 Broiler Chick", "Broiler", "Vencobb 430", 93.0, 84.0, 41.0, 21),
	("Ross 308 Broiler Chick", "Broiler", "Ross 308", 93.0, 83.5, 42.5, 21),
	("BV-300 Layer Chick", "Layer", "BV-300", 94.0, 85.0, 36.0, 21),
	("Hy-Line W-36 Layer Chick", "Layer", "Hy-Line W-36", 94.5, 85.5, 35.0, 21),
	("Vanaraja Chick", "Desi / Native", None, 88.0, 78.0, 38.0, 21),
	("Gramapriya Chick", "Desi / Native", None, 87.0, 77.0, 37.0, 21),
	("Rajasri Chick", "Desi / Native", None, 87.5, 77.5, 37.5, 21),
]

BREEDER_SUPPLIERS = [
	("Srinivasa Breeding Farms, Vijayawada", "Local"),
	("Venkateshwara Breeder Unit, Chittoor", "Local"),
	("ICAR-DPR Hyderabad (Vanaraja / Gramapriya)", "Local"),
	("Sneha Breeder Farm, Warangal", "Local"),
]

ITEMS = [
	("EGG-HAT-BRL", "Broiler Hatching Egg", 9.20),
	("EGG-HAT-LYR", "Layer Hatching Egg", 10.50),
	("EGG-HAT-DSI", "Desi Hatching Egg", 8.00),
	("CHICK-BRL", "Day Old Chick - Broiler", 32.0),
	("CHICK-LYR", "Day Old Chick - Layer Pullet", 46.0),
	("CHICK-DSI", "Day Old Chick - Vanaraja / Desi", 28.0),
]

TYPE_ITEMS = {
	"Broiler": ("EGG-HAT-BRL", "CHICK-BRL"),
	"Layer": ("EGG-HAT-LYR", "CHICK-LYR"),
	"Desi / Native": ("EGG-HAT-DSI", "CHICK-DSI"),
}


def make_masters():
	for code, name, rate in ITEMS:
		if frappe.db.exists("Item", code):
			continue
		_insert({"doctype": "Item", "item_code": code, "item_name": name,
		         "item_group": "Poultry", "stock_uom": "Nos", "is_stock_item": 1,
		         "valuation_rate": rate, "is_purchase_item": 1, "is_sales_item": 1,
		         "item_defaults": [{"company": COMPANY,
		                            "default_warehouse": wh("Hatchery Chick Hold")}]})

	for name, group in BREEDER_SUPPLIERS:
		if not frappe.db.exists("Supplier", name):
			_insert({"doctype": "Supplier", "supplier_name": name,
			         "supplier_group": group, "supplier_type": "Company"})

	for name, cat, strain, fert, hatch, wt, days in CHICK_TYPES:
		if frappe.db.exists("Chick Type", name):
			continue
		egg_item, chick_item = TYPE_ITEMS[cat]
		_insert({"doctype": "Chick Type", "chick_type_name": name, "category": cat,
		         "strain": strain if strain and frappe.db.exists("Strain", strain) else None,
		         "egg_item": egg_item, "chick_item": chick_item,
		         "is_sexed": 1 if cat == "Layer" else 0,
		         "std_fertility_pct": fert, "std_hatchability_pct": hatch,
		         "std_chick_weight_g": wt, "incubation_days": days})
	print(f"  + chick types: {len(CHICK_TYPES)}, breeder suppliers, hatching-egg items")


# (days ago, chick type, supplier, eggs received, breeder age weeks)
RECEIPTS = [
	(32, "Cobb 500 Broiler Chick", 0, 56000, 34),
	(29, "Vencobb 430 Broiler Chick", 1, 51000, 45),
	(26, "BV-300 Layer Chick", 0, 54000, 38),
	(23, "Ross 308 Broiler Chick", 3, 53000, 52),
	(20, "Vanaraja Chick", 2, 28000, 41),
	(12, "Cobb 500 Broiler Chick", 0, 55000, 36),
	(6, "Gramapriya Chick", 2, 26000, 44),
	(3, "BV-300 Layer Chick", 0, 52000, 40),
	(1, "Vencobb 430 Broiler Chick", 1, 49000, 47),
]


def make_receipts():
	made = 0
	for ago, ctype, sup_idx, eggs, age in RECEIPTS:
		d = add_days(TODAY, -ago)
		if frappe.db.exists("Hatching Egg Receipt",
		                    {"posting_date": d, "eggs_received": eggs, "docstatus": 1}):
			continue
		cracked = int(eggs * random.uniform(0.008, 0.019))
		dirty = int(eggs * random.uniform(0.006, 0.016))
		small = int(eggs * random.uniform(0.004, 0.011))
		mis = int(eggs * random.uniform(0.002, 0.007))
		doc = frappe.get_doc({
			"doctype": "Hatching Egg Receipt",
			"posting_date": d,
			"supplier": BREEDER_SUPPLIERS[sup_idx][0],
			"chick_type": ctype,
			"company": COMPANY,
			"breeder_age_weeks": age,
			"eggs_received": eggs,
			"cracked_eggs": cracked,
			"dirty_eggs": dirty,
			"small_eggs": small,
			"misshapen_eggs": mis,
			"fumigated": 1,
			"avg_egg_weight_g": round(random.uniform(56, 66), 1),
			"store_room": random.choice(["Cold Store 1", "Cold Store 2"]),
			"store_temp_c": round(random.uniform(16.8, 18.4), 1),
			"store_humidity_pct": round(random.uniform(72, 80), 1),
			"remarks": "Graded and fumigated on arrival",
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		made += 1
	frappe.db.commit()
	print(f"  + hatching egg receipts: {made}")


def link_settings():
	"""Attach the existing settings to a receipt and fill the incubation fields."""
	receipts = frappe.get_all(
		"Hatching Egg Receipt", filters={"docstatus": 1},
		fields=["name", "posting_date", "chick_type", "settable_eggs"],
		order_by="posting_date asc")
	if not receipts:
		return
	updated = 0
	for s in frappe.get_all("Egg Setting", filters={"docstatus": 1},
	                        fields=["name", "set_date", "egg_receipt"], order_by="set_date"):
		if s.egg_receipt:
			continue
		# the receipt just before this setting, which is how eggs actually flow
		prior = [r for r in receipts if getdate(r.posting_date) <= getdate(s.set_date)]
		if not prior:
			continue
		r = prior[-1]
		frappe.db.set_value("Egg Setting", s.name, {
			"egg_receipt": r.name,
			"chick_type": r.chick_type,
			"prewarm_hours": round(random.uniform(6, 12), 1),
			"setter_temp_c": round(random.uniform(37.4, 37.8), 2),
			"setter_humidity_pct": round(random.uniform(53, 58), 1),
			"turning_per_day": 24,
		}, update_modified=False)
		updated += 1

	for h in frappe.get_all("Hatch Entry", filters={"docstatus": 1}, pluck="name"):
		frappe.db.set_value("Hatch Entry", h, {
			"hatcher_temp_c": round(random.uniform(36.8, 37.2), 2),
			"hatcher_humidity_pct": round(random.uniform(64, 72), 1),
		}, update_modified=False)

	frappe.db.commit()
	print(f"  + settings linked to receipts: {updated}")


def make_breakouts():
	"""Break out the residue on every hatch that finished."""
	made = 0
	for h in frappe.get_all("Hatch Entry", filters={"docstatus": 1},
	                        fields=["name", "egg_setting", "posting_date", "eggs_set",
	                                "chicks_hatched"]):
		if frappe.db.exists("Breakout Analysis",
		                    {"egg_setting": h.egg_setting, "docstatus": 1}):
			continue
		residue = cint(h.eggs_set) - cint(h.chicks_hatched)
		if residue <= 0:
			continue
		# A normal spread: mostly infertile, then early dead, a tail of late dead.
		# Normalise first - independent ranges can sum past 100% and then the
		# classification exceeds the eggs actually broken out.
		w = {
			"infertile": random.uniform(42, 52),
			"early": random.uniform(16, 23),
			"mid": random.uniform(6, 10),
			"late": random.uniform(12, 18),
			"pipped": random.uniform(4, 8),
			"contam": random.uniform(0.8, 2.0),
			"malpos": random.uniform(2, 6),
		}
		total_w = sum(w.values())
		share = {k: v / total_w for k, v in w.items()}
		infertile = int(residue * share["infertile"])
		early = int(residue * share["early"])
		mid = int(residue * share["mid"])
		late = int(residue * share["late"])
		pipped = int(residue * share["pipped"])
		contam = int(residue * share["contam"])
		malpos = max(0, residue - (infertile + early + mid + late + pipped + contam))

		doc = frappe.get_doc({
			"doctype": "Breakout Analysis",
			"egg_setting": h.egg_setting,
			"posting_date": h.posting_date,
			"eggs_broken": residue,
			"infertile": infertile,
			"early_dead": early,
			"mid_dead": mid,
			"late_dead": late,
			"pipped_not_hatched": pipped,
			"contaminated": contam,
			"malpositioned": malpos,
			"remarks": "Residue broken out and classified after take-off",
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		made += 1
	frappe.db.commit()
	print(f"  + breakout analyses: {made}")


def run():
	make_masters()
	make_receipts()
	link_settings()
	make_breakouts()
	print("--- summary ---")
	for r in frappe.get_all("Hatching Egg Receipt", filters={"docstatus": 1},
	                        fields=["name", "chick_type", "eggs_received", "settable_pct",
	                                "eggs_in_store", "storage_days"],
	                        order_by="posting_date desc", limit=5):
		print(f"    {r.name} {r.chick_type}: {r.eggs_received} in, "
		      f"{flt(r.settable_pct, 1)}% settable, {r.eggs_in_store} in store "
		      f"({r.storage_days}d)")
	for b in frappe.get_all("Breakout Analysis", filters={"docstatus": 1},
	                        fields=["name", "infertile_pct", "late_dead_pct", "likely_cause"],
	                        limit=5):
		print(f"    {b.name}: infertile {flt(b.infertile_pct, 1)}%, "
		      f"late dead {flt(b.late_dead_pct, 1)}% -> {b.likely_cause}")
	print("HATCHERY DEMO 2 DONE")
