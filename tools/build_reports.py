"""Register the poultry script reports and write their filter UIs."""

import os
import shutil

import frappe

MODULE = "Poultry Management"
SRC = "/mnt/c/Users/jajul/poultry_build/reports"

DATE_RANGE = """
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today()},
"""

REPORTS = [
	{
		"name": "Flock Performance vs Standard",
		"file": "flock_performance_vs_standard",
		"ref": "Flock",
		"js": """
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock",
		 reqd: 1, get_query: () => ({filters: {status: ["!=", "Draft"]}})},
""",
	},
	{
		"name": "Broiler Batch Summary",
		"file": "broiler_batch_summary",
		"ref": "Flock",
		"js": """
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "status", label: __("Status"), fieldtype: "Select",
		 options: ["", "Placed", "Growing", "Depleting", "Closed"]},
""",
	},
	{
		"name": "Mortality Analysis",
		"file": "mortality_analysis",
		"ref": "Daily Flock Entry",
		"js": DATE_RANGE + """
		{fieldname: "group_by", label: __("Group By"), fieldtype: "Select",
		 options: ["Reason", "Category", "Age Band", "Shed", "Farm", "Flock"],
		 default: "Reason", reqd: 1},
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
""",
	},
	{
		"name": "Layer Production Curve",
		"file": "layer_production_curve",
		"ref": "Flock",
		"js": """
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock", reqd: 1,
		 get_query: () => ({filters: {flock_type: ["in", ["Layer", "Breeder"]]}})},
""",
	},
	{
		"name": "Feed Consumption and FCR Trend",
		"file": "feed_consumption_and_fcr_trend",
		"ref": "Daily Flock Entry",
		"js": DATE_RANGE + """
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
""",
	},
	{
		"name": "Vaccination Compliance",
		"file": "vaccination_compliance",
		"ref": "Flock Vaccination Plan",
		"js": """
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
		{fieldname: "flock", label: __("Flock"), fieldtype: "Link", options: "Flock"},
		{fieldname: "status_filter", label: __("Show"), fieldtype: "Select",
		 options: ["All", "Overdue only", "Done only"], default: "All"},
		{fieldname: "only_active", label: __("Active flocks only"), fieldtype: "Check", default: 1},
""",
	},
	{
		"name": "Withdrawal Period Alert",
		"file": "withdrawal_period_alert",
		"ref": "Medication Entry",
		"js": """
		{fieldname: "as_on", label: __("As On"), fieldtype: "Date",
		 default: frappe.datetime.get_today(), reqd: 1},
""",
	},
	{
		"name": "Hatchery Performance",
		"file": "hatchery_performance",
		"ref": "Egg Setting",
		"js": DATE_RANGE + """
		{fieldname: "source_flock", label: __("Source Flock"), fieldtype: "Link",
		 options: "Flock"},
		{fieldname: "setter", label: __("Setter"), fieldtype: "Link",
		 options: "Hatchery Machine"},
""",
	},
	{
		"name": "Shed Utilisation and Downtime",
		"file": "shed_utilisation_and_downtime",
		"ref": "Shed",
		"js": """
		{fieldname: "farm", label: __("Farm"), fieldtype: "Link", options: "Farm"},
""",
	},
]

ROLES = ["Poultry Manager", "Farm Manager", "Veterinarian", "Poultry Accounts", "System Manager"]


def report_dir(fname):
	base = frappe.get_app_path("poultry", "poultry_management", "report", fname)
	os.makedirs(base, exist_ok=True)
	init = os.path.join(base, "__init__.py")
	if not os.path.exists(init):
		open(init, "w").close()
	return base


def run():
	for r in REPORTS:
		base = report_dir(r["file"])
		shutil.copy(os.path.join(SRC, r["file"] + ".py"), os.path.join(base, r["file"] + ".py"))

		js = 'frappe.query_reports["%s"] = {\n\tfilters: [%s\t],\n};\n' % (r["name"], r["js"])
		with open(os.path.join(base, r["file"] + ".js"), "w") as fh:
			fh.write(js)

		if frappe.db.exists("Report", r["name"]):
			doc = frappe.get_doc("Report", r["name"])
			doc.disabled = 0
		else:
			doc = frappe.new_doc("Report")
			doc.report_name = r["name"]
		doc.ref_doctype = r["ref"]
		doc.report_type = "Script Report"
		doc.module = MODULE
		doc.is_standard = "Yes"
		doc.set("roles", [{"role": role} for role in ROLES])
		doc.flags.ignore_permissions = True
		doc.save()
		print("  + report:", r["name"])

	frappe.db.commit()
	print("REPORTS DONE:", len(REPORTS))
