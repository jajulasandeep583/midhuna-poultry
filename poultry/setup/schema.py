"""Create every Poultry doctype. Idempotent - safe to re-run."""

import frappe

MODULE = "Poultry Management"

ROLES = [
	"Poultry Manager",
	"Farm Manager",
	"Farm Supervisor",
	"Veterinarian",
	"Poultry Accounts",
]

FLOCK_TYPES = "\nBroiler\nLayer\nRearing\nBreeder"
ROUTES = "\nDrinking Water\nEye Drop\nSpray\nSubcutaneous\nIntramuscular\nWing Web\nIn-Ovo\nBeak Dip"


def f(fieldname, label, fieldtype="Data", **kw):
	d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
	d.update(kw)
	return d


def sb(fieldname, label="", **kw):
	d = {"fieldname": fieldname, "fieldtype": "Section Break", "label": label}
	d.update(kw)
	return d


def cb(fieldname, **kw):
	d = {"fieldname": fieldname, "fieldtype": "Column Break"}
	d.update(kw)
	return d


def perms(master=False, submittable=False):
	"""Master data is manager-maintained; transactions are supervisor-enterable.

	submit/cancel/amend may only be set on submittable doctypes - the DocType
	validator rejects them outright anywhere else.
	"""
	def full(**extra):
		d = {"read": 1, "write": 1, "create": 1, "report": 1, "export": 1, "print": 1}
		if submittable:
			d.update({"submit": 1, "cancel": 1, "amend": 1})
		d.update(extra)
		return d

	p = [
		dict(role="System Manager", delete=1, share=1, email=1, **full()),
		dict(role="Poultry Manager", delete=1, share=1, email=1, **full()),
	]
	if master:
		p += [
			{"role": "Farm Manager", "read": 1, "report": 1, "print": 1},
			{"role": "Farm Supervisor", "read": 1},
			{"role": "Veterinarian", "read": 1, "report": 1},
			{"role": "Poultry Accounts", "read": 1, "report": 1},
		]
	else:
		p += [
			dict(role="Farm Manager", delete=1, **full()),
			{"role": "Farm Supervisor", "read": 1, "write": 1, "create": 1, "report": 1, "print": 1,
			 **({"submit": 1} if submittable else {})},
			{"role": "Veterinarian", "read": 1, "report": 1, "print": 1},
			{"role": "Poultry Accounts", "read": 1, "report": 1, "print": 1},
		]
	return p


def make(name, fields, child=False, submittable=False, single=False, autoname=None,
         title_field=None, master=False, sort_field=None, search_fields=None, **kw):
	if frappe.db.exists("DocType", name):
		print("  = exists:", name)
		return
	doc = {
		"doctype": "DocType",
		"name": name,
		"module": MODULE,
		"custom": 0,
		"istable": 1 if child else 0,
		"issingle": 1 if single else 0,
		"is_submittable": 1 if submittable else 0,
		"editable_grid": 1,
		"track_changes": 0 if child else 1,
		"fields": fields,
		"permissions": [] if child else perms(master=master, submittable=submittable),
	}
	if autoname:
		doc["autoname"] = autoname
	if title_field:
		doc["title_field"] = title_field
		doc["show_title_field_in_link"] = 1
	if sort_field:
		doc["sort_field"] = sort_field
		doc["sort_order"] = "DESC"
	if search_fields:
		doc["search_fields"] = search_fields
	doc.update(kw)
	frappe.get_doc(doc).insert(ignore_permissions=True)
	print("  + created:", name)


def series(options):
	return f("naming_series", "Series", "Select", options=options, default=options.split("\n")[0],
	         reqd=1, no_copy=1, print_hide=1)


def amended(dt):
	return f("amended_from", "Amended From", "Link", options=dt, read_only=1,
	         no_copy=1, print_hide=1)


# ---------------------------------------------------------------- roles
def build_roles():
	for r in ROLES:
		if not frappe.db.exists("Role", r):
			frappe.get_doc({"doctype": "Role", "role_name": r, "desk_access": 1}).insert(
				ignore_permissions=True)
			print("  + role:", r)


# ---------------------------------------------------------------- masters
def build_masters():
	make("Poultry Settings", [
		sb("sec_modules", "Modules"),
		f("enable_egg_management", "Enable Egg Management", "Check", default="1"),
		f("enable_hatchery", "Enable Hatchery", "Check"),
		f("enable_processing", "Enable Processing", "Check"),
		cb("cb_modules"),
		f("enable_contract_farming", "Enable Contract Farming", "Check"),
		f("enable_breeder_operations", "Enable Breeder Operations", "Check"),
		f("enable_feed_mill", "Enable Feed Mill", "Check"),
		sb("sec_entry", "Data Entry"),
		f("data_tier", "Data Tier", "Select", options="Tier 1\nTier 2\nTier 3", default="Tier 2",
		  description="Tier 1 = mortality and feed only. Tier 2 adds eggs, weight, water. Tier 3 adds environment."),
		f("allow_backdated_entry", "Allow Backdated Entry", "Check", default="1"),
		f("max_backdate_days", "Max Backdate Days", "Int", default="30"),
		cb("cb_entry"),
		f("default_bag_weight_kg", "Default Bag Weight (kg)", "Float", default="50"),
		f("eggs_per_tray", "Eggs per Tray", "Int", default="30"),
		sb("sec_alerts", "Alert Thresholds"),
		f("mortality_spike_threshold_pct", "Mortality Spike Threshold (%/day)", "Float", default="0.5"),
		f("weight_deviation_threshold_pct", "Weight Deviation Threshold (%)", "Float", default="10"),
		cb("cb_alerts"),
		f("cumulative_mortality_factor", "Cumulative Mortality Alert Factor", "Float", default="1.5"),
		f("water_feed_factor", "Water:Feed Alert Factor", "Float", default="1.25"),
		sb("sec_costing", "Costing and Stock"),
		f("costing_method", "Costing Method", "Select", options="Project\nWork Order", default="Project"),
		f("create_stock_entries", "Post Stock Entries on Daily Entry", "Check", default="1"),
		f("auto_create_vaccination_plan", "Auto Create Vaccination Plan", "Check", default="1"),
		cb("cb_costing"),
		f("default_company", "Default Company", "Link", options="Company"),
		f("mortality_expense_account", "Mortality Expense Account", "Link", options="Account"),
		f("egg_warehouse", "Default Egg Warehouse", "Link", options="Warehouse"),
	], single=True, master=True)

	make("Poultry Disease", [
		f("disease_name", "Disease Name", reqd=1, unique=1, in_list_view=1),
		f("is_notifiable", "Notifiable Disease", "Check", in_list_view=1),
		f("typical_age_days", "Typical Age (days)", "Int"),
		f("clinical_signs", "Clinical Signs", "Small Text"),
	], autoname="field:disease_name", master=True)

	make("Breed", [
		f("breed_name", "Breed Name", reqd=1, unique=1, in_list_view=1),
		f("bird_type", "Bird Type", "Select", options="\nBroiler\nLayer\nDual Purpose\nNative\nBreeder",
		  in_list_view=1),
		f("description", "Description", "Small Text"),
	], autoname="field:breed_name", master=True)

	make("Strain", [
		f("strain_name", "Strain Name", reqd=1, unique=1, in_list_view=1),
		f("breed", "Breed", "Link", options="Breed", reqd=1, in_list_view=1),
		f("supplier", "Supplier", "Link", options="Supplier"),
		cb("cb1"),
		f("typical_cycle_days", "Typical Cycle (days)", "Int", in_list_view=1),
		f("bird_type", "Bird Type", "Select", options="\nBroiler\nLayer\nDual Purpose\nNative\nBreeder",
		  fetch_from="breed.bird_type", read_only=1),
	], autoname="field:strain_name", master=True)

	make("Breed Standard Detail", [
		f("age_days", "Age (days)", "Int", in_list_view=1, columns=1),
		f("age_weeks", "Age (weeks)", "Float", read_only=1, precision="1"),
		f("std_body_weight_g", "Body Weight (g)", "Float", in_list_view=1, columns=1),
		f("std_daily_feed_g", "Daily Feed (g)", "Float", in_list_view=1, columns=1),
		f("std_cumulative_feed_g", "Cumulative Feed (g)", "Float", in_list_view=1, columns=1),
		f("std_fcr", "FCR", "Float", precision="3", in_list_view=1, columns=1),
		f("std_cumulative_mortality_pct", "Cumulative Mortality %", "Percent", in_list_view=1, columns=1),
		f("std_hd_production_pct", "HD Production %", "Percent", in_list_view=1, columns=1),
		f("std_egg_weight_g", "Egg Weight (g)", "Float"),
		f("std_uniformity_pct", "Uniformity %", "Percent"),
		f("std_water_feed_ratio", "Water:Feed", "Float", precision="2"),
	], child=True)

	make("Breed Standard", [
		f("standard_name", "Standard Name", reqd=1, unique=1),
		f("strain", "Strain", "Link", options="Strain", reqd=1, in_list_view=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, in_list_view=1),
		cb("cb1"),
		f("source", "Source", description="Breeder company management guide and revision"),
		f("is_default", "Is Default for Strain", "Check", in_list_view=1),
		sb("sec_detail", "Standard by Age"),
		f("details", "Details", "Table", options="Breed Standard Detail"),
	], autoname="field:standard_name", master=True)

	make("Mortality Reason", [
		f("reason", "Reason", reqd=1, unique=1, in_list_view=1),
		f("category", "Category", "Select",
		  options="\nDisease\nCulling\nEnvironmental\nPredation\nHandling\nCannibalism\nUnknown",
		  in_list_view=1),
		cb("cb1"),
		f("is_culling", "Counts as Culling", "Check", in_list_view=1),
		f("requires_postmortem", "Requires Post Mortem", "Check"),
	], autoname="field:reason", master=True)

	make("Feed Type", [
		f("feed_type_name", "Feed Type", reqd=1, unique=1, in_list_view=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, in_list_view=1),
		f("item", "Item", "Link", options="Item", in_list_view=1),
		cb("cb1"),
		f("age_from_days", "Age From (days)", "Int"),
		f("age_to_days", "Age To (days)", "Int"),
		f("bag_weight_kg", "Bag Weight (kg)", "Float", default="50"),
	], autoname="field:feed_type_name", master=True)

	make("Egg Grade", [
		f("grade_code", "Grade Code", reqd=1, unique=1, in_list_view=1),
		f("grade_name", "Grade Name", in_list_view=1),
		f("item", "Item", "Link", options="Item", in_list_view=1),
		cb("cb1"),
		f("min_weight_g", "Min Weight (g)", "Float"),
		f("max_weight_g", "Max Weight (g)", "Float"),
		sb("sec_flags"),
		f("is_saleable", "Saleable", "Check", default="1"),
		f("is_hatching_egg", "Hatching Egg", "Check"),
		f("is_reject", "Reject", "Check"),
	], autoname="field:grade_code", master=True)

	make("Vaccine", [
		f("vaccine_name", "Vaccine Name", reqd=1, unique=1, in_list_view=1),
		f("item", "Item", "Link", options="Item"),
		f("disease", "Disease", "Link", options="Poultry Disease", in_list_view=1),
		f("route", "Route", "Select", options=ROUTES, in_list_view=1),
		cb("cb1"),
		f("dose_per_bird", "Dose per Bird", "Float", default="1"),
		f("live_or_killed", "Live or Killed", "Select", options="\nLive\nKilled"),
		f("withdrawal_days", "Withdrawal Days", "Int"),
	], autoname="field:vaccine_name", master=True)

	make("Poultry Medication", [
		f("medication_name", "Medication", reqd=1, unique=1, in_list_view=1),
		f("item", "Item", "Link", options="Item"),
		f("active_ingredient", "Active Ingredient", in_list_view=1),
		cb("cb1"),
		f("dose", "Dose"),
		f("withdrawal_days", "Withdrawal Days", "Int", in_list_view=1),
		f("route", "Route", "Select", options="\nDrinking Water\nFeed\nInjection\nSpray"),
	], autoname="field:medication_name", master=True)

	make("Farm", [
		f("farm_name", "Farm Name", reqd=1, unique=1, in_list_view=1),
		f("farm_type", "Farm Type", "Select",
		  options="\nBroiler\nLayer\nRearing\nBreeder\nHatchery\nFeed Mill\nProcessing", in_list_view=1),
		f("company", "Company", "Link", options="Company", reqd=1),
		f("bird_capacity", "Bird Capacity", "Int", in_list_view=1),
		cb("cb1"),
		f("cost_center", "Cost Center", "Link", options="Cost Center"),
		f("default_warehouse", "Parent Warehouse", "Link", options="Warehouse"),
		f("is_contract_farm", "Contract Farm", "Check"),
		f("grower", "Grower", "Link", options="Supplier", depends_on="is_contract_farm"),
		f("disabled", "Disabled", "Check"),
		sb("sec_location", "Location"),
		f("village", "Village"),
		f("district", "District"),
		f("state", "State"),
		cb("cb2"),
		f("biosecurity_zone", "Biosecurity Zone"),
		f("contact_person", "Contact Person"),
		f("mobile_no", "Mobile No"),
		sb("sec_addr"),
		f("address", "Address", "Small Text"),
	], autoname="field:farm_name", master=True, search_fields="farm_type,village,district")

	make("Shed", [
		f("farm", "Farm", "Link", options="Farm", reqd=1, in_list_view=1),
		f("shed_code", "Shed Code", reqd=1, in_list_view=1),
		f("capacity", "Capacity (birds)", "Int", reqd=1, in_list_view=1),
		f("housing_system", "Housing System", "Select",
		  options="\nDeep Litter\nCage\nSlat\nEnvironment Controlled\nFree Range", in_list_view=1),
		cb("cb1"),
		f("company", "Company", "Link", options="Company", fetch_from="farm.company", read_only=1),
		f("floor_area_sqft", "Floor Area (sqft)", "Float"),
		f("warehouse", "Warehouse", "Link", options="Warehouse", read_only=1,
		  description="Created automatically from the shed code"),
		sb("sec_status", "Status"),
		f("status", "Status", "Select", options="Empty\nOccupied\nCleaning\nUnder Repair",
		  default="Empty", read_only=1, in_list_view=1),
		f("last_depleted_on", "Last Depleted On", "Date", read_only=1),
		cb("cb2"),
		f("last_cleaned_on", "Last Cleaned On", "Date"),
		f("downtime_days", "Downtime Days", "Int", read_only=1),
	], autoname="format:{farm}-{shed_code}", master=True, search_fields="farm,status,capacity")


# ---------------------------------------------------------------- flock
def build_flock():
	make("Flock", [
		series("FLK-.YYYY.-.####"),
		f("flock_name", "Flock Name", reqd=1, in_list_view=1),
		f("farm", "Farm", "Link", options="Farm", reqd=1, in_list_view=1),
		f("shed", "Shed", "Link", options="Shed", reqd=1, in_list_view=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, reqd=1, in_list_view=1),
		cb("cb1"),
		f("company", "Company", "Link", options="Company", fetch_from="farm.company", read_only=1),
		f("breed", "Breed", "Link", options="Breed"),
		f("strain", "Strain", "Link", options="Strain"),
		f("status", "Status", "Select", options="Draft\nPlaced\nGrowing\nLaying\nDepleting\nClosed",
		  default="Draft", read_only=1, in_list_view=1, in_standard_filter=1),

		sb("sec_placement", "Placement"),
		f("source", "Source", "Select", options="\nPurchased DOC\nOwn Hatchery\nTransferred In"),
		f("supplier", "Supplier", "Link", options="Supplier"),
		f("hatch_date", "Hatch Date", "Date"),
		f("placement_date", "Placement Date", "Date", reqd=1),
		f("expected_end_date", "Expected End Date", "Date"),
		cb("cb2"),
		f("bird_item", "Bird Item", "Link", options="Item"),
		f("batch_no", "Batch", "Link", options="Batch", read_only=1),
		f("parent_flock_age_weeks", "Parent Flock Age (weeks)", "Float",
		  description="Breeder age at hatch - explains otherwise unexplained chick quality"),
		f("purchase_receipt", "Purchase Receipt", "Link", options="Purchase Receipt"),

		sb("sec_counts", "Bird Counts"),
		f("opening_qty", "Placed Qty", "Int", reqd=1),
		f("opening_male", "Placed Male", "Int"),
		f("opening_female", "Placed Female", "Int"),
		cb("cb3"),
		f("current_qty", "Birds Alive", "Int", read_only=1, in_list_view=1),
		f("cumulative_mortality", "Cumulative Mortality", "Int", read_only=1),
		f("cumulative_culls", "Cumulative Culls", "Int", read_only=1),
		f("cumulative_sold", "Cumulative Sold", "Int", read_only=1),

		sb("sec_perf", "Performance"),
		f("age_days", "Age (days)", "Int", read_only=1),
		f("mortality_pct", "Mortality %", "Percent", read_only=1),
		f("livability_pct", "Livability %", "Percent", read_only=1),
		f("cumulative_feed_kg", "Cumulative Feed (kg)", "Float", read_only=1),
		cb("cb4"),
		f("avg_body_weight_g", "Avg Body Weight (g)", "Float", read_only=1),
		f("fcr", "FCR", "Float", precision="3", read_only=1),
		f("adg_g", "ADG (g/day)", "Float", precision="1", read_only=1),
		f("eef", "EEF", "Float", precision="1", read_only=1,
		  description="Below 250 poor, 300 average, 350+ good, 400+ excellent"),

		sb("sec_egg", "Egg Production",
		   ),
		f("cumulative_eggs", "Cumulative Eggs", "Int", read_only=1),
		f("hd_production_pct", "HD Production %", "Percent", read_only=1),
		cb("cb5"),
		f("peak_production_pct", "Peak Production %", "Percent", read_only=1),
		f("eggs_per_bird_housed", "Eggs per Bird Housed", "Float", precision="2", read_only=1),

		sb("sec_cost", "Costing"),
		f("cost_center", "Cost Center", "Link", options="Cost Center"),
		f("project", "Project", "Link", options="Project", read_only=1),
		f("work_order", "Work Order", "Link", options="Work Order", read_only=1),
		cb("cb6"),
		f("total_cost", "Total Cost", "Currency", read_only=1),
		f("cost_per_bird", "Cost per Bird", "Currency", read_only=1),
		f("cost_per_kg_live", "Cost per kg Live", "Currency", read_only=1),

		sb("sec_std", "Breed Standard"),
		f("breed_standard", "Breed Standard", "Link", options="Breed Standard"),
		f("standard_snapshot", "Standard Snapshot", "Table", options="Breed Standard Detail",
		  read_only=1, description="Frozen at placement so history stays comparable"),

		sb("sec_closure", "Closure"),
		f("closure_date", "Closure Date", "Date", read_only=1),
		f("total_live_weight_kg", "Total Live Weight (kg)", "Float", read_only=1),
		cb("cb7"),
		f("total_revenue", "Total Revenue", "Currency", read_only=1),
		f("margin", "Margin", "Currency", read_only=1),
	], autoname="naming_series:", title_field="flock_name",
		search_fields="farm,shed,flock_type,status")

	# Shed.current_flock needs Flock to exist first
	if frappe.db.exists("DocType", "Shed") and not frappe.db.exists(
			"DocField", {"parent": "Shed", "fieldname": "current_flock"}):
		shed = frappe.get_doc("DocType", "Shed")
		idx = next(i for i, d in enumerate(shed.fields) if d.fieldname == "last_depleted_on")
		shed.insert_field_after = None
		row = shed.append("fields", {
			"fieldname": "current_flock", "label": "Current Flock", "fieldtype": "Link",
			"options": "Flock", "read_only": 1, "in_list_view": 1,
		})
		shed.fields.remove(row)
		shed.fields.insert(idx, row)
		for i, d in enumerate(shed.fields):
			d.idx = i + 1
		shed.save(ignore_permissions=True)
		print("  + field Shed.current_flock")

	make("Flock Mortality Detail", [
		f("reason", "Reason", "Link", options="Mortality Reason", in_list_view=1, columns=3),
		f("qty", "Qty", "Int", in_list_view=1, columns=1),
		f("sex", "Sex", "Select", options="\nMale\nFemale", in_list_view=1, columns=1),
		f("remarks", "Remarks", in_list_view=1, columns=4),
	], child=True)

	make("Flock Feed Detail", [
		f("feed_type", "Feed Type", "Link", options="Feed Type", in_list_view=1, columns=2),
		f("item", "Item", "Link", options="Item", in_list_view=1, columns=2),
		f("bags", "Bags", "Float", in_list_view=1, columns=1),
		f("bag_weight_kg", "Bag Wt (kg)", "Float", in_list_view=1, columns=1),
		f("qty_kg", "Qty (kg)", "Float", read_only=1, in_list_view=1, columns=1),
		f("warehouse", "Warehouse", "Link", options="Warehouse", in_list_view=1, columns=2),
	], child=True)

	make("Flock Egg Detail", [
		f("egg_grade", "Grade", "Link", options="Egg Grade", in_list_view=1, columns=2),
		f("item", "Item", "Link", options="Item", in_list_view=1, columns=2),
		f("trays", "Trays", "Float", in_list_view=1, columns=1),
		f("qty", "Eggs", "Int", read_only=1, in_list_view=1, columns=2),
		f("warehouse", "Warehouse", "Link", options="Warehouse", in_list_view=1, columns=2),
	], child=True)

	make("Daily Flock Entry", [
		series("DFE-.YYYY.-.#####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, in_list_view=1, in_standard_filter=1),
		f("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("age_days", "Age (days)", "Int", read_only=1, in_list_view=1),
		cb("cb1"),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1,
		  in_standard_filter=1),
		f("shed", "Shed", "Link", options="Shed", fetch_from="flock.shed", read_only=1),
		f("company", "Company", "Link", options="Company", fetch_from="flock.company", read_only=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, fetch_from="flock.flock_type",
		  read_only=1),
		f("entry_source", "Entry Source", "Select",
		  options="Desk\nField App\nBot\nIVR\nCatch-up", default="Desk"),

		sb("sec_birds", "Bird Count"),
		f("opening_qty", "Opening Qty", "Int", read_only=1),
		f("mortality_qty", "Mortality", "Int", in_list_view=1),
		f("cull_qty", "Culls", "Int"),
		cb("cb2"),
		f("closing_qty", "Closing Qty", "Int", read_only=1),
		f("mortality_pct_today", "Mortality % Today", "Percent", read_only=1, precision="3"),
		f("cumulative_mortality_pct", "Cumulative Mortality %", "Percent", read_only=1),
		sb("sec_mort_detail", "Mortality Detail"),
		f("mortality_details", "Mortality Details", "Table", options="Flock Mortality Detail"),

		sb("sec_feed", "Feed"),
		f("feed_details", "Feed", "Table", options="Flock Feed Detail"),
		f("total_feed_kg", "Total Feed (kg)", "Float", read_only=1, in_list_view=1),
		cb("cb3"),
		f("cumulative_feed_kg", "Cumulative Feed (kg)", "Float", read_only=1),
		f("feed_per_bird_g", "Feed per Bird (g)", "Float", read_only=1, precision="1"),

		sb("sec_water", "Water and Weight"),
		f("water_litres", "Water (litres)", "Float"),
		f("water_feed_ratio", "Water : Feed", "Float", read_only=1, precision="2"),
		cb("cb4"),
		f("avg_body_weight_g", "Avg Body Weight (g)", "Float"),
		f("sample_size", "Sample Size", "Int"),
		f("uniformity_pct", "Uniformity %", "Percent"),

		sb("sec_eggs", "Eggs"),
		f("egg_details", "Eggs", "Table", options="Flock Egg Detail"),
		f("total_eggs", "Total Eggs", "Int", read_only=1, in_list_view=1),
		f("floor_eggs", "Floor Eggs", "Int"),
		cb("cb5"),
		f("hd_production_pct", "HD Production %", "Percent", read_only=1),
		f("avg_egg_weight_g", "Avg Egg Weight (g)", "Float"),

		sb("sec_env", "Environment", collapsible=1),
		f("min_temp", "Min Temp (C)", "Float"),
		f("max_temp", "Max Temp (C)", "Float"),
		f("humidity_pct", "Humidity %", "Percent"),
		cb("cb6"),
		f("litter_condition", "Litter Condition", "Select", options="\nDry\nFriable\nDamp\nWet\nCaked"),
		f("light_hours", "Light Hours", "Float"),

		sb("sec_notes", "Notes and Alerts"),
		f("has_alert", "Has Alert", "Check", read_only=1, in_list_view=1),
		f("alert_message", "Alert Message", "Small Text", read_only=1, depends_on="has_alert"),
		f("remarks", "Remarks", "Small Text"),

		sb("sec_ref", "References", collapsible=1),
		f("feed_stock_entry", "Feed Stock Entry", "Link", options="Stock Entry", read_only=1),
		f("mortality_stock_entry", "Mortality Stock Entry", "Link", options="Stock Entry", read_only=1),
		cb("cb7"),
		f("egg_stock_entry", "Egg Stock Entry", "Link", options="Stock Entry", read_only=1),
		amended("Daily Flock Entry"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date",
		search_fields="flock,posting_date,farm")

	make("Bird Weighing", [
		series("BWG-.YYYY.-.####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, in_list_view=1),
		f("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("age_days", "Age (days)", "Int", read_only=1, in_list_view=1),
		cb("cb1"),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1),
		f("shed", "Shed", "Link", options="Shed", fetch_from="flock.shed", read_only=1),
		f("company", "Company", "Link", options="Company", fetch_from="flock.company", read_only=1),
		sb("sec_sample", "Sample"),
		f("sample_size", "Birds Weighed", "Int", reqd=1),
		f("total_weight_g", "Total Weight (g)", "Float", reqd=1),
		f("uniformity_pct", "Uniformity %", "Percent"),
		cb("cb2"),
		f("avg_body_weight_g", "Avg Body Weight (g)", "Float", read_only=1, in_list_view=1),
		f("cv_pct", "CV %", "Float", precision="1"),
		sb("sec_var", "Versus Standard"),
		f("std_body_weight_g", "Standard Weight (g)", "Float", read_only=1),
		cb("cb3"),
		f("variance_pct", "Variance %", "Percent", read_only=1, in_list_view=1),
		sb("sec_notes"),
		f("remarks", "Remarks", "Small Text"),
		amended("Bird Weighing"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")

	make("Flock Closure", [
		series("FCL-.YYYY.-.####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, in_list_view=1),
		f("closure_date", "Closure Date", "Date", reqd=1, default="Today", in_list_view=1),
		cb("cb1"),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1),
		f("shed", "Shed", "Link", options="Shed", fetch_from="flock.shed", read_only=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, fetch_from="flock.flock_type",
		  read_only=1),
		f("company", "Company", "Link", options="Company", fetch_from="flock.company", read_only=1),

		sb("sec_counts", "Final Counts"),
		f("placed_qty", "Placed Qty", "Int", read_only=1),
		f("total_mortality", "Total Mortality", "Int", read_only=1),
		f("total_culls", "Total Culls", "Int", read_only=1),
		cb("cb2"),
		f("total_sold", "Total Sold / Depleted", "Int", read_only=1),
		f("livability_pct", "Livability %", "Percent", read_only=1, in_list_view=1),
		f("age_days", "Age at Closure (days)", "Int", read_only=1),

		sb("sec_perf", "Performance"),
		f("cumulative_feed_kg", "Total Feed (kg)", "Float", read_only=1),
		f("total_live_weight_kg", "Live Weight Sold (kg)", "Float"),
		f("avg_sale_weight_kg", "Avg Sale Weight (kg)", "Float", read_only=1, precision="3"),
		cb("cb3"),
		f("fcr", "FCR", "Float", precision="3", read_only=1, in_list_view=1),
		f("adg_g", "ADG (g/day)", "Float", precision="1", read_only=1),
		f("eef", "EEF", "Float", precision="1", read_only=1, in_list_view=1),
		f("cumulative_eggs", "Total Eggs", "Int", read_only=1),

		sb("sec_money", "Settlement"),
		f("total_cost", "Total Cost", "Currency", read_only=1),
		f("cost_per_bird", "Cost per Bird", "Currency", read_only=1),
		f("cost_per_kg_live", "Cost per kg Live", "Currency", read_only=1),
		cb("cb4"),
		f("total_revenue", "Total Revenue", "Currency"),
		f("margin", "Margin", "Currency", read_only=1),
		sb("sec_notes"),
		f("remarks", "Remarks", "Small Text"),
		amended("Flock Closure"),
	], submittable=True, autoname="naming_series:", sort_field="closure_date")


# ---------------------------------------------------------------- health
def build_health():
	make("Vaccination Schedule Detail", [
		f("age_days", "Age (days)", "Int", in_list_view=1, columns=1),
		f("vaccine", "Vaccine", "Link", options="Vaccine", in_list_view=1, columns=3),
		f("route", "Route", "Select", options=ROUTES, in_list_view=1, columns=2),
		f("dose_per_bird", "Dose", "Float", in_list_view=1, columns=1),
		f("is_mandatory", "Mandatory", "Check", in_list_view=1, columns=1),
		f("remarks", "Remarks", in_list_view=1, columns=2),
	], child=True)

	make("Vaccination Schedule Template", [
		f("template_name", "Template Name", reqd=1, unique=1, in_list_view=1),
		f("strain", "Strain", "Link", options="Strain", in_list_view=1),
		f("flock_type", "Flock Type", "Select", options=FLOCK_TYPES, in_list_view=1),
		cb("cb1"),
		f("is_default", "Is Default", "Check", in_list_view=1),
		f("region", "Region"),
		sb("sec_detail", "Schedule"),
		f("schedule_details", "Schedule", "Table", options="Vaccination Schedule Detail"),
	], autoname="field:template_name", master=True)

	make("Vaccination Entry", [
		series("VAC-.YYYY.-.#####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, in_list_view=1),
		f("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("age_days", "Age (days)", "Int", read_only=1, in_list_view=1),
		cb("cb1"),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1),
		f("shed", "Shed", "Link", options="Shed", fetch_from="flock.shed", read_only=1),
		f("company", "Company", "Link", options="Company", fetch_from="flock.company", read_only=1),
		sb("sec_vac", "Vaccine"),
		f("vaccine", "Vaccine", "Link", options="Vaccine", reqd=1, in_list_view=1),
		f("route", "Route", "Select", options=ROUTES),
		f("dose_per_bird", "Dose per Bird", "Float", default="1"),
		f("birds_covered", "Birds Covered", "Int"),
		cb("cb2"),
		f("vial_batch", "Vial Batch No", description="Traceability - required on audit"),
		f("vial_serial", "Vial Serial No"),
		f("diluent", "Diluent"),
		f("wastage_pct", "Wastage %", "Percent"),
		sb("sec_notes"),
		f("operator", "Operator"),
		f("remarks", "Remarks", "Small Text"),
		amended("Vaccination Entry"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")

	make("Flock Vaccination Plan Detail", [
		f("age_days", "Age (days)", "Int", in_list_view=1, columns=1),
		f("due_date", "Due Date", "Date", in_list_view=1, columns=2),
		f("vaccine", "Vaccine", "Link", options="Vaccine", in_list_view=1, columns=2),
		f("route", "Route", "Select", options=ROUTES, columns=2),
		f("dose_per_bird", "Dose", "Float"),
		f("is_mandatory", "Mandatory", "Check"),
		f("status", "Status", "Select", options="Pending\nDone\nOverdue\nSkipped", default="Pending",
		  in_list_view=1, columns=1),
		f("done_on", "Done On", "Date", in_list_view=1, columns=2),
		f("vaccination_entry", "Vaccination Entry", "Link", options="Vaccination Entry", read_only=1),
	], child=True)

	make("Flock Vaccination Plan", [
		series("FVP-.YYYY.-.####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, unique=1, in_list_view=1),
		f("template", "Template", "Link", options="Vaccination Schedule Template", in_list_view=1),
		cb("cb1"),
		f("placement_date", "Placement Date", "Date", read_only=1),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1, in_list_view=1),
		f("pending_count", "Pending", "Int", read_only=1, in_list_view=1),
		f("overdue_count", "Overdue", "Int", read_only=1, in_list_view=1),
		sb("sec_plan", "Plan"),
		f("plan_details", "Plan", "Table", options="Flock Vaccination Plan Detail"),
	], autoname="naming_series:")

	make("Medication Entry", [
		series("MED-.YYYY.-.#####"),
		f("flock", "Flock", "Link", options="Flock", reqd=1, in_list_view=1),
		f("medication", "Medication", "Link", options="Poultry Medication", reqd=1, in_list_view=1),
		f("start_date", "Start Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("end_date", "End Date", "Date", reqd=1),
		cb("cb1"),
		f("farm", "Farm", "Link", options="Farm", fetch_from="flock.farm", read_only=1),
		f("company", "Company", "Link", options="Company", fetch_from="flock.company", read_only=1),
		f("withdrawal_days", "Withdrawal Days", "Int"),
		f("withdrawal_clear_date", "Withdrawal Clear Date", "Date", read_only=1, in_list_view=1,
		  description="Birds and eggs from this flock cannot be sold before this date"),
		sb("sec_dose", "Treatment"),
		f("dose", "Dose"),
		f("route", "Route", "Select", options="\nDrinking Water\nFeed\nInjection\nSpray"),
		f("birds_treated", "Birds Treated", "Int"),
		cb("cb2"),
		f("reason", "Reason"),
		f("prescriber", "Prescribed By"),
		sb("sec_notes"),
		f("remarks", "Remarks", "Small Text"),
		amended("Medication Entry"),
	], submittable=True, autoname="naming_series:", sort_field="start_date")


def run():
	# NOTE: never set frappe.flags.in_import here. It suppresses export_doc() /
	# make_controller_template() while run_module_method("on_doctype_update")
	# still fires, so the import of a controller that was never written fails.
	print("--- roles ---")
	build_roles()
	print("--- masters ---")
	build_masters()
	print("--- flock ---")
	build_flock()
	print("--- health ---")
	build_health()
	frappe.db.commit()
	made = frappe.get_all("DocType", filters={"module": MODULE}, pluck="name")
	print("TOTAL DOCTYPES:", len(made))
	for m in sorted(made):
		print("   -", m)


# alias used by poultry.setup.after_install
install = run
