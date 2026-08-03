"""Build the Poultry app sidebars explicitly.

Frappe's auto-generator creates a Workspace Sidebar once and never revisits it,
so pages added later never appear. This owns the order and the icons instead.
One sidebar per workspace, each scoped to that job - a single list carrying
every screen was the confusing arrangement this replaced.
"""

import frappe

SIDEBARS = {
	"Poultry": {
		"icon": "poultry-farm",
		"items": [
			("Home", "Workspace", "Poultry", "poultry-farm"),
			("Management", "Workspace", "Management", "poultry-manage"),
			("Flock Operations", "Workspace", "Flock Operations", "poultry-hen"),
			("Health", "Workspace", "Poultry Health", "poultry-syringe"),
			("Hatchery", "Workspace", "Hatchery", "poultry-hatchery"),
			("Analytics", "Workspace", "Poultry Analytics", "poultry-chart"),
			("Setup", "Workspace", "Poultry Setup", "poultry-settings"),
			("How to Use Poultry", "Page", "poultry-guide", "poultry-guide"),
		],
	},
	"Management": {
		"icon": "poultry-manage",
		"items": [
			("Home", "Workspace", "Management", "poultry-manage"),
			("Management", "Page", "poultry-manage", "poultry-manage"),
			("Control Tower", "Page", "poultry-tower", "poultry-alert"),
			("Sales & Purchases", "Page", "poultry-trade", "poultry-sales"),
			("Stock on Hand", "Page", "poultry-stock", "poultry-stock"),
			("Cost & Profitability", "Page", "poultry-cost-hub", "poultry-cost"),
			("Daily Entry Board", "Page", "poultry-entry-board", "poultry-board"),
			("Sales Invoice", "DocType", "Sales Invoice", "poultry-sales"),
			("Purchase Receipt", "DocType", "Purchase Receipt", "poultry-purchase"),
			("Stock Entry", "DocType", "Stock Entry", "poultry-stock"),
			("How to Use Poultry", "Page", "poultry-guide", "poultry-guide"),
		],
	},
	"Flock Operations": {
		"icon": "poultry-hen",
		"items": [
			("Home", "Workspace", "Flock Operations", "poultry-hen"),
			("Flock 360", "Page", "poultry-flock-360", "poultry-target"),
			("Daily Entry Board", "Page", "poultry-entry-board", "poultry-board"),
			("Daily Flock Entry", "DocType", "Daily Flock Entry", "poultry-clipboard"),
			("Flock", "DocType", "Flock", "poultry-hen"),
			("Bird Weighing", "DocType", "Bird Weighing", "poultry-scale"),
			("Flock Closure", "DocType", "Flock Closure", "poultry-closure"),
			("Shed", "DocType", "Shed", "poultry-shed"),
			("Farm", "DocType", "Farm", "poultry-farm"),
			("Broiler Batch Summary", "Report", "Broiler Batch Summary", "poultry-broiler"),
			("Layer Production Curve", "Report", "Layer Production Curve", "poultry-layer"),
		],
	},
	"Poultry Health": {
		"icon": "poultry-syringe",
		"items": [
			("Home", "Workspace", "Poultry Health", "poultry-syringe"),
			("Vaccination & Health", "Page", "poultry-health-hub", "poultry-syringe"),
			("Flock Vaccination Plan", "DocType", "Flock Vaccination Plan", "poultry-schedule"),
			("Vaccination Entry", "DocType", "Vaccination Entry", "poultry-syringe"),
			("Medication Entry", "DocType", "Medication Entry", "poultry-pill"),
			("Vaccine", "DocType", "Vaccine", "poultry-syringe"),
			("Poultry Medication", "DocType", "Poultry Medication", "poultry-pill"),
			("Poultry Disease", "DocType", "Poultry Disease", "poultry-virus"),
			("Vaccination Compliance", "Report", "Vaccination Compliance", "poultry-schedule"),
			("Withdrawal Period Alert", "Report", "Withdrawal Period Alert", "poultry-withdrawal"),
		],
	},
	"Hatchery": {
		"icon": "poultry-hatchery",
		"items": [
			("Home", "Workspace", "Hatchery", "poultry-hatchery"),
			("Egg Setting", "DocType", "Egg Setting", "poultry-egg"),
			("Candling Entry", "DocType", "Candling Entry", "poultry-search"),
			("Hatch Entry", "DocType", "Hatch Entry", "poultry-chick"),
			("Chick Dispatch", "DocType", "Chick Dispatch", "poultry-dispatch"),
			("Hatchery Machine", "DocType", "Hatchery Machine", "poultry-hatchery"),
			("Hatchery Performance", "Report", "Hatchery Performance", "poultry-chart"),
		],
	},
	"Poultry Setup": {
		"icon": "poultry-settings",
		"items": [
			("Home", "Workspace", "Poultry Setup", "poultry-settings"),
			("Farm", "DocType", "Farm", "poultry-farm"),
			("Shed", "DocType", "Shed", "poultry-shed"),
			("Breed", "DocType", "Breed", "poultry-dna"),
			("Strain", "DocType", "Strain", "poultry-chick"),
			("Breed Standard", "DocType", "Breed Standard", "poultry-standard"),
			("Feed Type", "DocType", "Feed Type", "poultry-feed-bag"),
			("Egg Grade", "DocType", "Egg Grade", "poultry-egg"),
			("Mortality Reason", "DocType", "Mortality Reason", "poultry-mortality"),
			("Hatchery Machine", "DocType", "Hatchery Machine", "poultry-hatchery"),
			("Poultry Settings", "DocType", "Poultry Settings", "poultry-settings"),
		],
	},
	"Poultry Analytics": {
		"icon": "poultry-chart",
		"items": [
			("Home", "Workspace", "Poultry Analytics", "poultry-chart"),
			("Cost & Profitability", "Page", "poultry-cost-hub", "poultry-cost"),
			("Sales & Purchases", "Page", "poultry-trade", "poultry-sales"),
			("Flock Performance vs Standard", "Report", "Flock Performance vs Standard",
			 "poultry-standard"),
			("Broiler Batch Summary", "Report", "Broiler Batch Summary", "poultry-broiler"),
			("Layer Production Curve", "Report", "Layer Production Curve", "poultry-layer"),
			("Feed Consumption and FCR Trend", "Report", "Feed Consumption and FCR Trend",
			 "poultry-feed-bag"),
			("Mortality Analysis", "Report", "Mortality Analysis", "poultry-mortality"),
			("Hatchery Performance", "Report", "Hatchery Performance", "poultry-hatchery"),
			("Shed Utilisation and Downtime", "Report", "Shed Utilisation and Downtime",
			 "poultry-shed"),
			("Stock Ledger", "Report", "Stock Ledger", "poultry-stock"),
			("Profit and Loss Statement", "Report", "Profit and Loss Statement", "poultry-cost"),
		],
	},
}


def install():
	for name, cfg in SIDEBARS.items():
		if not frappe.db.exists("Workspace", name):
			continue
		if frappe.db.exists("Workspace Sidebar", name):
			doc = frappe.get_doc("Workspace Sidebar", name)
		else:
			doc = frappe.new_doc("Workspace Sidebar")
			doc.name = name
		doc.title = name
		doc.app = "poultry"
		doc.header_icon = cfg["icon"]
		doc.standard = 1
		doc.set("items", [])
		for label, link_type, link_to, icon in cfg["items"]:
			dt = {"Report": "Report", "Page": "Page", "DocType": "DocType",
			      "Workspace": "Workspace"}[link_type]
			if not frappe.db.exists(dt, link_to):
				continue
			doc.append("items", {"type": "Link", "label": label, "link_type": link_type,
			                     "link_to": link_to, "icon": icon})
		doc.flags.ignore_permissions = True
		doc.save()
		print(f"  + sidebar {name}: {len(doc.items)} items")
	frappe.db.commit()
	frappe.clear_cache()


run = install
