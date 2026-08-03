"""Number cards, charts and workspaces for the Poultry module.

Seven workspaces, one per job to be done, each with its own icon: overview,
management, flock operations, health, hatchery, setup, analytics. Four
workspaces carrying everything between them was the confusing arrangement this
replaced.
"""

import json

import frappe

MODULE = "Poultry Management"
ACTIVE = ["Placed", "Growing", "Laying", "Depleting"]


def jf(rows):
	return json.dumps(rows)


# ------------------------------------------------------------------ cards
NUMBER_CARDS = [
	{"label": "Birds on Hand", "document_type": "Flock", "function": "Sum",
	 "aggregate_function_based_on": "current_qty", "color": "#29CD42",
	 "filters_json": jf([["Flock", "status", "in", ACTIVE]])},
	{"label": "Flocks in Production", "document_type": "Flock", "function": "Count",
	 "color": "#449CF0", "filters_json": jf([["Flock", "status", "in", ACTIVE]])},
	{"label": "Sheds Occupied", "document_type": "Shed", "function": "Count",
	 "color": "#7575FF", "filters_json": jf([["Shed", "status", "=", "Occupied"]])},
	{"label": "Eggs Collected Today", "document_type": "Daily Flock Entry", "function": "Sum",
	 "aggregate_function_based_on": "total_eggs", "color": "#ECAD4B",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
	                     ["Daily Flock Entry", "posting_date", "Timespan", "today"]])},
	{"label": "Feed Used (30 Days) kg", "document_type": "Daily Flock Entry", "function": "Sum",
	 "aggregate_function_based_on": "total_feed_kg", "color": "#761ACB",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
	                     ["Daily Flock Entry", "posting_date", "Timespan", "last month"]])},
	{"label": "Birds Lost (30 Days)", "document_type": "Daily Flock Entry", "function": "Sum",
	 "aggregate_function_based_on": "mortality_qty", "color": "#CB2929",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
	                     ["Daily Flock Entry", "posting_date", "Timespan", "last month"]])},
	{"label": "Overdue Vaccinations", "document_type": "Flock Vaccination Plan",
	 "function": "Sum", "aggregate_function_based_on": "overdue_count", "color": "#CB2929",
	 "filters_json": jf([])},
	{"label": "Open Alerts (7 Days)", "document_type": "Daily Flock Entry", "function": "Count",
	 "color": "#ECAD4B",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
	                     ["Daily Flock Entry", "has_alert", "=", 1],
	                     ["Daily Flock Entry", "posting_date", "Timespan", "last week"]])},
	{"label": "Eggs Set (30 Days)", "document_type": "Egg Setting", "function": "Sum",
	 "aggregate_function_based_on": "eggs_set", "color": "#E8A33D",
	 "filters_json": jf([["Egg Setting", "docstatus", "=", 1],
	                     ["Egg Setting", "set_date", "Timespan", "last month"]])},
	{"label": "Chicks Hatched (30 Days)", "document_type": "Hatch Entry", "function": "Sum",
	 "aggregate_function_based_on": "chicks_hatched", "color": "#17B897",
	 "filters_json": jf([["Hatch Entry", "docstatus", "=", 1],
	                     ["Hatch Entry", "posting_date", "Timespan", "last month"]])},
]

CHARTS = [
	{"chart_name": "Daily Mortality Trend", "chart_type": "Sum",
	 "document_type": "Daily Flock Entry", "based_on": "posting_date",
	 "value_based_on": "mortality_qty", "type": "Line", "timespan": "Last Month",
	 "time_interval": "Daily", "color": "#CB2929",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]])},
	{"chart_name": "Daily Egg Collection", "chart_type": "Sum",
	 "document_type": "Daily Flock Entry", "based_on": "posting_date",
	 "value_based_on": "total_eggs", "type": "Bar", "timespan": "Last Month",
	 "time_interval": "Daily", "color": "#ECAD4B",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]])},
	{"chart_name": "Daily Feed Consumption (kg)", "chart_type": "Sum",
	 "document_type": "Daily Flock Entry", "based_on": "posting_date",
	 "value_based_on": "total_feed_kg", "type": "Line", "timespan": "Last Month",
	 "time_interval": "Daily", "color": "#449CF0",
	 "filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]])},
	{"chart_name": "Flocks by Status", "chart_type": "Group By",
	 "document_type": "Flock", "group_by_type": "Count", "group_by_based_on": "status",
	 "type": "Donut", "color": "#7575FF", "filters_json": jf([])},
	{"chart_name": "Eggs Set per Week", "chart_type": "Sum", "document_type": "Egg Setting",
	 "based_on": "set_date", "value_based_on": "eggs_set", "type": "Bar",
	 "timespan": "Last Quarter", "time_interval": "Weekly", "color": "#E8A33D",
	 "filters_json": jf([["Egg Setting", "docstatus", "=", 1]])},
]


def make_cards():
	for c in NUMBER_CARDS:
		if not frappe.db.exists("DocType", c["document_type"]):
			continue
		if frappe.db.exists("Number Card", c["label"]):
			doc = frappe.get_doc("Number Card", c["label"])
		else:
			doc = frappe.new_doc("Number Card")
			doc.name = c["label"]
		doc.update(c)
		doc.type = "Document Type"
		doc.is_public = 1
		doc.show_percentage_change = 0
		doc.module = MODULE
		# Number Card defaults currency to the company currency, which renders
		# "1.13 L birds" as a rupee amount.
		doc.currency = None
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.set_value("Number Card", doc.name, "currency", None, update_modified=False)
	print("  + number cards:", len(NUMBER_CARDS))


def make_charts():
	for c in CHARTS:
		if not frappe.db.exists("DocType", c["document_type"]):
			continue
		if frappe.db.exists("Dashboard Chart", c["chart_name"]):
			doc = frappe.get_doc("Dashboard Chart", c["chart_name"])
		else:
			doc = frappe.new_doc("Dashboard Chart")
			doc.name = c["chart_name"]
		doc.update(c)
		doc.is_public = 1
		doc.module = MODULE
		doc.flags.ignore_permissions = True
		doc.save()
	print("  + charts:", len(CHARTS))


# ------------------------------------------------------------------ helpers
def link(label, type_, to, description=""):
	return {"type": "Link", "label": label, "link_type": type_, "link_to": to,
	        "dependencies": "", "onboard": 0,
	        "is_query_report": 1 if type_ == "Report" else 0, "description": description}


def card_break(label):
	return {"type": "Card Break", "label": label, "hidden": 0}


def shortcut(label, to, type_="DocType", color="Grey", filters=None):
	s = {"type": type_, "label": label, "link_to": to, "color": color, "doc_view": ""}
	if filters:
		s["stats_filter"] = json.dumps(filters)
	return s


def content(blocks):
	return json.dumps([{"id": f"pltry{i:03d}", "type": k, "data": d}
	                   for i, (k, d) in enumerate(blocks)])


def cards_from(links):
	return [("card", {"card_name": c["label"], "col": 4})
	        for c in links if c["type"] == "Card Break"]


def present(links):
	"""Drop links whose target does not exist yet - the home workspace points at
	child workspaces that are created after it."""
	out = []
	for l in links:
		if l["type"] == "Card Break":
			out.append(l)
			continue
		dt = {"Report": "Report", "Page": "Page", "DocType": "DocType",
		      "Workspace": "Workspace"}.get(l["link_type"])
		if dt and frappe.db.exists(dt, l["link_to"]):
			out.append(l)
	# a card with nothing under it renders as an empty box
	cleaned, i = [], 0
	while i < len(out):
		if out[i]["type"] == "Card Break" and (
				i + 1 >= len(out) or out[i + 1]["type"] == "Card Break"):
			i += 1
			continue
		cleaned.append(out[i])
		i += 1
	return cleaned


def upsert(name, doc):
	if frappe.db.exists("Workspace", name):
		w = frappe.get_doc("Workspace", name)
		w.links, w.shortcuts, w.number_cards, w.charts = [], [], [], []
	else:
		w = frappe.new_doc("Workspace")
		w.name = name
	w.update(doc)
	w.flags.ignore_permissions = True
	w.save()
	print("  + workspace:", name)


# ------------------------------------------------------------------ link sets
MANAGEMENT_LINKS = [
	card_break("Daily Screens"),
	link("Management", "Page", "poultry-manage",
	     description="Sales, purchases, stock and every other screen in one place"),
	link("Poultry Control Tower", "Page", "poultry-tower",
	     description="Every flock ranked by what needs attention"),
	link("Daily Entry Board", "Page", "poultry-entry-board",
	     description="Days across, flocks down. Fill the gaps"),
	card_break("Commercial"),
	link("Sales & Purchases", "Page", "poultry-trade",
	     description="Sold and bought today, this week, this month"),
	link("Stock on Hand", "Page", "poultry-stock",
	     description="Birds, eggs and feed by item and location"),
	link("Cost & Profitability", "Page", "poultry-cost-hub",
	     description="Cost per bird and per kilogram, closed-batch margin"),
	card_break("Documents"),
	link("Sales Invoice", "DocType", "Sales Invoice"),
	link("Purchase Receipt", "DocType", "Purchase Receipt"),
	link("Stock Entry", "DocType", "Stock Entry"),
	link("Item", "DocType", "Item"),
	card_break("Help"),
	link("How to Use Poultry", "Page", "poultry-guide",
	     description="The guide, with a button to every screen"),
]

FLOCK_LINKS = [
	card_break("Flock"),
	link("Flock", "DocType", "Flock", description="The spine - everything hangs off it"),
	link("Daily Flock Entry", "DocType", "Daily Flock Entry",
	     description="Mortality and feed. Everything else is derived"),
	link("Bird Weighing", "DocType", "Bird Weighing"),
	link("Flock Closure", "DocType", "Flock Closure"),
	card_break("Screens"),
	link("Flock 360", "Page", "poultry-flock-360",
	     description="One flock, end to end, against its standard"),
	link("Daily Entry Board", "Page", "poultry-entry-board"),
	link("Poultry Control Tower", "Page", "poultry-tower"),
	card_break("Housing"),
	link("Shed", "DocType", "Shed", description="One shed, one warehouse, one flock"),
	link("Farm", "DocType", "Farm"),
	card_break("Flock Reports"),
	link("Flock Performance vs Standard", "Report", "Flock Performance vs Standard"),
	link("Broiler Batch Summary", "Report", "Broiler Batch Summary"),
	link("Layer Production Curve", "Report", "Layer Production Curve"),
	link("Shed Utilisation and Downtime", "Report", "Shed Utilisation and Downtime"),
]

HEALTH_LINKS = [
	card_break("Screens"),
	link("Vaccination & Health", "Page", "poultry-health-hub",
	     description="Doses due, overdue, and which flocks cannot be sold"),
	card_break("Vaccination"),
	link("Flock Vaccination Plan", "DocType", "Flock Vaccination Plan",
	     description="Generated at placement with real due dates"),
	link("Vaccination Entry", "DocType", "Vaccination Entry",
	     description="Actual dose given, with vial batch"),
	link("Vaccination Schedule Template", "DocType", "Vaccination Schedule Template"),
	card_break("Medication and Withdrawal"),
	link("Medication Entry", "DocType", "Medication Entry",
	     description="Sets the withdrawal date that blocks sales"),
	link("Poultry Medication", "DocType", "Poultry Medication"),
	link("Vaccine", "DocType", "Vaccine"),
	link("Poultry Disease", "DocType", "Poultry Disease"),
	card_break("Health Reports"),
	link("Vaccination Compliance", "Report", "Vaccination Compliance"),
	link("Withdrawal Period Alert", "Report", "Withdrawal Period Alert"),
	link("Mortality Analysis", "Report", "Mortality Analysis"),
]

HATCHERY_LINKS = [
	card_break("Incubation"),
	link("Egg Setting", "DocType", "Egg Setting",
	     description="Day 0. Records breeder age, which explains hatchability"),
	link("Candling Entry", "DocType", "Candling Entry", description="Day 18. Gives fertility %"),
	link("Hatch Entry", "DocType", "Hatch Entry",
	     description="Day 21. Hatchability of set and of fertile"),
	card_break("Dispatch"),
	link("Chick Dispatch", "DocType", "Chick Dispatch",
	     description="Boxes, transit temperature, in-ovo vaccination"),
	card_break("Machines"),
	link("Hatchery Machine", "DocType", "Hatchery Machine",
	     description="Setters and hatchers, capacity and staging"),
	card_break("Hatchery Reports"),
	link("Hatchery Performance", "Report", "Hatchery Performance"),
]

SETUP_LINKS = [
	card_break("Farm Structure"),
	link("Farm", "DocType", "Farm", description="Sites, capacity and biosecurity zone"),
	link("Shed", "DocType", "Shed", description="One shed, one warehouse, one flock"),
	card_break("Birds"),
	link("Breed", "DocType", "Breed"),
	link("Strain", "DocType", "Strain"),
	link("Breed Standard", "DocType", "Breed Standard",
	     description="Target curve a flock is measured against"),
	card_break("Feed and Eggs"),
	link("Feed Type", "DocType", "Feed Type"),
	link("Egg Grade", "DocType", "Egg Grade"),
	card_break("Health Masters"),
	link("Vaccine", "DocType", "Vaccine"),
	link("Poultry Medication", "DocType", "Poultry Medication"),
	link("Poultry Disease", "DocType", "Poultry Disease"),
	link("Mortality Reason", "DocType", "Mortality Reason"),
	link("Vaccination Schedule Template", "DocType", "Vaccination Schedule Template"),
	card_break("Configuration"),
	link("Poultry Settings", "DocType", "Poultry Settings",
	     description="Modules, tiers, alert thresholds, costing"),
]

ANALYTICS_LINKS = [
	card_break("Flock Performance"),
	link("Flock Performance vs Standard", "Report", "Flock Performance vs Standard"),
	link("Broiler Batch Summary", "Report", "Broiler Batch Summary"),
	link("Layer Production Curve", "Report", "Layer Production Curve"),
	card_break("Feed and Cost"),
	link("Feed Consumption and FCR Trend", "Report", "Feed Consumption and FCR Trend"),
	link("Cost & Profitability", "Page", "poultry-cost-hub"),
	link("Sales & Purchases", "Page", "poultry-trade"),
	card_break("Health and Compliance"),
	link("Mortality Analysis", "Report", "Mortality Analysis"),
	link("Vaccination Compliance", "Report", "Vaccination Compliance"),
	link("Withdrawal Period Alert", "Report", "Withdrawal Period Alert"),
	card_break("Hatchery and Operations"),
	link("Hatchery Performance", "Report", "Hatchery Performance"),
	link("Shed Utilisation and Downtime", "Report", "Shed Utilisation and Downtime"),
	card_break("Standard ERPNext"),
	link("Stock Ledger", "Report", "Stock Ledger"),
	link("Stock Balance", "Report", "Stock Balance"),
	link("Profit and Loss Statement", "Report", "Profit and Loss Statement"),
]

HOME_LINKS = [
	card_break("Start Here"),
	link("Management", "Page", "poultry-manage",
	     description="Sales, purchases, stock and every screen"),
	link("Poultry Control Tower", "Page", "poultry-tower"),
	link("How to Use Poultry", "Page", "poultry-guide"),
	card_break("Every Day"),
	link("Daily Flock Entry", "DocType", "Daily Flock Entry"),
	link("Flock", "DocType", "Flock"),
	link("Shed", "DocType", "Shed"),
	# Workspace Link only accepts DocType, Page or Report - the child
	# workspaces reach the user through the sidebar tree and the navigator
	card_break("Other Areas"),
	link("Vaccination & Health", "Page", "poultry-health-hub"),
	link("Egg Setting", "DocType", "Egg Setting", description="Hatchery"),
	link("Cost & Profitability", "Page", "poultry-cost-hub"),
	link("Broiler Batch Summary", "Report", "Broiler Batch Summary"),
	link("Poultry Settings", "DocType", "Poultry Settings"),
]


def block_row(names, col=3):
	return [("number_card", {"number_card_name": n, "col": col}) for n in names]


def make_workspaces():
	nav = [("custom_block", {"custom_block_name": "Poultry Navigator", "col": 12})]

	def home_doc():
		links = present(HOME_LINKS)
		blocks = nav + [
			("header", {"text": '<span class="h4"><b>Today on the Farms</b></span>', "col": 12}),
		] + block_row(["Birds on Hand", "Flocks in Production", "Sheds Occupied",
		               "Eggs Collected Today", "Feed Used (30 Days) kg", "Birds Lost (30 Days)",
		               "Overdue Vaccinations", "Open Alerts (7 Days)"]) + [
			("spacer", {"col": 12}),
			("chart", {"chart_name": "Daily Mortality Trend", "col": 12}),
			("chart", {"chart_name": "Daily Egg Collection", "col": 12}),
			("chart", {"chart_name": "Daily Feed Consumption (kg)", "col": 12}),
			("header", {"text": '<span class="h4"><b>Go To</b></span>', "col": 12}),
		] + cards_from(links)
		return {
			"label": "Poultry", "title": "Poultry", "module": MODULE, "icon": "poultry-farm",
			"public": 1, "is_hidden": 0, "sequence_id": 15.0, "content": content(blocks),
			"links": links,
			"shortcuts": [
				shortcut("Management", "poultry-manage", "Page", "Grey"),
				shortcut("Control Tower", "poultry-tower", "Page", "Orange"),
				shortcut("Daily Flock Entry", "Daily Flock Entry", color="Blue",
				         filters={"docstatus": 1}),
				shortcut("Flock", "Flock", color="Green", filters={"status": ["in", ACTIVE]}),
			],
			"number_cards": [{"number_card_name": c["label"], "label": c["label"]}
			                 for c in NUMBER_CARDS[:8]],
			"charts": [{"chart_name": c["chart_name"], "label": c["chart_name"]}
			           for c in CHARTS[:3]],
			"custom_blocks": [{"custom_block_name": "Poultry Navigator",
			                   "label": "Poultry Navigator"}],
		}

	# pass 1: home without the child-workspace links, so children have a parent
	upsert("Poultry", home_doc())

	old_home = nav + [
		("header", {"text": '<span class="h4"><b>Today on the Farms</b></span>', "col": 12}),
	] + block_row(["Birds on Hand", "Flocks in Production", "Sheds Occupied",
	               "Eggs Collected Today", "Feed Used (30 Days) kg", "Birds Lost (30 Days)",
	               "Overdue Vaccinations", "Open Alerts (7 Days)"]) + [
		("spacer", {"col": 12}),
		("chart", {"chart_name": "Daily Mortality Trend", "col": 12}),
		("chart", {"chart_name": "Daily Egg Collection", "col": 12}),
		("chart", {"chart_name": "Daily Feed Consumption (kg)", "col": 12}),
		("header", {"text": '<span class="h4"><b>Go To</b></span>', "col": 12}),
	]

	def child(name, icon, seq, links, shortcuts, blocks_extra=None, cards=None, charts=None):
		links = present(links)
		blocks = nav + [("header", {"text": f'<span class="h4"><b>{name}</b></span>',
		                            "col": 12})]
		blocks += blocks_extra or []
		blocks += cards_from(links)
		upsert(name, {
			"label": name, "title": name, "module": MODULE, "icon": icon, "public": 1,
			"parent_page": "Poultry", "sequence_id": seq, "content": content(blocks),
			"links": links, "shortcuts": shortcuts,
			"number_cards": [{"number_card_name": c, "label": c} for c in (cards or [])],
			"charts": [{"chart_name": c, "label": c} for c in (charts or [])],
			"custom_blocks": [{"custom_block_name": "Poultry Navigator",
			                   "label": "Poultry Navigator"}],
		})

	child("Management", "poultry-manage", 15.1, MANAGEMENT_LINKS, [
		shortcut("Management", "poultry-manage", "Page", "Grey"),
		shortcut("Sales & Purchases", "poultry-trade", "Page", "Green"),
		shortcut("Stock on Hand", "poultry-stock", "Page", "Blue"),
		shortcut("Cost & Profitability", "poultry-cost-hub", "Page", "Purple"),
	])

	child("Flock Operations", "poultry-hen", 15.2, FLOCK_LINKS, [
		shortcut("Daily Flock Entry", "Daily Flock Entry", color="Blue",
		         filters={"docstatus": 1}),
		shortcut("Flock", "Flock", color="Green", filters={"status": ["in", ACTIVE]}),
		shortcut("Shed", "Shed", color="Cyan", filters={"status": "Occupied"}),
		shortcut("Flock 360", "poultry-flock-360", "Page", "Purple"),
	], cards=["Birds on Hand", "Flocks in Production", "Sheds Occupied"],
		blocks_extra=block_row(["Birds on Hand", "Flocks in Production", "Sheds Occupied"], 4))

	child("Poultry Health", "poultry-syringe", 15.3, HEALTH_LINKS, [
		shortcut("Vaccination & Health", "poultry-health-hub", "Page", "Green"),
		shortcut("Vaccination Entry", "Vaccination Entry", color="Orange"),
		shortcut("Medication Entry", "Medication Entry", color="Red"),
		shortcut("Withdrawal Period Alert", "Withdrawal Period Alert", "Report", "Red"),
	], cards=["Overdue Vaccinations", "Birds Lost (30 Days)", "Open Alerts (7 Days)"],
		blocks_extra=block_row(["Overdue Vaccinations", "Birds Lost (30 Days)",
		                        "Open Alerts (7 Days)"], 4))

	child("Hatchery", "poultry-hatchery", 15.4, HATCHERY_LINKS, [
		shortcut("Egg Setting", "Egg Setting", color="Yellow"),
		shortcut("Candling Entry", "Candling Entry", color="Blue"),
		shortcut("Hatch Entry", "Hatch Entry", color="Green"),
		shortcut("Chick Dispatch", "Chick Dispatch", color="Orange"),
	], cards=["Eggs Set (30 Days)", "Chicks Hatched (30 Days)"],
		blocks_extra=block_row(["Eggs Set (30 Days)", "Chicks Hatched (30 Days)"], 6) +
		[("chart", {"chart_name": "Eggs Set per Week", "col": 12})],
		charts=["Eggs Set per Week"])

	child("Poultry Setup", "poultry-settings", 15.5, SETUP_LINKS, [
		shortcut("Farm", "Farm", color="Green"),
		shortcut("Shed", "Shed", color="Cyan"),
		shortcut("Breed Standard", "Breed Standard", color="Purple"),
		shortcut("Poultry Settings", "Poultry Settings", color="Grey"),
	])

	child("Poultry Analytics", "poultry-chart", 15.6, ANALYTICS_LINKS, [
		shortcut("Broiler Batch Summary", "Broiler Batch Summary", "Report", "Purple"),
		shortcut("Hatchery Performance", "Hatchery Performance", "Report", "Yellow"),
		shortcut("Mortality Analysis", "Mortality Analysis", "Report", "Red"),
		shortcut("Cost & Profitability", "poultry-cost-hub", "Page", "Green"),
	], blocks_extra=[("chart", {"chart_name": "Flocks by Status", "col": 12})],
		charts=["Flocks by Status"])

	# pass 2: now every child exists, so the home "Areas" card can point at them
	upsert("Poultry", home_doc())


def install():
	make_cards()
	make_charts()
	make_workspaces()
	frappe.db.commit()
	print("WORKSPACES DONE")


run = install
