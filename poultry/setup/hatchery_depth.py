"""Hatchery, deepened to how it is actually run in the AP/Telangana belt.

A commercial hatchery there does far more than set and pull. Eggs arrive from
breeder farms and are graded and fumigated on arrival; they age in a cold store
where hatchability falls roughly a percent a day past the first week; they are
pre-warmed before setting; setter and hatcher run different temperature and
humidity regimes; and after take-off the unhatched eggs are broken out and
classified, because that breakout is the only thing that tells you whether a
poor hatch was the breeder flock's fault or the machine's.

This adds the parts that were missing: egg receipt and grading, a chick type
master, incubation parameters, chick grading, and breakout analysis.
"""

import frappe

MODULE = "Poultry Management"
from poultry.setup.schema import amended, cb, f, make, sb, series  # noqa: E402

EGG_TYPES = "\nBroiler Hatching Egg\nLayer Hatching Egg\nDesi / Native Hatching Egg\nBreeder Hatching Egg"


def build():
	# ---------------------------------------------------------------- masters
	make("Chick Type", [
		f("chick_type_name", "Chick Type", reqd=1, unique=1, in_list_view=1),
		f("category", "Category", "Select",
		  options="\nBroiler\nLayer\nDesi / Native\nBreeder", reqd=1, in_list_view=1),
		f("strain", "Strain", "Link", options="Strain", in_list_view=1),
		cb("cb1"),
		f("chick_item", "Chick Item", "Link", options="Item"),
		f("egg_item", "Hatching Egg Item", "Link", options="Item"),
		f("is_sexed", "Sexed at Hatchery", "Check",
		  description="Layer chicks are sexed; broilers are usually sold straight run"),
		sb("sec_std", "Expected Performance"),
		f("std_fertility_pct", "Standard Fertility %", "Percent", default="93"),
		f("std_hatchability_pct", "Standard Hatch of Set %", "Percent", default="84"),
		cb("cb2"),
		f("std_chick_weight_g", "Standard Chick Weight (g)", "Float", default="40"),
		f("incubation_days", "Incubation Days", "Int", default="21"),
	], autoname="field:chick_type_name", master=True)

	# ---------------------------------------------------------------- receipt
	make("Hatching Egg Receipt", [
		series("HER-.YYYY.-.####"),
		f("posting_date", "Receipt Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("supplier", "Breeder Farm / Supplier", "Link", options="Supplier", in_list_view=1),
		f("source_flock", "Source Breeder Flock", "Link", options="Flock",
		  description="Where the eggs came from - drives breeder age on the setting"),
		cb("cb1"),
		f("chick_type", "Chick Type", "Link", options="Chick Type", reqd=1, in_list_view=1),
		f("egg_type", "Egg Type", "Select", options=EGG_TYPES),
		f("company", "Company", "Link", options="Company"),
		f("breeder_age_weeks", "Breeder Age (weeks)", "Float"),

		sb("sec_qty", "Grading on Arrival"),
		f("eggs_received", "Eggs Received", "Int", reqd=1, in_list_view=1),
		f("cracked_eggs", "Cracked / Hairline", "Int"),
		f("dirty_eggs", "Dirty / Stained", "Int"),
		cb("cb2"),
		f("small_eggs", "Undersized", "Int"),
		f("misshapen_eggs", "Misshapen / Double Yolk", "Int"),
		f("settable_eggs", "Settable Eggs", "Int", read_only=1, in_list_view=1),
		f("settable_pct", "Settable %", "Percent", read_only=1),

		sb("sec_handling", "Handling"),
		f("fumigated", "Fumigated on Arrival", "Check", default="1",
		  description="Formaldehyde and potassium permanganate, standard practice"),
		f("fumigation_time", "Fumigation Time", "Datetime"),
		f("avg_egg_weight_g", "Avg Egg Weight (g)", "Float"),
		cb("cb3"),
		f("store_room", "Egg Store", "Data", default="Cold Store 1"),
		f("store_temp_c", "Store Temp (C)", "Float", default="17.5"),
		f("store_humidity_pct", "Store Humidity %", "Percent", default="75"),

		sb("sec_status", "Status"),
		f("eggs_set", "Eggs Set from this Receipt", "Int", read_only=1),
		f("eggs_in_store", "Still in Store", "Int", read_only=1, in_list_view=1),
		cb("cb4"),
		f("storage_days", "Days in Store", "Int", read_only=1,
		  description="Hatchability falls about a point a day past the first week"),
		f("remarks", "Remarks", "Small Text"),
		amended("Hatching Egg Receipt"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date",
		search_fields="supplier,chick_type,posting_date")

	# ---------------------------------------------------------------- breakout
	make("Breakout Analysis", [
		series("BRK-.YYYY.-.####"),
		f("egg_setting", "Egg Setting", "Link", options="Egg Setting", reqd=1, in_list_view=1),
		f("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		cb("cb1"),
		f("eggs_broken", "Eggs Broken Out", "Int", reqd=1,
		  description="The unhatched residue, opened and classified"),
		f("company", "Company", "Link", options="Company", read_only=1),

		sb("sec_class", "Classification"),
		f("infertile", "Infertile (true clears)", "Int",
		  description="Blames the breeder flock, not the machine"),
		f("early_dead", "Early Dead (day 1-7)", "Int"),
		f("mid_dead", "Mid Dead (day 8-14)", "Int"),
		cb("cb2"),
		f("late_dead", "Late Dead (day 15-18)", "Int"),
		f("pipped_not_hatched", "Pipped, Not Hatched", "Int",
		  description="Usually humidity or ventilation in the hatcher"),
		f("contaminated", "Contaminated / Exploders", "Int"),
		f("malpositioned", "Malpositioned", "Int"),

		sb("sec_pct", "Percentages"),
		f("infertile_pct", "Infertile %", "Percent", read_only=1, in_list_view=1),
		f("early_dead_pct", "Early Dead %", "Percent", read_only=1),
		cb("cb3"),
		f("late_dead_pct", "Late Dead %", "Percent", read_only=1),
		f("contamination_pct", "Contamination %", "Percent", read_only=1),

		sb("sec_find", "Reading"),
		f("likely_cause", "Likely Cause", "Select",
		  options="\nBreeder flock fertility\nEgg storage / age\nSetter temperature\n"
		          "Hatcher humidity\nTurning\nEgg handling / cracks\nContamination / hygiene\n"
		          "Nutrition of breeders\nInconclusive", read_only=1, in_list_view=1),
		f("remarks", "Remarks", "Small Text"),
		amended("Breakout Analysis"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")


def extend():
	"""Add the incubation and chick-grading fields the first pass left out."""
	extra = {
		"Egg Setting": [
			("sec_incub", {"fieldtype": "Section Break", "label": "Incubation"}),
			("egg_receipt", {"fieldtype": "Link", "options": "Hatching Egg Receipt",
			                 "label": "Egg Receipt"}),
			("chick_type", {"fieldtype": "Link", "options": "Chick Type", "label": "Chick Type"}),
			("prewarm_hours", {"fieldtype": "Float", "label": "Pre-warm Hours",
			                   "default": "8",
			                   "description": "6-12 hours at about 25 C before setting"}),
			("cb_incub", {"fieldtype": "Column Break"}),
			("setter_temp_c", {"fieldtype": "Float", "label": "Setter Temp (C)",
			                   "default": "37.6"}),
			("setter_humidity_pct", {"fieldtype": "Percent", "label": "Setter Humidity %",
			                         "default": "55"}),
			("turning_per_day", {"fieldtype": "Int", "label": "Turns per Day", "default": "24"}),
		],
		"Hatch Entry": [
			("sec_chick", {"fieldtype": "Section Break", "label": "Chick Quality"}),
			("grade_a_chicks", {"fieldtype": "Int", "label": "Grade A Chicks"}),
			("grade_b_chicks", {"fieldtype": "Int", "label": "Grade B Chicks"}),
			("cb_chick", {"fieldtype": "Column Break"}),
			("hatcher_temp_c", {"fieldtype": "Float", "label": "Hatcher Temp (C)",
			                    "default": "37.0"}),
			("hatcher_humidity_pct", {"fieldtype": "Percent", "label": "Hatcher Humidity %",
			                          "default": "68"}),
			("chick_yield_pct", {"fieldtype": "Percent", "label": "Chick : Egg Weight %",
			                     "read_only": 1,
			                     "description": "A good chick is 67-70% of the egg it came from"}),
		],
		"Chick Dispatch": [
			("sec_transit", {"fieldtype": "Section Break", "label": "Transit"}),
			("driver_name", {"fieldtype": "Data", "label": "Driver"}),
			("dispatch_time", {"fieldtype": "Datetime", "label": "Dispatch Time"}),
			("cb_transit", {"fieldtype": "Column Break"}),
			("transit_hours", {"fieldtype": "Float", "label": "Transit Hours"}),
			("doa_chicks", {"fieldtype": "Int", "label": "Dead on Arrival"}),
			("doa_pct", {"fieldtype": "Percent", "label": "DOA %", "read_only": 1}),
		],
	}

	for dt, fields in extra.items():
		if not frappe.db.exists("DocType", dt):
			continue
		doc = frappe.get_doc("DocType", dt)
		have = {d.fieldname for d in doc.fields}
		added = 0
		for fieldname, props in fields:
			if fieldname in have:
				continue
			row = {"fieldname": fieldname, "label": props.get("label", "")}
			row.update(props)
			doc.append("fields", row)
			added += 1
		if added:
			doc.flags.ignore_permissions = True
			doc.save()
			print(f"  + {dt}: {added} fields")


def run():
	build()
	extend()
	frappe.db.commit()
	print("HATCHERY DEPTH DONE")
