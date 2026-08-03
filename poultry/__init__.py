__version__ = "0.1.0"

import frappe


def check_app_permission():
	"""Who sees Poultry in the app switcher."""
	if frappe.session.user == "Administrator":
		return True
	roles = frappe.get_roles()
	return any(r in roles for r in (
		"System Manager", "Poultry Manager", "Farm Manager", "Farm Supervisor",
		"Veterinarian", "Poultry Accounts",
	))
