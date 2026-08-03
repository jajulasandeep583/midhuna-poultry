"""Build the Poultry app sidebar explicitly.

Frappe's auto-generator creates a Workspace Sidebar once and never revisits it,
so pages added later never appear. This owns the order and the icons instead of
hoping the generator picks them up.
"""

import frappe

SIDEBARS = {
	"Poultry": {
		"icon": "poultry-hen",
		"items": [
			("Home", "Workspace", "Poultry", "poultry-hen"),
			("Management", "Page", "poultry-manage", "poultry-manage"),
			("Sales & Purchases", "Page", "poultry-trade", "poultry-sales"),
			("Stock on Hand", "Page", "poultry-stock", "poultry-stock"),
			("Control Tower", "Page", "poultry-tower", "poultry-alert"),
			("Flock 360", "Page", "poultry-flock-360", "poultry-target"),
			("Daily Entry Board", "Page", "poultry-entry-board", "poultry-board"),
			("Vaccination & Health", "Page", "poultry-health-hub", "poultry-syringe"),
			("Cost & Profitability", "Page", "poultry-cost-hub", "poultry-cost"),
			("Daily Flock Entry", "DocType", "Daily Flock Entry", "poultry-clipboard"),
			("Flock", "DocType", "Flock", "poultry-layer"),
			("Shed", "DocType", "Shed", "poultry-shed"),
			("Bird Weighing", "DocType", "Bird Weighing", "poultry-scale"),
			("Vaccination Entry", "DocType", "Vaccination Entry", "poultry-syringe"),
			("Medication Entry", "DocType", "Medication Entry", "poultry-pill"),
			("Broiler Batch Summary", "Report", "Broiler Batch Summary", "poultry-broiler"),
			("Withdrawal Period Alert", "Report", "Withdrawal Period Alert", "poultry-withdrawal"),
			("How to Use Poultry", "Page", "poultry-guide", "poultry-guide"),
			("Poultry Settings", "DocType", "Poultry Settings", "poultry-settings"),
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
			("Poultry Settings", "DocType", "Poultry Settings", "poultry-settings"),
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
	"Poultry Analytics": {
		"icon": "poultry-chart",
		"items": [
			("Home", "Workspace", "Poultry Analytics", "poultry-chart"),
			("Cost & Profitability", "Page", "poultry-cost-hub", "poultry-cost"),
			("Sales & Purchases", "Page", "poultry-trade", "poultry-sales"),
			("Stock on Hand", "Page", "poultry-stock", "poultry-stock"),
			("Flock Performance vs Standard", "Report", "Flock Performance vs Standard",
			 "poultry-standard"),
			("Broiler Batch Summary", "Report", "Broiler Batch Summary", "poultry-broiler"),
			("Layer Production Curve", "Report", "Layer Production Curve", "poultry-layer"),
			("Feed Consumption and FCR Trend", "Report", "Feed Consumption and FCR Trend",
			 "poultry-feed-bag"),
			("Mortality Analysis", "Report", "Mortality Analysis", "poultry-mortality"),
			("Vaccination Compliance", "Report", "Vaccination Compliance", "poultry-schedule"),
			("Shed Utilisation and Downtime", "Report", "Shed Utilisation and Downtime",
			 "poultry-shed"),
			("Stock Ledger", "Report", "Stock Ledger", "poultry-cost"),
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
			if link_type == "Report" and not frappe.db.exists("Report", link_to):
				continue
			if link_type == "Page" and not frappe.db.exists("Page", link_to):
				continue
			if link_type == "DocType" and not frappe.db.exists("DocType", link_to):
				continue
			doc.append("items", {
				"type": "Link", "label": label, "link_type": link_type,
				"link_to": link_to, "icon": icon,
			})
		doc.flags.ignore_permissions = True
		doc.save()
		print(f"  + sidebar {name}: {len(doc.items)} items")
	frappe.db.commit()
	frappe.clear_cache()


run = install
