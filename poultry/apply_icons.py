"""Give every poultry doctype, workspace, shortcut and link its own icon."""

import frappe

DOCTYPE_ICONS = {
	"Farm": "poultry-farm",
	"Shed": "poultry-shed",
	"Flock": "poultry-hen",
	"Daily Flock Entry": "poultry-clipboard",
	"Bird Weighing": "poultry-scale",
	"Flock Closure": "poultry-closure",
	"Breed": "poultry-dna",
	"Strain": "poultry-chick",
	"Breed Standard": "poultry-standard",
	"Mortality Reason": "poultry-mortality",
	"Feed Type": "poultry-feed-bag",
	"Egg Grade": "poultry-egg",
	"Vaccine": "poultry-syringe",
	"Poultry Medication": "poultry-pill",
	"Poultry Disease": "poultry-virus",
	"Vaccination Schedule Template": "poultry-schedule",
	"Flock Vaccination Plan": "poultry-schedule",
	"Vaccination Entry": "poultry-syringe",
	"Medication Entry": "poultry-pill",
	"Poultry Settings": "poultry-settings",
}

WORKSPACE_ICONS = {
	"Poultry": "poultry-hen",
	"Poultry Setup": "poultry-settings",
	"Poultry Health": "poultry-syringe",
	"Poultry Analytics": "poultry-chart",
}

# reports and non-poultry doctypes referenced from workspace cards
EXTRA_ICONS = {
	"Flock Performance vs Standard": "poultry-standard",
	"Broiler Batch Summary": "poultry-hen",
	"Mortality Analysis": "poultry-mortality",
	"Layer Production Curve": "poultry-egg",
	"Feed Consumption and FCR Trend": "poultry-feed-bag",
	"Vaccination Compliance": "poultry-schedule",
	"Withdrawal Period Alert": "poultry-withdrawal",
	"Shed Utilisation and Downtime": "poultry-shed",
	"Stock Ledger": "poultry-chart",
	"Stock Balance": "poultry-chart",
	"Profit and Loss Statement": "poultry-chart",
	"Stock Entry": "poultry-feed-bag",
	"Purchase Receipt": "poultry-feed-bag",
	"Sales Invoice": "poultry-egg-tray",
	"Item": "poultry-egg-tray",
	"Poultry Control Tower": "poultry-alert",
	"Flock 360": "poultry-hen",
}


def icon_for(label):
	return DOCTYPE_ICONS.get(label) or EXTRA_ICONS.get(label) or WORKSPACE_ICONS.get(label)


def run():
	for dt, icon in DOCTYPE_ICONS.items():
		if frappe.db.exists("DocType", dt):
			frappe.db.set_value("DocType", dt, "icon", icon, update_modified=False)
	print(f"  + doctype icons: {len(DOCTYPE_ICONS)}")

	for ws, icon in WORKSPACE_ICONS.items():
		if not frappe.db.exists("Workspace", ws):
			continue
		doc = frappe.get_doc("Workspace", ws)
		doc.icon = icon
		for row in doc.links:
			ic = icon_for(row.label)
			if ic:
				row.icon = ic
		for row in doc.shortcuts:
			ic = icon_for(row.label)
			if ic:
				row.icon = ic
		doc.flags.ignore_permissions = True
		doc.save()
		print(f"  + workspace {ws}: icon={icon}, "
		      f"{sum(1 for r in doc.links if r.icon)} link icons, "
		      f"{sum(1 for r in doc.shortcuts if r.icon)} shortcut icons")

	for sb, icon in WORKSPACE_ICONS.items():
		if not frappe.db.exists("Workspace Sidebar", sb):
			continue
		doc = frappe.get_doc("Workspace Sidebar", sb)
		doc.header_icon = icon
		for row in doc.items:
			ic = icon_for(row.label)
			if ic:
				row.icon = ic
		doc.flags.ignore_permissions = True
		doc.save()
		print(f"  + sidebar {sb}: {sum(1 for r in doc.items if r.icon)} item icons")

	for di in frappe.get_all("Desktop Icon", fields=["name", "label"]):
		ic = icon_for(di.label)
		if ic:
			frappe.db.set_value("Desktop Icon", di.name, "icon", ic, update_modified=False)

	frappe.db.commit()
	frappe.clear_cache()
	print("ICONS APPLIED")
