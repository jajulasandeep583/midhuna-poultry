import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	make_custom_fields()
	frappe.db.commit()


def make_custom_fields():
	"""ERPNext core doctypes are extended, never forked (§2.3). Tagging the
	flock onto Stock Entry is what lets flock cost be read back out of the
	stock ledger instead of kept in a parallel accumulator."""
	create_custom_fields({
		"Stock Entry": [{
			"fieldname": "poultry_flock",
			"label": "Flock",
			"fieldtype": "Link",
			"options": "Flock",
			"insert_after": "project",
			"read_only": 0,
			"allow_on_submit": 0,
		}],
		"Batch": [{
			"fieldname": "poultry_flock",
			"label": "Flock",
			"fieldtype": "Link",
			"options": "Flock",
			"insert_after": "item",
			"read_only": 1,
		}],
		"Delivery Note Item": [{
			"fieldname": "poultry_flock",
			"label": "Flock",
			"fieldtype": "Link",
			"options": "Flock",
			"insert_after": "batch_no",
			"read_only": 1,
			"print_hide": 1,
		}],
	}, ignore_validate=True)


# alias used by poultry.setup.after_install
install = after_install
