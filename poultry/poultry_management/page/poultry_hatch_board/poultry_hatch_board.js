frappe.pages["poultry-hatch-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hatchery Board"),
		single_column: true,
	});
	wrapper.hatch_board = new HatchBoard(page);
};

frappe.pages["poultry-hatch-board"].on_page_show = function (wrapper) {
	wrapper.hatch_board && wrapper.hatch_board.load();
};

const N = (n) => Number(n || 0).toLocaleString("en-IN");
const P = (n, d = 1) => Number(n || 0).toFixed(d);

class HatchBoard {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.add_filters();
		this.$body = $('<div class="hb"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.page.add_menu_item(__("Receive Hatching Eggs"), () =>
			frappe.new_doc("Hatching Egg Receipt"));
		this.page.add_menu_item(__("New Egg Setting"), () => frappe.new_doc("Egg Setting"));
		this.page.add_menu_item(__("New Breakout Analysis"), () =>
			frappe.new_doc("Breakout Analysis"));
		this.load();
	}

	add_filters() {
		this.chick_type = this.page.add_field({
			fieldname: "chick_type", label: __("Chick Type"), fieldtype: "Link",
			options: "Chick Type", change: () => this.load(),
		});
	}

	inject_styles() {
		if (document.getElementById("hb-styles")) return;
		$(`<style id="hb-styles">
		.hb { padding-bottom: 2.5rem; }
		.hb .icon { margin: 0; flex: none; }
		.hb-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
			gap: 12px; margin-bottom: 1.5rem; }
		.hb-kpi { border-radius: var(--border-radius-md); padding: 14px 16px; color: #fff;
			position: relative; overflow: hidden; }
		.hb-kpi .l { font-size: var(--text-xs); text-transform: uppercase;
			letter-spacing: .05em; opacity: .85; }
		.hb-kpi .v { font-size: 25px; font-weight: 700; margin-top: 4px; white-space: nowrap; }
		.hb-kpi .s { font-size: var(--text-xs); opacity: .85; margin-top: 2px; }
		.hb-kpi .bg { position: absolute; right: -8px; bottom: -12px; opacity: .17; }
		.hb-kpi .bg .icon { width: 80px; height: 80px; stroke: #fff !important; }
		.hb-egg   { background: linear-gradient(135deg,#E8A33D,#D9822B); }
		.hb-set   { background: linear-gradient(135deg,#D9694B,#B4563A); }
		.hb-due   { background: linear-gradient(135deg,#5B8DEF,#4178D4); }
		.hb-good  { background: linear-gradient(135deg,#2CA58D,#1F9254); }
		.hb-card { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); margin-bottom: 16px; overflow: hidden; }
		.hb-card h5 { display: flex; align-items: center; gap: 8px; margin: 0; padding: 12px 16px;
			font-size: var(--text-md); font-weight: 600;
			border-bottom: 1px solid var(--border-color); }
		.hb-card h5 .note { margin-left: auto; font-weight: 400; font-size: var(--text-xs);
			color: var(--text-muted); }
		.hb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
		@media (max-width: 1100px) { .hb-grid { grid-template-columns: 1fr; } }
		.hb-tbl { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
		.hb-tbl th { text-align: left; font-weight: 500; color: var(--text-muted);
			font-size: var(--text-xs); text-transform: uppercase; padding: 8px 14px;
			border-bottom: 1px solid var(--border-color); white-space: nowrap; }
		.hb-tbl td { padding: 9px 14px; border-bottom: 1px solid var(--border-color);
			white-space: nowrap; }
		.hb-tbl tbody tr:last-child td { border-bottom: 0; }
		.hb-tbl tbody tr { cursor: pointer; }
		.hb-tbl tbody tr:hover { background: var(--bg-light-gray); }
		.hb-tbl .num { text-align: right; font-variant-numeric: tabular-nums; }
		.hb-nm { font-weight: 600; color: var(--text-color); }
		.hb-sub { font-size: var(--text-xs); color: var(--text-muted); }
		.hb-pill { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 10px;
			white-space: nowrap; }
		.hb-pill.ok { background: var(--green-100); color: var(--green-700); }
		.hb-pill.warn { background: var(--orange-100); color: var(--orange-600); }
		.hb-pill.old { background: var(--red-100); color: var(--red-600); }
		.hb-pill.day { background: var(--blue-100); color: var(--blue-600); }
		.hb-track { height: 6px; border-radius: 3px; background: var(--bg-light-gray);
			overflow: hidden; margin-top: 5px; width: 130px; }
		.hb-track i { display: block; height: 100%; background: #D9694B; }
		.hb-empty { padding: 24px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		.hb-cause { font-size: var(--text-xs); color: var(--red-600); font-weight: 600; }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({
			method: "poultry.dashboard.hatch_board",
			args: { chick_type: this.chick_type.get_value() },
		}).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data, t = d.totals;
		this.$body.empty();

		const kpis = [
			{ cls: "hb-egg", icon: "poultry-egg", l: __("Eggs in Store"), v: N(t.eggs_in_store),
			  s: __("{0} receipts, {1} ageing", [t.receipts_in_store, t.ageing_receipts]) },
			{ cls: "hb-set", icon: "poultry-hatchery", l: __("Eggs Incubating"),
			  v: N(t.eggs_incubating), s: __("{0} settings running", [t.settings_incubating]) },
			{ cls: "hb-due", icon: "poultry-schedule", l: __("Hatching This Week"),
			  v: N(t.hatching_this_week), s: __("eggs due in 7 days") },
			{ cls: "hb-good", icon: "poultry-target", l: __("Fertility"),
			  v: `${P(t.avg_fertility)}%`, s: __("average of finished hatches") },
			{ cls: "hb-good", icon: "poultry-chick", l: __("Hatch of Set"),
			  v: `${P(t.avg_hatch_of_set)}%`, s: __("average of finished hatches") },
		];
		const $k = $('<div class="hb-kpis"></div>').appendTo(this.$body);
		kpis.forEach((k) =>
			$(`<div class="hb-kpi ${k.cls}"><div class="l">${k.l}</div>
				<div class="v">${k.v}</div><div class="s">${k.s}</div>
				<div class="bg">${frappe.utils.icon(k.icon, "lg")}</div></div>`).appendTo($k));

		// ---- incubating
		const $inc = $(`<div class="hb-card"><h5>${frappe.utils.icon("poultry-hatchery", "md")}
			${__("In the machines")}
			<span class="note">${__("day of incubation, and what is due next")}</span></h5></div>`)
			.appendTo(this.$body);
		if (!d.incubating.length) {
			$inc.append(`<div class="hb-empty">${__("Nothing incubating.")}</div>`);
		} else {
			$inc.append(`<div style="overflow-x:auto"><table class="hb-tbl">
				<thead><tr><th>${__("Setting")}</th><th>${__("Chick Type")}</th>
				<th class="num">${__("Eggs")}</th><th>${__("Setter")}</th>
				<th>${__("Day")}</th><th>${__("Next")}</th><th>${__("Hatch Due")}</th>
				<th class="num">${__("Breeder Age")}</th></tr></thead><tbody>
				${d.incubating.map((s) => `<tr data-name="${s.name}">
					<td><div class="hb-nm">${s.name}</div>
						<div class="hb-sub">${__("set")} ${frappe.datetime.str_to_user(s.set_date)}</div></td>
					<td>${frappe.utils.escape_html(s.chick_type || "-")}</td>
					<td class="num">${N(s.eggs_set)}</td>
					<td>${frappe.utils.escape_html(s.setter || "")}</td>
					<td><span class="hb-pill day">${__("Day")} ${s.day}</span>
						<div class="hb-track"><i style="width:${Math.min(100, (s.day / 21) * 100)}%"></i></div></td>
					<td>${__(s.next)}</td>
					<td>${frappe.datetime.str_to_user(s.hatch_date)}
						<div class="hb-sub">${s.days_to_hatch >= 0
							? __("in {0}d", [s.days_to_hatch]) : __("overdue")}</div></td>
					<td class="num">${P(s.breeder_age_weeks)} ${__("wk")}</td>
				</tr>`).join("")}</tbody></table></div>`);
			$inc.find("tbody tr").on("click", function () {
				frappe.set_route("Form", "Egg Setting", $(this).data("name"));
			});
		}

		const $g = $('<div class="hb-grid"></div>').appendTo(this.$body);

		// ---- egg store
		const $st = $(`<div class="hb-card"><h5>${frappe.utils.icon("poultry-egg", "md")}
			${__("Egg store")}
			<span class="note">${__("hatchability falls past 7 days")}</span></h5></div>`)
			.appendTo($g);
		if (!d.store.length) {
			$st.append(`<div class="hb-empty">${__("No eggs in store.")}</div>`);
		} else {
			$st.append(`<table class="hb-tbl">
				<thead><tr><th>${__("Receipt")}</th><th class="num">${__("In Store")}</th>
				<th class="num">${__("Settable")}</th><th>${__("Age")}</th></tr></thead><tbody>
				${d.store.map((r) => `<tr data-name="${r.name}">
					<td><div class="hb-nm">${frappe.utils.escape_html(r.chick_type || r.name)}</div>
						<div class="hb-sub">${frappe.utils.escape_html((r.supplier || "").slice(0, 34))}</div></td>
					<td class="num">${N(r.eggs_in_store)}</td>
					<td class="num">${P(r.settable_pct)}%</td>
					<td><span class="hb-pill ${r.ageing}">${r.storage_days}d</span></td>
				</tr>`).join("")}</tbody></table>`);
			$st.find("tbody tr").on("click", function () {
				frappe.set_route("Form", "Hatching Egg Receipt", $(this).data("name"));
			});
		}

		// ---- breakout spread
		const $bs = $(`<div class="hb-card"><h5>${frappe.utils.icon("poultry-search", "md")}
			${__("Why eggs did not hatch")}
			<span class="note">${__("breakout of the residue")}</span></h5>
			<div class="c" style="padding:8px"></div></div>`).appendTo($g);
		if (!d.spread.length) {
			$bs.find(".c").html(`<div class="hb-empty">${__("No breakout recorded yet.")}</div>`);
		} else {
			new frappe.Chart($bs.find(".c")[0], {
				data: {
					labels: d.spread.map((x) => __(x.label)),
					datasets: [{ name: __("Eggs"), values: d.spread.map((x) => x.qty) }],
				},
				type: "bar", height: 240, colors: ["#D9694B"],
			});
		}

		// ---- finished hatches
		const $h = $(`<div class="hb-card"><h5>${frappe.utils.icon("poultry-chick", "md")}
			${__("Finished hatches")}</h5></div>`).appendTo(this.$body);
		if (!d.hatched.length) {
			$h.append(`<div class="hb-empty">${__("Nothing hatched yet.")}</div>`);
		} else {
			$h.append(`<div style="overflow-x:auto"><table class="hb-tbl">
				<thead><tr><th>${__("Setting")}</th><th>${__("Chick Type")}</th>
				<th class="num">${__("Breeder Age")}</th><th class="num">${__("Eggs Set")}</th>
				<th class="num">${__("Fertile")}</th><th class="num">${__("Fertility %")}</th>
				<th class="num">${__("Hatched")}</th><th class="num">${__("Hatch of Set %")}</th>
				<th class="num">${__("Hatch of Fertile %")}</th></tr></thead><tbody>
				${d.hatched.map((h) => `<tr data-name="${h.name}">
					<td><div class="hb-nm">${h.name}</div>
						<div class="hb-sub">${frappe.datetime.str_to_user(h.hatch_date)}</div></td>
					<td>${frappe.utils.escape_html(h.chick_type || "-")}</td>
					<td class="num">${P(h.breeder_age_weeks)}</td>
					<td class="num">${N(h.eggs_set)}</td>
					<td class="num">${N(h.fertile_eggs)}</td>
					<td class="num">${P(h.fertility_pct)}</td>
					<td class="num">${N(h.chicks_hatched)}</td>
					<td class="num hb-nm">${P(h.hatchability_set_pct)}</td>
					<td class="num">${P(h.hatchability_fertile_pct)}</td>
				</tr>`).join("")}</tbody></table></div>`);
			$h.find("tbody tr").on("click", function () {
				frappe.set_route("Form", "Egg Setting", $(this).data("name"));
			});
		}

		// ---- breakout readings
		if (d.breakouts.length) {
			const $b = $(`<div class="hb-card"><h5>${frappe.utils.icon("poultry-virus", "md")}
				${__("Breakout readings")}
				<span class="note">${__("what the residue points at")}</span></h5></div>`)
				.appendTo(this.$body);
			$b.append(`<div style="overflow-x:auto"><table class="hb-tbl">
				<thead><tr><th>${__("Setting")}</th><th class="num">${__("Broken Out")}</th>
				<th class="num">${__("Infertile %")}</th><th class="num">${__("Early Dead %")}</th>
				<th class="num">${__("Late Dead %")}</th><th class="num">${__("Contam %")}</th>
				<th>${__("Likely Cause")}</th></tr></thead><tbody>
				${d.breakouts.map((b) => `<tr data-name="${b.name}">
					<td class="hb-nm">${b.egg_setting}</td>
					<td class="num">${N(b.eggs_broken)}</td>
					<td class="num">${P(b.infertile_pct)}</td>
					<td class="num">${P(b.early_dead_pct)}</td>
					<td class="num">${P(b.late_dead_pct)}</td>
					<td class="num">${P(b.contamination_pct)}</td>
					<td class="hb-cause">${frappe.utils.escape_html(b.likely_cause || "-")}</td>
				</tr>`).join("")}</tbody></table></div>`);
			$b.find("tbody tr").on("click", function () {
				frappe.set_route("Form", "Breakout Analysis", $(this).data("name"));
			});
		}
	}
}
