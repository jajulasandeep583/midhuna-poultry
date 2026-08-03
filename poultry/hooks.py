app_name = "poultry"
app_title = "Poultry Management"
app_publisher = "Midhuna Tech"
app_description = "Poultry farm management for Frappe/ERPNext v16"
app_email = "aimidhunatech@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

app_home = "/app/poultry"

# Purpose-drawn icon set, so every doctype and workspace reads as poultry
# rather than sharing one generic glyph.
app_include_icons = ["/assets/poultry/icons/poultry-icons.svg"]

# Puts Poultry in the v16 app switcher, so its workspaces get their own sidebar
# instead of hiding under ERPNext.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/poultry/images/poultry-logo.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "poultry.check_app_permission",
	}
]

# NOTE: no app_include_js. The scaffold suggests "poultry.bundle.js", but the
# file does not exist, and the resulting 404 on every desk page aborts the rest
# of the bundle - which silently stops workspace chart widgets from rendering.
# Add it back only together with a real file and a `bench build --app poultry`.

after_install = "poultry.setup.after_install"
after_migrate = "poultry.setup.after_migrate"

# Core doctypes are never forked (§2.3) - they are extended through document
# events and custom fields only, so the app stays upgradeable.
doc_events = {
	"Delivery Note": {
		"validate": "poultry.compliance.block_sales_under_withdrawal",
	},
	"Sales Invoice": {
		"validate": "poultry.compliance.block_sales_under_withdrawal",
	},
}

scheduler_events = {
	"daily": [
		"poultry.tasks.flag_overdue_vaccinations",
		"poultry.tasks.update_shed_downtime",
		"poultry.tasks.refresh_open_flocks",
	],
}
