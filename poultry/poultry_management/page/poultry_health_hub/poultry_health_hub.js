frappe.pages["poultry-health-hub"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Vaccination & Health"),
		single_column: true,
	});
	wrapper.health_hub = new HealthHub(page);
};

frappe.pages["poultry-health-hub"].on_page_show = function (wrapper) {
	wrapper.health_hub && wrapper.health_hub.load();
};

class HealthHub {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="hh"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.page.add_menu_item(__("Record a Vaccination"), () =>
			frappe.new_doc("Vaccination Entry"));
		this.page.add_menu_item(__("Record a Medication"), () =>
			frappe.new_doc("Medication Entry"));
		this.load();
	}

	inject_styles() {
		if (document.getElementById("hh-styles")) return;
		$(`<style id="hh-styles">
		.hh { padding-bottom: 2.5rem; }
		.hh .icon { margin: 0; flex: none; }
		.hh-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(184px, 1fr));
			gap: 12px; margin-bottom: 1.5rem; }
		.hh-kpi { border-radius: var(--border-radius-md); padding: 14px 16px; color: #fff;
			position: relative; overflow: hidden; }
		.hh-kpi .l { font-size: var(--text-xs); text-transform: uppercase;
			letter-spacing: .05em; opacity: .85; }
		.hh-kpi .v { font-size: 26px; font-weight: 700; line-height: 1.15; margin-top: 4px;
			white-space: nowrap; }
		.hh-kpi .s { font-size: var(--text-xs); opacity: .85; margin-top: 2px; }
		.hh-kpi .bg { position: absolute; right: -8px; bottom: -10px; opacity: .18; }
		.hh-kpi .bg .icon { width: 74px; height: 74px; stroke: #fff !important; }
		.hh-red   { background: linear-gradient(135deg,#E24C4C,#C0392B); }
		.hh-amber { background: linear-gradient(135deg,#E8A33D,#D9822B); }
		.hh-teal  { background: linear-gradient(135deg,#17B897,#0E9F85); }
		.hh-blue  { background: linear-gradient(135deg,#5B8DEF,#4178D4); }
		.hh-slate { background: linear-gradient(135deg,#6B7A8F,#4B6A88); }
		.hh-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
		@media (max-width: 1000px) { .hh-grid { grid-template-columns: 1fr; } }
		.hh-card { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); overflow: hidden; margin-bottom: 16px; }
		.hh-card h5 { display: flex; align-items: center; gap: 8px; margin: 0;
			padding: 13px 16px; font-size: var(--text-md); font-weight: 600;
			border-bottom: 1px solid var(--border-color); }
		.hh-card h5 .pill { margin-left: auto; font-size: 11px; font-weight: 600;
			padding: 2px 9px; border-radius: 10px; background: var(--bg-light-gray);
			color: var(--text-muted); }
		.hh-card h5 .pill.bad { background: var(--red-100); color: var(--red-600); }
		.hh-card h5 .pill.warn { background: var(--orange-100); color: var(--orange-600); }
		.hh-card h5 .pill.ok { background: var(--green-100); color: var(--green-700); }
		.hh-row { display: flex; align-items: center; gap: 10px; padding: 10px 16px;
			border-bottom: 1px solid var(--border-color); cursor: pointer;
			font-size: var(--text-sm); }
		.hh-row:last-child { border-bottom: 0; }
		.hh-row:hover { background: var(--bg-light-gray); }
		.hh-row .main { flex: 1; min-width: 0; }
		.hh-row .t { font-weight: 600; color: var(--text-color); white-space: nowrap;
			overflow: hidden; text-overflow: ellipsis; }
		.hh-row .s { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap;
			overflow: hidden; text-overflow: ellipsis; }
		.hh-tag { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 10px;
			white-space: nowrap; }
		.hh-tag.late { background: var(--red-100); color: var(--red-600); }
		.hh-tag.today { background: var(--orange-100); color: var(--orange-600); }
		.hh-tag.soon { background: var(--blue-100); color: var(--blue-600); }
		.hh-tag.hold { background: var(--red-100); color: var(--red-600); }
		.hh-empty { padding: 26px 16px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		.hh-bar { height: 7px; border-radius: 4px; background: var(--bg-light-gray);
			overflow: hidden; margin-top: 5px; }
		.hh-bar i { display: block; height: 100%; background: var(--red-400); }
		.hh-reason { padding: 10px 16px; border-bottom: 1px solid var(--border-color); }
		.hh-reason:last-child { border-bottom: 0; }
		.hh-reason .top { display: flex; justify-content: space-between;
			font-size: var(--text-sm); }
		.hh-reason .top b { font-variant-numeric: tabular-nums; }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.health_hub" }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data, t = d.totals;
		this.$body.empty();

		const kpis = [
			{ cls: "hh-red", icon: "poultry-schedule", l: __("Overdue"), v: t.overdue,
			  s: __("doses past their date") },
			{ cls: "hh-amber", icon: "poultry-syringe", l: __("Due Today"), v: t.due_today,
			  s: __("give these today") },
			{ cls: "hh-blue", icon: "poultry-schedule", l: __("Next 7 Days"), v: t.due_soon,
			  s: __("plan the vials") },
			{ cls: "hh-teal", icon: "poultry-target", l: __("Compliance"),
			  v: `${t.compliance_pct}%`, s: __("planned doses done") },
			{ cls: "hh-slate", icon: "poultry-withdrawal", l: __("Under Withdrawal"),
			  v: t.under_withdrawal,
			  s: __("{0} birds cannot be sold", [Number(t.birds_blocked).toLocaleString("en-IN")]) },
		];
		const $k = $('<div class="hh-kpis"></div>').appendTo(this.$body);
		kpis.forEach((k) =>
			$(`<div class="hh-kpi ${k.cls}">
				<div class="l">${k.l}</div><div class="v">${k.v}</div><div class="s">${k.s}</div>
				<div class="bg">${frappe.utils.icon(k.icon, "lg")}</div>
			</div>`).appendTo($k)
		);

		const $g = $('<div class="hh-grid"></div>').appendTo(this.$body);
		const $l = $("<div></div>").appendTo($g);
		const $r = $("<div></div>").appendTo($g);

		this.dose_card($l, __("Overdue — give these first"), "poultry-alert", d.overdue,
			"late", (x) => __("{0} days late", [Math.abs(x.days)]), "bad");
		this.dose_card($l, __("Due today"), "poultry-syringe", d.due_today,
			"today", () => __("today"), "warn");
		this.dose_card($l, __("Coming in the next 7 days"), "poultry-schedule", d.due_soon,
			"soon", (x) => __("in {0} days", [x.days]), "ok");

		// withdrawal
		const $w = $(`<div class="hh-card"><h5>${frappe.utils.icon("poultry-withdrawal", "md")}
			${__("Withdrawal — cannot be sold")}
			<span class="pill ${d.withdrawals.length ? "bad" : "ok"}">${d.withdrawals.length}</span>
			</h5></div>`).appendTo($r);
		if (!d.withdrawals.length) {
			$w.append(`<div class="hh-empty">${__("Every flock is clear for sale.")}</div>`);
		} else {
			d.withdrawals.forEach((x) => {
				$(`<div class="hh-row" data-flock="${x.flock}">
					<div class="main">
						<div class="t">${frappe.utils.escape_html(x.flock_name)}</div>
						<div class="s">${frappe.utils.escape_html(x.medication)} &middot;
							${__("clears")} ${frappe.datetime.str_to_user(x.clears_on)} &middot;
							${Number(x.birds).toLocaleString("en-IN")} ${__("birds")}</div>
					</div>
					<span class="hh-tag hold">${x.days_left === 0 ? __("clears today") : __("{0} days", [x.days_left])}</span>
				</div>`).appendTo($w)
					.on("click", () => frappe.set_route("poultry-flock-360", { flock: x.flock }));
			});
		}

		// medications
		const $m = $(`<div class="hh-card"><h5>${frappe.utils.icon("poultry-pill", "md")}
			${__("Recent medication")}</h5></div>`).appendTo($r);
		if (!d.medications.length) {
			$m.append(`<div class="hh-empty">${__("No medication recorded.")}</div>`);
		} else {
			d.medications.forEach((x) => {
				$(`<div class="hh-row" data-name="${x.name}">
					<div class="main">
						<div class="t">${frappe.utils.escape_html(x.medication)}</div>
						<div class="s">${frappe.utils.escape_html(x.flock_name)} &middot;
							${frappe.datetime.str_to_user(x.start_date)} → ${frappe.datetime.str_to_user(x.end_date)}
							${x.reason ? " &middot; " + frappe.utils.escape_html(x.reason) : ""}</div>
					</div>
				</div>`).appendTo($m)
					.on("click", () => frappe.set_route("Form", "Medication Entry", x.name));
			});
		}

		// mortality reasons
		const total = d.mortality_reasons.reduce((s, x) => s + Number(x.qty || 0), 0) || 1;
		const $mr = $(`<div class="hh-card"><h5>${frappe.utils.icon("poultry-mortality", "md")}
			${__("Why birds died — last 30 days")}</h5></div>`).appendTo($r);
		if (!d.mortality_reasons.length) {
			$mr.append(`<div class="hh-empty">${__("No mortality recorded.")}</div>`);
		} else {
			d.mortality_reasons.forEach((x) => {
				const pct = Math.round((Number(x.qty) / total) * 100);
				$(`<div class="hh-reason">
					<div class="top"><span>${frappe.utils.escape_html(x.reason)}</span>
						<b>${Number(x.qty).toLocaleString("en-IN")} &middot; ${pct}%</b></div>
					<div class="hh-bar"><i style="width:${pct}%"></i></div>
				</div>`).appendTo($mr);
			});
		}
	}

	dose_card($parent, title, icon, rows, tag, tagtext, pill) {
		const $c = $(`<div class="hh-card"><h5>${frappe.utils.icon(icon, "md")} ${title}
			<span class="pill ${rows.length ? pill : "ok"}">${rows.length}</span></h5></div>`)
			.appendTo($parent);
		if (!rows.length) {
			$c.append(`<div class="hh-empty">${__("Nothing here. Good.")}</div>`);
			return;
		}
		rows.forEach((x) => {
			$(`<div class="hh-row">
				<div class="main">
					<div class="t">${frappe.utils.escape_html(x.vaccine)}</div>
					<div class="s">${frappe.utils.escape_html(x.flock_name)} &middot;
						${frappe.utils.escape_html(x.route || "")} &middot;
						${__("day")} ${x.age_days} &middot;
						${Number(x.current_qty || 0).toLocaleString("en-IN")} ${__("birds")}</div>
				</div>
				<span class="hh-tag ${tag}">${tagtext(x)}</span>
			</div>`).appendTo($c)
				.on("click", () => frappe.new_doc("Vaccination Entry", {
					flock: x.flock, vaccine: x.vaccine, route: x.route,
					posting_date: frappe.datetime.get_today(),
				}));
		});
	}
}
