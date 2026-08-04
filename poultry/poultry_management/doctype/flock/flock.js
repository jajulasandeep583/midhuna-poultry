// Copyright (c) 2026, Midhuna Tech and contributors
// For license information, please see license.txt

// The two lifecycle actions live on the server (flock.py). This form wires
// them to buttons — without it a user has no way to place or close a flock.

frappe.ui.form.on("Flock", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Place Flock"), () => {
				frappe.confirm(
					__(
						"Place {0} birds in {1}?<br><br>This creates the batch, snapshots the breed standard, opens the costing project, generates the vaccination plan, marks the shed occupied and receives the chicks into stock.",
						[cstr(frm.doc.opening_qty), frappe.utils.escape_html(frm.doc.shed || "")]
					),
					() => {
						frappe.call({
							method: "poultry.poultry_management.doctype.flock.flock.place_flock",
							args: { flock_name: frm.doc.name },
							freeze: true,
							freeze_message: __("Placing flock..."),
							callback: () => frm.reload_doc(),
						});
					}
				);
			}).addClass("btn-primary");
		}

		if (["Placed", "Growing", "Laying", "Depleting"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Close Flock"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Close Flock {0}", [frm.doc.name]),
					fields: [
						{
							fieldname: "closure_date",
							fieldtype: "Date",
							label: __("Closure Date"),
							default: frappe.datetime.get_today(),
							reqd: 1,
						},
						{
							fieldname: "total_live_weight_kg",
							fieldtype: "Float",
							label: __("Total Live Weight Sold (kg)"),
							description: __("Broilers: the weighbridge total for the lifted batch."),
						},
						{
							fieldname: "total_revenue",
							fieldtype: "Currency",
							label: __("Total Revenue"),
							description: __("Everything the flock earned, if not already on sales invoices."),
						},
					],
					primary_action_label: __("Close Flock"),
					primary_action(values) {
						d.hide();
						frappe.call({
							method: "poultry.poultry_management.doctype.flock.flock.close_flock",
							args: { flock_name: frm.doc.name, ...values },
							freeze: true,
							freeze_message: __("Closing flock..."),
							callback: () => frm.reload_doc(),
						});
					},
				});
				d.show();
			});

			frm.add_custom_button(__("Flock 360"), () => {
				frappe.route_options = { flock: frm.doc.name };
				frappe.set_route("poultry-flock-360");
			});
		}
	},
});
