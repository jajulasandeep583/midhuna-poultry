"""Number cards, charts and workspaces for the Poultry module."""

import json

import frappe

MODULE = "Poultry Management"
ACTIVE = ["Placed", "Growing", "Laying", "Depleting"]


def jf(rows):
	return json.dumps(rows)


# ------------------------------------------------------------------ cards
NUMBER_CARDS = [
	{
		"label": "Birds on Hand", "document_type": "Flock", "function": "Sum",
		"aggregate_function_based_on": "current_qty", "color": "#29CD42",
		"filters_json": jf([["Flock", "status", "in", ACTIVE]]),
	},
	{
		"label": "Flocks in Production", "document_type": "Flock", "function": "Count",
		"color": "#449CF0", "filters_json": jf([["Flock", "status", "in", ACTIVE]]),
	},
	{
		"label": "Sheds Occupied", "document_type": "Shed", "function": "Count",
		"color": "#7575FF", "filters_json": jf([["Shed", "status", "=", "Occupied"]]),
	},
	{
		"label": "Eggs Collected Today", "document_type": "Daily Flock Entry", "function": "Sum",
		"aggregate_function_based_on": "total_eggs", "color": "#ECAD4B",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
		                    ["Daily Flock Entry", "posting_date", "Timespan", "today"]]),
	},
	{
		"label": "Feed Used (30 Days) kg", "document_type": "Daily Flock Entry", "function": "Sum",
		"aggregate_function_based_on": "total_feed_kg", "color": "#761ACB",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
		                    ["Daily Flock Entry", "posting_date", "Timespan", "last month"]]),
	},
	{
		"label": "Birds Lost (30 Days)", "document_type": "Daily Flock Entry", "function": "Sum",
		"aggregate_function_based_on": "mortality_qty", "color": "#CB2929",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
		                    ["Daily Flock Entry", "posting_date", "Timespan", "last month"]]),
	},
	{
		"label": "Overdue Vaccinations", "document_type": "Flock Vaccination Plan",
		"function": "Sum", "aggregate_function_based_on": "overdue_count", "color": "#CB2929",
		"filters_json": jf([]),
	},
	{
		"label": "Open Alerts (7 Days)", "document_type": "Daily Flock Entry", "function": "Count",
		"color": "#ECAD4B",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1],
		                    ["Daily Flock Entry", "has_alert", "=", 1],
		                    ["Daily Flock Entry", "posting_date", "Timespan", "last week"]]),
	},
]

CHARTS = [
	{
		"chart_name": "Daily Mortality Trend", "chart_type": "Sum",
		"document_type": "Daily Flock Entry", "based_on": "posting_date",
		"value_based_on": "mortality_qty", "type": "Line", "timespan": "Last Month",
		"time_interval": "Daily", "color": "#CB2929",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]]),
	},
	{
		"chart_name": "Daily Egg Collection", "chart_type": "Sum",
		"document_type": "Daily Flock Entry", "based_on": "posting_date",
		"value_based_on": "total_eggs", "type": "Bar", "timespan": "Last Month",
		"time_interval": "Daily", "color": "#ECAD4B",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]]),
	},
	{
		"chart_name": "Daily Feed Consumption (kg)", "chart_type": "Sum",
		"document_type": "Daily Flock Entry", "based_on": "posting_date",
		"value_based_on": "total_feed_kg", "type": "Line", "timespan": "Last Month",
		"time_interval": "Daily", "color": "#449CF0",
		"filters_json": jf([["Daily Flock Entry", "docstatus", "=", 1]]),
	},
	{
		"chart_name": "Flocks by Status", "chart_type": "Group By",
		"document_type": "Flock", "group_by_type": "Count", "group_by_based_on": "status",
		"type": "Donut", "color": "#7575FF", "filters_json": jf([]),
	},
]


def make_cards():
	for c in NUMBER_CARDS:
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
		# These count birds, eggs and kilograms. Number Card defaults currency to
		# the company currency, which renders "1.13 L birds" as a rupee amount.
		doc.currency = None
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.set_value("Number Card", doc.name, "currency", None, update_modified=False)
	print("  + number cards:", len(NUMBER_CARDS))


def make_charts():
	for c in CHARTS:
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


# ------------------------------------------------------------------ workspaces
def link(label, type_, to, dependencies="", onboard=0, description=""):
	return {
		"type": "Link", "label": label, "link_type": type_, "link_to": to,
		"dependencies": dependencies, "onboard": onboard, "is_query_report":
			1 if type_ == "Report" else 0, "description": description,
	}


def card_break(label, hidden=0):
	return {"type": "Card Break", "label": label, "hidden": hidden}


def shortcut(label, to, type_="DocType", color="Grey", filters=None, doc_view=""):
	s = {"type": type_, "label": label, "link_to": to, "color": color, "doc_view": doc_view}
	if filters:
		s["stats_filter"] = json.dumps(filters)
	return s


def content(blocks):
	out = []
	for i, (kind, data) in enumerate(blocks):
		out.append({"id": f"pltry{i:03d}", "type": kind, "data": data})
	return json.dumps(out)


def upsert(name, doc):
	if frappe.db.exists("Workspace", name):
		w = frappe.get_doc("Workspace", name)
		w.links = []
		w.shortcuts = []
		w.number_cards = []
		w.charts = []
	else:
		w = frappe.new_doc("Workspace")
		w.name = name
	w.update(doc)
	w.flags.ignore_permissions = True
	w.save()
	print("  + workspace:", name)


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

HEALTH_LINKS = [
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
	card_break("Health Reports"),
	link("Vaccination Compliance", "Report", "Vaccination Compliance"),
	link("Withdrawal Period Alert", "Report", "Withdrawal Period Alert"),
	link("Mortality Analysis", "Report", "Mortality Analysis"),
]

ANALYTICS_LINKS = [
	card_break("Flock Performance"),
	link("Flock Performance vs Standard", "Report", "Flock Performance vs Standard"),
	link("Broiler Batch Summary", "Report", "Broiler Batch Summary"),
	link("Layer Production Curve", "Report", "Layer Production Curve"),
	card_break("Feed and Cost"),
	link("Feed Consumption and FCR Trend", "Report", "Feed Consumption and FCR Trend"),
	card_break("Health and Compliance"),
	link("Mortality Analysis", "Report", "Mortality Analysis"),
	link("Vaccination Compliance", "Report", "Vaccination Compliance"),
	link("Withdrawal Period Alert", "Report", "Withdrawal Period Alert"),
	card_break("Operations"),
	link("Shed Utilisation and Downtime", "Report", "Shed Utilisation and Downtime"),
	card_break("Standard ERPNext"),
	link("Stock Ledger", "Report", "Stock Ledger"),
	link("Stock Balance", "Report", "Stock Balance"),
	link("Profit and Loss Statement", "Report", "Profit and Loss Statement"),
]

MAIN_LINKS = [
	card_break("Dashboards"),
	link("Poultry Control Tower", "Page", "poultry-tower",
	     description="Live board: every flock, ranked by what needs attention"),
	link("Flock 360", "Page", "poultry-flock-360",
	     description="One flock, end to end, against its standard"),
	link("Daily Entry Board", "Page", "poultry-entry-board",
	     description="Days across, flocks down - fill the gaps after a farm visit"),
	link("How to Use Poultry", "Page", "poultry-guide",
	     description="The in-app guide, with a button to every screen"),
	card_break("Flock"),
	link("Flock", "DocType", "Flock", description="The spine - everything hangs off it"),
	link("Daily Flock Entry", "DocType", "Daily Flock Entry",
	     description="Mortality and feed. Everything else is derived"),
	link("Bird Weighing", "DocType", "Bird Weighing"),
	link("Flock Closure", "DocType", "Flock Closure"),
	card_break("Health"),
	link("Vaccination Entry", "DocType", "Vaccination Entry"),
	link("Flock Vaccination Plan", "DocType", "Flock Vaccination Plan"),
	link("Medication Entry", "DocType", "Medication Entry"),
	card_break("Farm Setup"),
	link("Farm", "DocType", "Farm"),
	link("Shed", "DocType", "Shed"),
	link("Breed Standard", "DocType", "Breed Standard"),
	link("Poultry Settings", "DocType", "Poultry Settings"),
	card_break("Key Reports"),
	link("Broiler Batch Summary", "Report", "Broiler Batch Summary"),
	link("Flock Performance vs Standard", "Report", "Flock Performance vs Standard"),
	link("Layer Production Curve", "Report", "Layer Production Curve"),
	link("Withdrawal Period Alert", "Report", "Withdrawal Period Alert"),
	card_break("Stock and Accounts"),
	link("Stock Entry", "DocType", "Stock Entry"),
	link("Purchase Receipt", "DocType", "Purchase Receipt"),
	link("Sales Invoice", "DocType", "Sales Invoice"),
	link("Item", "DocType", "Item"),
]

MAIN_SHORTCUTS = [
	shortcut("Poultry Control Tower", "poultry-tower", type_="Page", color="Green"),
	shortcut("Flock 360", "poultry-flock-360", type_="Page", color="Blue"),
	shortcut("Daily Entry Board", "poultry-entry-board", type_="Page", color="Cyan"),
	shortcut("How to Use Poultry", "poultry-guide", type_="Page", color="Yellow"),
	shortcut("Daily Flock Entry", "Daily Flock Entry", color="Blue",
	         filters={"docstatus": 1}),
	shortcut("Flock", "Flock", color="Green", filters={"status": ["in", ACTIVE]}),
	shortcut("Shed", "Shed", color="Cyan", filters={"status": "Occupied"}),
	shortcut("Vaccination Entry", "Vaccination Entry", color="Orange"),
	shortcut("Medication Entry", "Medication Entry", color="Red"),
	shortcut("Broiler Batch Summary", "Broiler Batch Summary", type_="Report", color="Purple"),
	shortcut("Withdrawal Period Alert", "Withdrawal Period Alert", type_="Report", color="Red"),
	shortcut("Poultry Settings", "Poultry Settings", color="Grey"),
]


def make_workspaces():
	main_blocks = [
		("header", {"text": "<span class=\"h4\"><b>Today on the Farms</b></span>", "col": 12}),
		("number_card", {"number_card_name": "Birds on Hand", "col": 3}),
		("number_card", {"number_card_name": "Flocks in Production", "col": 3}),
		("number_card", {"number_card_name": "Sheds Occupied", "col": 3}),
		("number_card", {"number_card_name": "Eggs Collected Today", "col": 3}),
		("number_card", {"number_card_name": "Feed Used (30 Days) kg", "col": 3}),
		("number_card", {"number_card_name": "Birds Lost (30 Days)", "col": 3}),
		("number_card", {"number_card_name": "Overdue Vaccinations", "col": 3}),
		("number_card", {"number_card_name": "Open Alerts (7 Days)", "col": 3}),
		("spacer", {"col": 12}),
		("chart", {"chart_name": "Daily Mortality Trend", "col": 12}),
		("chart", {"chart_name": "Daily Egg Collection", "col": 12}),
		("chart", {"chart_name": "Daily Feed Consumption (kg)", "col": 12}),
		("header", {"text": "<span class=\"h4\"><b>Shortcuts</b></span>", "col": 12}),
	]
	for s in MAIN_SHORTCUTS:
		main_blocks.append(("shortcut", {"shortcut_name": s["label"], "col": 3}))
	main_blocks.append(
		("header", {"text": "<span class=\"h4\"><b>Masters and Reports</b></span>", "col": 12}))
	for c in MAIN_LINKS:
		if c["type"] == "Card Break":
			main_blocks.append(("card", {"card_name": c["label"], "col": 4}))

	upsert("Poultry", {
		"label": "Poultry", "title": "Poultry", "module": MODULE, "icon": "organization",
		"public": 1, "is_hidden": 0, "sequence_id": 15.0,
		"content": content(main_blocks),
		"links": MAIN_LINKS, "shortcuts": MAIN_SHORTCUTS,
		"number_cards": [{"number_card_name": c["label"], "label": c["label"]}
		                 for c in NUMBER_CARDS],
		"charts": [{"chart_name": c["chart_name"], "label": c["chart_name"]} for c in CHARTS],
	})

	setup_blocks = [("header", {"text": "<span class=\"h4\"><b>Poultry Setup</b></span>",
	                            "col": 12})]
	for c in SETUP_LINKS:
		if c["type"] == "Card Break":
			setup_blocks.append(("card", {"card_name": c["label"], "col": 4}))
	upsert("Poultry Setup", {
		"label": "Poultry Setup", "title": "Poultry Setup", "module": MODULE, "icon": "setting",
		"public": 1, "parent_page": "Poultry", "sequence_id": 15.1,
		"content": content(setup_blocks), "links": SETUP_LINKS,
		"shortcuts": [
			shortcut("Farm", "Farm", color="Green"),
			shortcut("Shed", "Shed", color="Cyan"),
			shortcut("Breed Standard", "Breed Standard", color="Purple"),
			shortcut("Poultry Settings", "Poultry Settings", color="Grey"),
		],
	})

	health_blocks = [("header", {"text": "<span class=\"h4\"><b>Health and Biosecurity</b></span>",
	                             "col": 12}),
	                 ("number_card", {"number_card_name": "Overdue Vaccinations", "col": 4}),
	                 ("number_card", {"number_card_name": "Birds Lost (30 Days)", "col": 4}),
	                 ("number_card", {"number_card_name": "Open Alerts (7 Days)", "col": 4}),
	                 ("spacer", {"col": 12})]
	for c in HEALTH_LINKS:
		if c["type"] == "Card Break":
			health_blocks.append(("card", {"card_name": c["label"], "col": 4}))
	upsert("Poultry Health", {
		"label": "Poultry Health", "title": "Poultry Health", "module": MODULE, "icon": "quality",
		"public": 1, "parent_page": "Poultry", "sequence_id": 15.2,
		"content": content(health_blocks), "links": HEALTH_LINKS,
		"shortcuts": [
			shortcut("Vaccination Entry", "Vaccination Entry", color="Orange"),
			shortcut("Medication Entry", "Medication Entry", color="Red"),
			shortcut("Withdrawal Period Alert", "Withdrawal Period Alert", type_="Report",
			         color="Red"),
			shortcut("Vaccination Compliance", "Vaccination Compliance", type_="Report",
			         color="Blue"),
		],
		"number_cards": [{"number_card_name": n, "label": n} for n in
		                 ("Overdue Vaccinations", "Birds Lost (30 Days)", "Open Alerts (7 Days)")],
	})

	analytics_blocks = [("header", {"text": "<span class=\"h4\"><b>Poultry Analytics</b></span>",
	                                "col": 12}),
	                    ("chart", {"chart_name": "Flocks by Status", "col": 12}),
	                    ("spacer", {"col": 12})]
	for c in ANALYTICS_LINKS:
		if c["type"] == "Card Break":
			analytics_blocks.append(("card", {"card_name": c["label"], "col": 4}))
	upsert("Poultry Analytics", {
		"label": "Poultry Analytics", "title": "Poultry Analytics", "module": MODULE,
		"icon": "table", "public": 1, "parent_page": "Poultry", "sequence_id": 15.3,
		"content": content(analytics_blocks), "links": ANALYTICS_LINKS,
		"charts": [{"chart_name": "Flocks by Status", "label": "Flocks by Status"}],
		"shortcuts": [
			shortcut("Broiler Batch Summary", "Broiler Batch Summary", type_="Report",
			         color="Purple"),
			shortcut("Flock Performance vs Standard", "Flock Performance vs Standard",
			         type_="Report", color="Blue"),
			shortcut("Layer Production Curve", "Layer Production Curve", type_="Report",
			         color="Orange"),
			shortcut("Mortality Analysis", "Mortality Analysis", type_="Report", color="Red"),
		],
	})


def run():
	make_cards()
	make_charts()
	make_workspaces()
	frappe.db.commit()
	print("WORKSPACES DONE")


# alias used by poultry.setup.after_install
install = run
