"""Site-specific demo masters: accounts, warehouses, items, parties, farms, sheds.

The breed standards, vaccines and other reference content ship with the app
(poultry.setup.masters); this only adds what a real installation would own.
"""

import frappe

COMPANY = "Midhuna Poultry"
ABBR = "MP"
ITEM_GROUP = "Poultry"


def wh(name):
	return f"{name} - {ABBR}"


def acc(name):
	return f"{name} - {ABBR}"


def _insert(doc):
	d = frappe.get_doc(doc)
	d.flags.ignore_permissions = True
	d.flags.ignore_mandatory = True
	d.insert()
	return d


BIRD_ITEMS = [("BIRD-BRL", "Broiler Live Bird", 32.0), ("BIRD-LYR", "Layer Bird", 48.0)]

FEED_ITEMS = [
	("FEED-BPS", "Broiler Pre-Starter Crumble", 41.5),
	("FEED-BST", "Broiler Starter Crumble", 38.9),
	("FEED-BFN", "Broiler Finisher Pellet", 36.4),
	("FEED-CHM", "Chick Mash", 39.2),
	("FEED-GRW", "Grower Mash", 33.8),
	("FEED-LP1", "Layer Mash Phase-1", 31.6),
	("FEED-LP2", "Layer Mash Phase-2", 30.4),
]

EGG_ITEMS = [
	("EGG-SML", "Table Egg - Small", 3.90),
	("EGG-MED", "Table Egg - Medium", 4.60),
	("EGG-LRG", "Table Egg - Large", 5.30),
	("EGG-JUM", "Table Egg - Jumbo", 5.90),
	("EGG-CRK", "Crack / Reject Egg", 1.80),
]

# reference master -> the item this installation stocks it as
FEED_TYPE_ITEMS = {
	"Broiler Pre-Starter": "FEED-BPS", "Broiler Starter": "FEED-BST",
	"Broiler Finisher": "FEED-BFN", "Chick Mash": "FEED-CHM", "Grower Mash": "FEED-GRW",
	"Layer Phase-1": "FEED-LP1", "Layer Phase-2": "FEED-LP2",
	"Pullet Chick Mash": "FEED-CHM", "Pullet Grower Mash": "FEED-GRW",
}
EGG_GRADE_ITEMS = {"S": "EGG-SML", "M": "EGG-MED", "L": "EGG-LRG", "XL": "EGG-JUM",
                   "CR": "EGG-CRK"}

SUPPLIERS = ["Venkateshwara Hatcheries", "Suguna Breeding Farms", "Godrej Agrovet Feed",
             "SKM Animal Feeds"]
CUSTOMERS = ["Hyderabad Egg Mandi", "Sri Lakshmi Poultry Traders", "Metro Fresh Retail",
             "Balaji Chicken Centre"]

STRAIN_SUPPLIERS = {
	"Cobb 500": "Venkateshwara Hatcheries", "Ross 308": "Suguna Breeding Farms",
	"Vencobb 430": "Venkateshwara Hatcheries", "Hy-Line W-36": "Venkateshwara Hatcheries",
	"Lohmann Brown": "Suguna Breeding Farms", "BV-300": "Venkateshwara Hatcheries",
}

FARMS = [
	("Ramgundam Broiler Farm", "Broiler", 60000, "Ramgundam", "Peddapalli", "Telangana",
	 "K. Srinivas", "9848012345", "Zone A"),
	("Siddipet Layer Farm", "Layer", 90000, "Siddipet", "Siddipet", "Telangana",
	 "M. Ramesh", "9848023456", "Zone B"),
	("Zaheerabad Rearing Unit", "Rearing", 40000, "Zaheerabad", "Sangareddy", "Telangana",
	 "P. Anjaiah", "9848034567", "Zone C"),
]

SHEDS = [
	("Ramgundam Broiler Farm", "SH-01", 12000, "Environment Controlled", 14000),
	("Ramgundam Broiler Farm", "SH-02", 12000, "Environment Controlled", 14000),
	("Ramgundam Broiler Farm", "SH-03", 10000, "Deep Litter", 12000),
	("Ramgundam Broiler Farm", "SH-04", 10000, "Deep Litter", 12000),
	("Ramgundam Broiler Farm", "SH-05", 8000, "Deep Litter", 9500),
	("Siddipet Layer Farm", "LH-01", 20000, "Cage", 18000),
	("Siddipet Layer Farm", "LH-02", 20000, "Cage", 18000),
	("Siddipet Layer Farm", "LH-03", 18000, "Cage", 16000),
	("Siddipet Layer Farm", "LH-04", 18000, "Cage", 16000),
	("Zaheerabad Rearing Unit", "RH-01", 15000, "Deep Litter", 15000),
	("Zaheerabad Rearing Unit", "RH-02", 15000, "Deep Litter", 15000),
	("Zaheerabad Rearing Unit", "RH-03", 10000, "Slat", 10000),
]


def make_accounts():
	if not frappe.db.exists("Account", acc("Bird Mortality Written Off")):
		_insert({"doctype": "Account", "account_name": "Bird Mortality Written Off",
		         "parent_account": acc("Direct Expenses"), "company": COMPANY,
		         "root_type": "Expense", "account_type": "Expense Account", "is_group": 0})


def make_warehouses():
	for name in ("Egg Cold Store", "Feed Store"):
		if not frappe.db.exists("Warehouse", wh(name)):
			_insert({"doctype": "Warehouse", "warehouse_name": name, "company": COMPANY,
			         "parent_warehouse": wh("All Warehouses"), "is_group": 0})


def make_item(code, name, uom, rate, batch=False):
	if frappe.db.exists("Item", code):
		return
	_insert({
		"doctype": "Item", "item_code": code, "item_name": name, "item_group": ITEM_GROUP,
		"stock_uom": uom, "is_stock_item": 1, "has_batch_no": 1 if batch else 0,
		"valuation_rate": rate, "is_purchase_item": 1, "is_sales_item": 1,
		"item_defaults": [{"company": COMPANY, "default_warehouse": wh("Stores")}],
	})


def make_items():
	if not frappe.db.exists("Item Group", ITEM_GROUP):
		_insert({"doctype": "Item Group", "item_group_name": ITEM_GROUP,
		         "parent_item_group": "All Item Groups", "is_group": 0})
	for code, name, rate in BIRD_ITEMS:
		make_item(code, name, "Nos", rate, batch=True)
	for code, name, rate in FEED_ITEMS:
		make_item(code, name, "Kg", rate)
	for code, name, rate in EGG_ITEMS:
		make_item(code, name, "Nos", rate)


def link_items():
	"""Point the shipped Feed Type and Egg Grade masters at this site's items."""
	for feed_type, item in FEED_TYPE_ITEMS.items():
		if frappe.db.exists("Feed Type", feed_type):
			frappe.db.set_value("Feed Type", feed_type, "item", item, update_modified=False)
	for grade, item in EGG_GRADE_ITEMS.items():
		if frappe.db.exists("Egg Grade", grade):
			frappe.db.set_value("Egg Grade", grade, "item", item, update_modified=False)
	for strain, supplier in STRAIN_SUPPLIERS.items():
		if frappe.db.exists("Strain", strain):
			frappe.db.set_value("Strain", strain, "supplier", supplier, update_modified=False)


def make_parties():
	for name in SUPPLIERS:
		if not frappe.db.exists("Supplier", name):
			_insert({"doctype": "Supplier", "supplier_name": name, "supplier_group": "Local",
			         "supplier_type": "Company"})
	for name in CUSTOMERS:
		if not frappe.db.exists("Customer", name):
			_insert({"doctype": "Customer", "customer_name": name,
			         "customer_group": "Commercial", "territory": "India"})


def make_farms():
	cc = frappe.db.get_value("Cost Center", {"company": COMPANY, "is_group": 0}, "name")
	for name, ftype, cap, village, district, state, person, mobile, zone in FARMS:
		if frappe.db.exists("Farm", name):
			continue
		_insert({"doctype": "Farm", "farm_name": name, "farm_type": ftype, "company": COMPANY,
		         "bird_capacity": cap, "village": village, "district": district, "state": state,
		         "contact_person": person, "mobile_no": mobile, "biosecurity_zone": zone,
		         "cost_center": cc})
	for farm, code, cap, housing, area in SHEDS:
		if frappe.db.exists("Shed", f"{farm}-{code}"):
			continue
		_insert({"doctype": "Shed", "farm": farm, "shed_code": code, "capacity": cap,
		         "housing_system": housing, "floor_area_sqft": area})


def make_settings():
	s = frappe.get_doc("Poultry Settings")
	s.enable_egg_management = 1
	s.data_tier = "Tier 3"
	s.allow_backdated_entry = 1
	s.max_backdate_days = 45
	s.default_bag_weight_kg = 50
	s.eggs_per_tray = 30
	s.mortality_spike_threshold_pct = 0.5
	s.weight_deviation_threshold_pct = 10
	s.cumulative_mortality_factor = 1.5
	s.water_feed_factor = 1.25
	s.costing_method = "Project"
	s.create_stock_entries = 1
	s.auto_create_vaccination_plan = 1
	s.default_company = COMPANY
	s.mortality_expense_account = acc("Bird Mortality Written Off")
	s.egg_warehouse = wh("Egg Cold Store")
	s.flags.ignore_permissions = True
	s.save()


def install():
	from poultry.setup import masters as reference

	reference.install()
	make_accounts()
	make_warehouses()
	make_items()
	make_parties()
	link_items()
	make_farms()
	make_settings()
	frappe.db.commit()
	print("  + demo masters: items, parties, 3 farms, 12 sheds, settings")


# kept so the old entry point still works
run = install
