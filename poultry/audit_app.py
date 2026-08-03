"""Does the app hold every customisation, or does some of it only exist in this
site's database?

Anything listed as NOT REPRODUCED would be lost on a fresh install.
"""

import os

import frappe

APP = "poultry"
MODULE = "Poultry Management"


def app_files(*parts):
	path = frappe.get_app_path(APP, *parts)
	return set(os.listdir(path)) if os.path.exists(path) else set()


def run():
	base = frappe.get_app_path(APP)
	print(f"APP PATH: {base}")
	print(f"GIT: {'yes' if os.path.exists(os.path.join(base, '..', '.git')) else 'no'}")

	ok, gap = [], []

	# ---------------------------------------------------------- file-based
	dt_dirs = app_files("poultry_management", "doctype")
	dts = frappe.get_all("DocType", filters={"module": MODULE}, pluck="name")
	missing = [d for d in dts if frappe.scrub(d) not in dt_dirs]
	(ok if not missing else gap).append(
		f"DocTypes: {len(dts)} in db, {len(dt_dirs)} folders on disk"
		+ (f" | MISSING ON DISK: {missing}" if missing else ""))

	rep_dirs = app_files("poultry_management", "report")
	reps = frappe.get_all("Report", filters={"module": MODULE}, pluck="name")
	rmiss = [r for r in reps if frappe.scrub(r) not in rep_dirs]
	(ok if not rmiss else gap).append(
		f"Reports: {len(reps)} in db, {len(rep_dirs) - 1} folders"
		+ (f" | MISSING: {rmiss}" if rmiss else ""))

	pg_dirs = app_files("poultry_management", "page")
	pgs = frappe.get_all("Page", filters={"module": MODULE}, pluck="name")
	pmiss = [p for p in pgs if p.replace("-", "_") not in pg_dirs]
	(ok if not pmiss else gap).append(
		f"Pages: {len(pgs)} in db, {len(pg_dirs) - 1} folders"
		+ (f" | MISSING: {pmiss}" if pmiss else ""))

	ws_dirs = app_files("poultry_management", "workspace")
	wss = frappe.get_all("Workspace", filters={"module": MODULE}, pluck="name")
	wmiss = [w for w in wss if frappe.scrub(w) not in ws_dirs]
	(ok if not wmiss else gap).append(
		f"Workspaces: {len(wss)} in db, {len(ws_dirs) - 1} folders"
		+ (f" | MISSING: {wmiss}" if wmiss else ""))

	# ---------------------------------------------------------- code-built
	setup_files = app_files("setup")
	built = {
		"custom_fields.py": ("Custom Field", frappe.db.count(
			"Custom Field", {"fieldname": ["like", "poultry%"]})),
		"desk.py": ("Number Card + Dashboard Chart",
		            frappe.db.count("Number Card", {"module": MODULE})
		            + frappe.db.count("Dashboard Chart", {"module": MODULE})),
		"sidebar.py": ("Workspace Sidebar", frappe.db.count(
			"Workspace Sidebar", {"app": APP})),
		"desktop_icons.py": ("Desktop Icon", frappe.db.count("Desktop Icon", {"app": APP})),
		"navblock.py": ("Custom HTML Block", frappe.db.count(
			"Custom HTML Block", {"name": "Poultry Navigator"})),
		"masters.py": ("reference masters", frappe.db.count("Breed Standard")
		               + frappe.db.count("Vaccine") + frappe.db.count("Chick Type")),
	}
	for fname, (what, count) in built.items():
		line = f"{what}: {count} in db, built by setup/{fname}"
		(ok if fname in setup_files and count else gap).append(line)

	# ---------------------------------------------------------- orphans
	orphan_cf = frappe.get_all(
		"Custom Field",
		filters={"dt": ["in", ["Stock Entry", "Batch", "Delivery Note Item"]]},
		fields=["dt", "fieldname"])
	print("\nCUSTOM FIELDS ON CORE DOCTYPES")
	for c in orphan_cf:
		covered = c.fieldname == "poultry_flock"
		print(f"  {'OK ' if covered else '!! '}{c.dt}.{c.fieldname}"
		      + ("" if covered else "   <-- NOT created by the app"))

	ps = frappe.get_all("Property Setter", filters={"doc_type": ["in", dts]}, pluck="name")
	cs = frappe.get_all("Client Script", pluck="name")
	sv = frappe.get_all("Server Script", pluck="name")
	print(f"\nProperty Setters on poultry doctypes: {len(ps)}")
	print(f"Client Scripts on site: {len(cs)} {cs[:5]}")
	print(f"Server Scripts on site: {len(sv)} {sv[:5]}")

	# ---------------------------------------------------------- site-only
	print("\nSITE-LEVEL SETTINGS (not app code - a fresh site needs these set)")
	print("  Stock Settings.enable_serial_and_batch_no_for_item =",
	      frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item"))
	print("  User.default_workspace (Administrator) =",
	      frappe.db.get_value("User", "Administrator", "default_workspace"))
	print("  Poultry Settings.mortality_expense_account =",
	      frappe.db.get_single_value("Poultry Settings", "mortality_expense_account"))

	print("\n--- REPRODUCED BY THE APP ---")
	for line in ok:
		print("  OK  " + line)
	if gap:
		print("\n--- NOT REPRODUCED ---")
		for line in gap:
			print("  !!  " + line)
	else:
		print("\nNo gaps: everything above is rebuilt from the repository.")
