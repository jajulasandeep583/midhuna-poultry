"""Everything the app builds for itself at install time.

Doctypes, reports, desk pages and workspaces are plain files in the app and are
synced by Frappe. What is NOT file-based - custom fields on core doctypes,
roles, number cards, dashboard charts, icons and the reference masters - is
built here, so a fresh `bench install-app poultry` reproduces the whole product
from this repository with nothing done by hand.
"""

import frappe

ROLES = [
	"Poultry Manager",
	"Farm Manager",
	"Farm Supervisor",
	"Veterinarian",
	"Poultry Accounts",
]


def after_install():
	print("Setting up Poultry Management...")
	make_roles()

	from poultry.setup import custom_fields, desk, icons, masters, sidebar

	custom_fields.install()
	masters.install()
	desk.install()
	sidebar.install()
	icons.install()

	frappe.db.commit()
	print("Poultry Management is ready. Open the Poultry workspace.")


def after_migrate():
	"""Keep the desk objects and icons in step with the code on every migrate."""
	from poultry.setup import desk, icons, sidebar

	try:
		desk.install()
		sidebar.install()
		icons.install()
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Poultry: after_migrate desk rebuild failed")


def make_roles():
	for r in ROLES:
		if not frappe.db.exists("Role", r):
			frappe.get_doc({"doctype": "Role", "role_name": r, "desk_access": 1}).insert(
				ignore_permissions=True)
	print(f"  + roles: {len(ROLES)}")
