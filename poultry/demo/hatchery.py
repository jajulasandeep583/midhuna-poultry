"""Hatchery demo data: machines, settings at every stage, candling, hatch,
dispatch. Numbers sit in the range a real hatchery reports."""

import random

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

COMPANY = "Midhuna Poultry"
ABBR = "MP"
TODAY = getdate(nowdate())

random.seed(20260804)


def wh(n):
	return f"{n} - {ABBR}"


def _insert(doc):
	d = frappe.get_doc(doc)
	d.flags.ignore_permissions = True
	d.flags.ignore_mandatory = True
	d.insert()
	return d


MACHINES = [
	("Setter S-1", "Setter", 57600, 96, "Multi Stage"),
	("Setter S-2", "Setter", 57600, 96, "Multi Stage"),
	("Hatcher H-1", "Hatcher", 19200, 32, "Single Stage"),
	("Hatcher H-2", "Hatcher", 19200, 32, "Single Stage"),
]


def make_base():
	if not frappe.db.exists("Warehouse", wh("Hatchery Chick Hold")):
		_insert({"doctype": "Warehouse", "warehouse_name": "Hatchery Chick Hold",
		         "company": COMPANY, "parent_warehouse": wh("All Warehouses"), "is_group": 0})

	for code, name, rate in [("EGG-HAT", "Hatching Egg", 8.50),
	                         ("CHICK-DOC", "Day Old Chick - Broiler", 30.0)]:
		if frappe.db.exists("Item", code):
			continue
		_insert({"doctype": "Item", "item_code": code, "item_name": name,
		         "item_group": "Poultry", "stock_uom": "Nos", "is_stock_item": 1,
		         "valuation_rate": rate, "is_purchase_item": 1, "is_sales_item": 1,
		         "item_defaults": [{"company": COMPANY,
		                            "default_warehouse": wh("Hatchery Chick Hold")}]})

	if not frappe.db.exists("Farm", "Midhuna Hatchery"):
		cc = frappe.db.get_value("Cost Center", {"company": COMPANY, "is_group": 0}, "name")
		_insert({"doctype": "Farm", "farm_name": "Midhuna Hatchery", "farm_type": "Hatchery",
		         "company": COMPANY, "bird_capacity": 0, "village": "Siddipet",
		         "district": "Siddipet", "state": "Telangana",
		         "contact_person": "G. Naresh", "mobile_no": "9848045678",
		         "biosecurity_zone": "Zone H", "cost_center": cc})

	for name, mtype, cap, trays, stage in MACHINES:
		if frappe.db.exists("Hatchery Machine", name):
			continue
		_insert({"doctype": "Hatchery Machine", "machine_name": name, "machine_type": mtype,
		         "capacity_eggs": cap, "trays": trays, "stage_type": stage, "company": COMPANY})
	print("  + hatchery machines, items, warehouse, farm")


# (days ago set, eggs, stage) - stage: hatched / candled / set
SETTINGS = [
	(29, 52800, "hatched"),
	(26, 48000, "hatched"),
	(23, 51600, "hatched"),
	(20, 49200, "candled"),
	(19, 45600, "candled"),
	(4, 50400, "set"),
	(1, 47400, "set"),
]


def make_settings():
	layer_flocks = frappe.get_all("Flock", filters={"flock_type": "Layer"}, pluck="name")
	made = 0
	for i, (ago, eggs, stage) in enumerate(SETTINGS):
		set_date = add_days(TODAY, -ago)
		if frappe.db.exists("Egg Setting", {"set_date": set_date, "eggs_set": eggs}):
			continue
		flock = layer_flocks[i % len(layer_flocks)] if layer_flocks else None
		doc = frappe.get_doc({
			"doctype": "Egg Setting",
			"set_date": set_date,
			"source_flock": flock,
			"setter": MACHINES[i % 2][0],
			"company": COMPANY,
			"egg_item": "EGG-HAT",
			"eggs_set": eggs,
			"egg_age_days": random.randint(2, 6),
			"storage_temp_c": round(random.uniform(17.5, 19.5), 1),
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		made += 1

		if stage in ("candled", "hatched"):
			fert = random.uniform(0.88, 0.935)
			clear = int(eggs * (1 - fert) * 0.72)
			dead = int(eggs * (1 - fert) * 0.20)
			cont = int(eggs * (1 - fert)) - clear - dead
			c = frappe.get_doc({
				"doctype": "Candling Entry", "egg_setting": doc.name,
				"posting_date": add_days(set_date, 18),
				"clear_eggs": clear, "dead_germ": dead, "contaminated": max(0, cont),
				"remarks": "Routine candling at day 18",
			})
			c.flags.ignore_permissions = True
			c.insert()
			c.submit()

		if stage == "hatched":
			doc.reload()
			fertile = cint(doc.fertile_eggs)
			hatched = int(fertile * random.uniform(0.90, 0.945))
			cripples = int(hatched * random.uniform(0.015, 0.032))
			h = frappe.get_doc({
				"doctype": "Hatch Entry", "egg_setting": doc.name,
				"posting_date": add_days(set_date, 21),
				"hatcher": MACHINES[2 + (i % 2)][0],
				"chicks_hatched": hatched, "cripples": cripples,
				"avg_chick_weight_g": round(random.uniform(38, 44), 1),
				"chick_item": "CHICK-DOC", "warehouse": wh("Hatchery Chick Hold"),
			})
			h.flags.ignore_permissions = True
			h.insert()
			h.submit()

			h.reload()
			saleable = cint(h.saleable_chicks)
			boxes = int(saleable / 100)
			d = frappe.get_doc({
				"doctype": "Chick Dispatch", "hatch_entry": h.name,
				"posting_date": add_days(set_date, 21),
				"destination_type": "Own Farm" if i % 2 == 0 else "Customer",
				"to_farm": "Ramgundam Broiler Farm" if i % 2 == 0 else None,
				"customer": None if i % 2 == 0 else "Balaji Chicken Centre",
				"boxes": boxes, "chicks_per_box": 100,
				"extras": saleable - boxes * 100,
				"transit_temp_c": round(random.uniform(24, 28), 1),
				"in_ovo_vaccinated": 1,
				"vehicle_no": f"TS{random.randint(10, 39)}AB{random.randint(1000, 9999)}",
			})
			d.flags.ignore_permissions = True
			d.insert()
			d.submit()

	frappe.db.commit()
	print(f"  + egg settings: {made}")


def run():
	make_base()
	make_settings()
	rows = frappe.get_all("Egg Setting", fields=["name", "eggs_set", "fertility_pct",
	                                             "hatchability_set_pct", "status"],
	                      order_by="set_date")
	for r in rows:
		print(f"    {r.name} {r.eggs_set} eggs, fertility {flt(r.fertility_pct, 1)}%, "
		      f"hatch of set {flt(r.hatchability_set_pct, 1)}%, {r.status}")
	print("HATCHERY DEMO DONE")
