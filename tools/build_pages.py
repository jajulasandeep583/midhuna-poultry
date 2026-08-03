"""Register the two Poultry desk pages and copy their JS into the app."""

import os
import shutil

import frappe

MODULE = "Poultry Management"
SRC = "/mnt/c/Users/jajul/poultry_build/pages"

PAGES = [
	{
		"name": "poultry-tower",
		"file": "poultry_tower",
		"title": "Poultry Control Tower",
		"icon": "poultry-alert",
	},
	{
		"name": "poultry-entry-board",
		"file": "poultry_entry_board",
		"title": "Daily Entry Board",
		"icon": "poultry-board",
	},
	{
		"name": "poultry-guide",
		"file": "poultry_guide",
		"title": "How to Use Poultry",
		"icon": "poultry-guide",
	},
	{
		"name": "poultry-health-hub",
		"file": "poultry_health_hub",
		"title": "Vaccination & Health",
		"icon": "poultry-syringe",
	},
	{
		"name": "poultry-cost-hub",
		"file": "poultry_cost_hub",
		"title": "Cost & Profitability",
		"icon": "poultry-cost",
	},
	{
		"name": "poultry-flock-360",
		"file": "poultry_flock_360",
		"title": "Flock 360",
		"icon": "poultry-hen",
	},
]

ROLES = ["Poultry Manager", "Farm Manager", "Farm Supervisor", "Veterinarian",
         "Poultry Accounts", "System Manager"]


def run():
	for p in PAGES:
		if frappe.db.exists("Page", p["name"]):
			doc = frappe.get_doc("Page", p["name"])
		else:
			doc = frappe.new_doc("Page")
			doc.name = p["name"]
			doc.page_name = p["name"]
		doc.title = p["title"]
		doc.module = MODULE
		doc.standard = "Yes"
		doc.icon = p["icon"]
		doc.set("roles", [{"role": r} for r in ROLES])
		doc.flags.ignore_permissions = True
		doc.save()

		folder = frappe.get_app_path("poultry", "poultry_management", "page",
		                             p["name"].replace("-", "_"))
		os.makedirs(folder, exist_ok=True)
		init = os.path.join(folder, "__init__.py")
		if not os.path.exists(init):
			open(init, "w").close()
		shutil.copy(os.path.join(SRC, p["file"] + ".js"),
		            os.path.join(folder, p["name"].replace("-", "_") + ".js"))
		print(f"  + page: {p['name']} -> {folder}")

	frappe.db.commit()
	print("PAGES DONE")
