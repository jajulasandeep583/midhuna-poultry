"""Module 6 - Hatchery (design doc §5.8).

Setting -> candling -> transfer -> hatch -> dispatch, with the three numbers the
industry manages on: fertility %, hatchability of set and hatchability of
fertile. Breeder age at set is recorded on every setting because it is the
standard explanation for hatchability variation.
"""

import frappe

MODULE = "Poultry Management"
from poultry.setup.schema import amended, cb, f, make, sb, series  # noqa: E402


def build():
	make("Hatchery Machine", [
		f("machine_name", "Machine Name", reqd=1, unique=1, in_list_view=1),
		f("machine_type", "Type", "Select", options="\nSetter\nHatcher\nCombi", reqd=1,
		  in_list_view=1),
		f("capacity_eggs", "Capacity (eggs)", "Int", reqd=1, in_list_view=1),
		cb("cb1"),
		f("trays", "Trays", "Int"),
		f("stage_type", "Stage", "Select", options="\nSingle Stage\nMulti Stage"),
		f("company", "Company", "Link", options="Company"),
		f("disabled", "Disabled", "Check"),
	], autoname="field:machine_name", master=True)

	make("Egg Setting", [
		series("SET-.YYYY.-.####"),
		f("set_date", "Set Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("source_flock", "Source Flock", "Link", options="Flock", in_list_view=1,
		  description="Breeder or layer flock the hatching eggs came from"),
		f("breeder_age_weeks", "Breeder Age (weeks)", "Float",
		  description="The standard explanation for hatchability variation"),
		cb("cb1"),
		f("setter", "Setter", "Link", options="Hatchery Machine", reqd=1),
		f("company", "Company", "Link", options="Company"),
		f("egg_item", "Hatching Egg Item", "Link", options="Item"),

		sb("sec_qty", "Eggs"),
		f("eggs_set", "Eggs Set", "Int", reqd=1, in_list_view=1),
		f("egg_age_days", "Egg Age at Set (days)", "Int"),
		cb("cb2"),
		f("storage_temp_c", "Storage Temp (C)", "Float"),

		sb("sec_dates", "Derived Dates"),
		f("candling_date", "Candling Due", "Date", read_only=1),
		f("transfer_date", "Transfer Due", "Date", read_only=1),
		cb("cb3"),
		f("hatch_date", "Hatch Due", "Date", read_only=1, in_list_view=1),

		sb("sec_res", "Result"),
		f("fertile_eggs", "Fertile Eggs", "Int", read_only=1),
		f("fertility_pct", "Fertility %", "Percent", read_only=1, in_list_view=1),
		cb("cb4"),
		f("chicks_hatched", "Chicks Hatched", "Int", read_only=1),
		f("hatchability_set_pct", "Hatchability of Set %", "Percent", read_only=1),
		f("hatchability_fertile_pct", "Hatchability of Fertile %", "Percent", read_only=1),
		f("status", "Status", "Select", options="Set\nCandled\nTransferred\nHatched",
		  default="Set", read_only=1, in_standard_filter=1),
		sb("sec_notes"),
		f("remarks", "Remarks", "Small Text"),
		amended("Egg Setting"),
	], submittable=True, autoname="naming_series:", sort_field="set_date",
		search_fields="source_flock,setter,set_date")

	make("Candling Entry", [
		series("CAN-.YYYY.-.####"),
		f("egg_setting", "Egg Setting", "Link", options="Egg Setting", reqd=1, in_list_view=1),
		f("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		cb("cb1"),
		f("eggs_set", "Eggs Set", "Int", read_only=1, fetch_from="egg_setting.eggs_set"),
		f("company", "Company", "Link", options="Company", read_only=1),
		sb("sec_counts", "Candling Result"),
		f("clear_eggs", "Clear (infertile)", "Int"),
		f("dead_germ", "Dead Germ", "Int"),
		cb("cb2"),
		f("contaminated", "Contaminated / Rots", "Int"),
		f("fertile_eggs", "Fertile Eggs", "Int", read_only=1, in_list_view=1),
		f("fertility_pct", "Fertility %", "Percent", read_only=1, in_list_view=1),
		sb("sec_notes"),
		f("remarks", "Remarks", "Small Text"),
		amended("Candling Entry"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")

	make("Hatch Entry", [
		series("HTC-.YYYY.-.####"),
		f("egg_setting", "Egg Setting", "Link", options="Egg Setting", reqd=1, in_list_view=1),
		f("posting_date", "Hatch Date", "Date", reqd=1, default="Today", in_list_view=1),
		cb("cb1"),
		f("hatcher", "Hatcher", "Link", options="Hatchery Machine"),
		f("eggs_set", "Eggs Set", "Int", read_only=1, fetch_from="egg_setting.eggs_set"),
		f("fertile_eggs", "Fertile Eggs", "Int", read_only=1,
		  fetch_from="egg_setting.fertile_eggs"),
		f("company", "Company", "Link", options="Company", read_only=1),

		sb("sec_out", "Hatch Result"),
		f("chicks_hatched", "Chicks Hatched", "Int", reqd=1, in_list_view=1),
		f("saleable_chicks", "Saleable Chicks", "Int"),
		f("cripples", "Cripples / Culls", "Int"),
		cb("cb2"),
		f("dead_in_shell", "Dead in Shell", "Int", read_only=1),
		f("chick_item", "Chick Item", "Link", options="Item"),
		f("warehouse", "Receive Into", "Link", options="Warehouse"),

		sb("sec_kpi", "Performance"),
		f("hatchability_set_pct", "Hatchability of Set %", "Percent", read_only=1,
		  in_list_view=1),
		f("hatchability_fertile_pct", "Hatchability of Fertile %", "Percent", read_only=1),
		cb("cb3"),
		f("saleable_pct", "Saleable Chick %", "Percent", read_only=1),
		f("avg_chick_weight_g", "Avg Chick Weight (g)", "Float"),

		sb("sec_ref", "References", collapsible=1),
		f("stock_entry", "Stock Entry", "Link", options="Stock Entry", read_only=1),
		f("remarks", "Remarks", "Small Text"),
		amended("Hatch Entry"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")

	make("Chick Dispatch", [
		series("CHD-.YYYY.-.####"),
		f("hatch_entry", "Hatch Entry", "Link", options="Hatch Entry", reqd=1, in_list_view=1),
		f("posting_date", "Dispatch Date", "Date", reqd=1, default="Today", in_list_view=1),
		f("destination_type", "Destination", "Select",
		  options="\nOwn Farm\nCustomer", default="Own Farm", in_list_view=1),
		cb("cb1"),
		f("customer", "Customer", "Link", options="Customer",
		  depends_on="eval:doc.destination_type=='Customer'"),
		f("to_farm", "To Farm", "Link", options="Farm",
		  depends_on="eval:doc.destination_type=='Own Farm'"),
		f("company", "Company", "Link", options="Company", read_only=1),

		sb("sec_qty", "Load"),
		f("boxes", "Boxes", "Int"),
		f("chicks_per_box", "Chicks per Box", "Int", default="100"),
		f("extras", "Extras", "Int"),
		cb("cb2"),
		f("chicks_dispatched", "Chicks Dispatched", "Int", read_only=1, in_list_view=1),
		f("transit_temp_c", "Transit Temp (C)", "Float"),
		f("in_ovo_vaccinated", "In-Ovo / Hatchery Vaccinated", "Check"),
		sb("sec_notes"),
		f("vehicle_no", "Vehicle No"),
		f("remarks", "Remarks", "Small Text"),
		amended("Chick Dispatch"),
	], submittable=True, autoname="naming_series:", sort_field="posting_date")


def run():
	build()
	frappe.db.commit()
	made = [d for d in frappe.get_all("DocType", filters={"module": MODULE}, pluck="name")
	        if d in ("Hatchery Machine", "Egg Setting", "Candling Entry", "Hatch Entry",
	                 "Chick Dispatch")]
	print("HATCHERY DOCTYPES:", len(made), sorted(made))
