frappe.pages["poultry-flock-360"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Flock 360"),
		single_column: true,
	});
	wrapper.flock360 = new Flock360(page);
};

frappe.pages["poultry-flock-360"].on_page_show = function (wrapper) {
	const flock = frappe.get_route_options && frappe.get_route_options().flock;
	if (wrapper.flock360 && flock) wrapper.flock360.select(flock);
};

class Flock360 {
	constructor(page) {
		this.page = page;
		this.inject_styles();

		this.field = this.page.add_field({
			fieldname: "flock",
			label: __("Flock"),
			fieldtype: "Link",
			options: "Flock",
			change: () => this.load(this.field.get_value()),
		});

		this.$body = $('<div class="f360"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(this.field.get_value()), "refresh");

		const routed = frappe.get_route_options && frappe.get_route_options().flock;
		if (routed) this.select(routed);
		else this.pick_default();
	}

	select(flock) {
		this.field.set_value(flock);
	}

	pick_default() {
		frappe.call({ method: "poultry.dashboard.flock_options" }).then((r) => {
			const list = (r.message || []).filter((f) => f.status !== "Draft");
			if (list.length) this.select(list[0].name);
			else this.$body.html(this.empty(__("No flocks yet. Create one to see this view.")));
		});
	}

	inject_styles() {
		if (document.getElementById("f360-styles")) return;
		$(`<style id="f360-styles">
		.f360 { padding-bottom: 2rem; }
		/* frappe's .icon uses margin: 0 auto, which right-shunts flex headings */
		.f360 .icon { margin: 0; flex: none; }
		.f360-head { display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
			margin-bottom: 1rem; }
		.f360-head .t { font-size: 20px; font-weight: 700; color: var(--text-color); }
		.f360-head .sub { color: var(--text-muted); font-size: var(--text-sm); }
		.f360-badge { font-size: 11px; padding: 3px 9px; border-radius: 10px;
			background: var(--bg-light-gray); color: var(--text-muted); }
		.f360-badge.on { background: var(--green-100); color: var(--green-700); }
		.f360-badge.hold { background: var(--red-100); color: var(--red-600); }
		.f360-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(172px, 1fr));
			gap: 10px; margin-bottom: 1.4rem; }
		.f360-kpi { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 12px 14px; }
		.f360-kpi .l { font-size: var(--text-xs); color: var(--text-muted);
			text-transform: uppercase; letter-spacing: .04em; }
		.f360-kpi .v { font-size: 21px; font-weight: 700; color: var(--text-color); margin-top: 3px;
			white-space: nowrap; text-align: left; }
		.f360-kpi .v .u { font-size: 13px; font-weight: 500; color: var(--text-muted);
			margin-left: 3px; }
		.f360-kpi .d { font-size: var(--text-xs); margin-top: 2px; white-space: nowrap;
			overflow: hidden; text-overflow: ellipsis; }
		.f360-kpi .d.up { color: var(--green-600); }
		.f360-kpi .d.down { color: var(--red-500); }
		.f360-kpi .d.flat { color: var(--text-muted); }
		.f360-panel { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 14px; margin-bottom: 16px; }
		.f360-panel h5 { margin: 0 0 10px; font-size: var(--text-md); font-weight: 600;
			display: flex; align-items: center; gap: 7px; }
		.f360-split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
		@media (max-width: 900px) { .f360-split { grid-template-columns: 1fr; } }
		.f360-table { width: 100%; font-size: var(--text-sm); border-collapse: collapse; }
		.f360-table th { text-align: left; font-weight: 500; color: var(--text-muted);
			font-size: var(--text-xs); text-transform: uppercase; padding: 6px 8px;
			border-bottom: 1px solid var(--border-color); }
		.f360-table td { padding: 7px 8px; border-bottom: 1px solid var(--border-color); }
		.f360-table tr:last-child td { border-bottom: 0; }
		.f360-table .num { text-align: right; font-variant-numeric: tabular-nums; }
		.f360-pill { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
		.f360-pill.Done { background: var(--green-100); color: var(--green-700); }
		.f360-pill.Pending { background: var(--bg-light-gray); color: var(--text-muted); }
		.f360-pill.Overdue { background: var(--red-100); color: var(--red-600); }
		.f360-pill.Skipped { background: var(--yellow-100); color: var(--yellow-700); }
		.f360-empty { padding: 24px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		</style>`).appendTo(document.head);
	}

	empty(msg) {
		return `<div class="f360-panel"><div class="f360-empty">${msg}</div></div>`;
	}

	load(flock) {
		if (!flock) return;
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.flock_360", args: { flock } }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data;
		const f = d.flock;
		this.$body.empty();
		this.page.set_title(`${f.flock_name}`);

		const isLayer = f.flock_type === "Layer" || f.flock_type === "Breeder";
		const hold = (d.withdrawals || []).length;

		$(`<div class="f360-head">
			${frappe.utils.icon(isLayer ? "poultry-egg" : "poultry-hen", "lg")}
			<div>
				<div class="t">${frappe.utils.escape_html(f.flock_name)}</div>
				<div class="sub">${frappe.utils.escape_html(f.farm)} &middot;
					${frappe.utils.escape_html(f.shed)} &middot;
					${frappe.utils.escape_html(f.strain || "")} &middot;
					${__("placed")} ${frappe.datetime.str_to_user(f.placement_date)}</div>
			</div>
			<span class="f360-badge on">${frappe.utils.escape_html(f.status)}</span>
			${hold ? `<span class="f360-badge hold">${__("Under withdrawal")}</span>` : ""}
			<span style="flex:1"></span>
			<button class="btn btn-default btn-sm">${__("Open Flock")}</button>
		</div>`)
			.appendTo(this.$body)
			.find("button")
			.on("click", () => frappe.set_route("Form", "Flock", f.name));

		this.render_kpis(f, isLayer, d);
		this.render_charts(d, isLayer);
		this.render_tables(d);
	}

	render_kpis(f, isLayer, d) {
		// Plain strings only. frappe.format() returns markup for several
		// fieldtypes, and a block element inside the tile breaks the layout.
		const int = (n) => Number(n || 0).toLocaleString("en-IN");
		const dec = (n, p) => Number(n || 0).toFixed(p);
		const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN",
			{ minimumFractionDigits: 2, maximumFractionDigits: 2 });

		const tiles = [
			{ l: __("Birds Alive"), v: int(f.current_qty),
			  d: __("of {0} placed", [int(f.opening_qty)]) },
			{ l: __("Age"), v: f.age_days, u: "d",
			  d: __("{0} weeks", [(f.age_days / 7).toFixed(1)]) },
			{ l: __("Livability"), v: dec(f.livability_pct, 2), u: "%",
			  d: __("{0} lost", [int(f.cumulative_mortality + f.cumulative_culls)]),
			  cls: f.livability_pct >= 95 ? "up" : "down" },
			{ l: __("Feed"), v: int(Math.round(f.cumulative_feed_kg)), u: "kg",
			  d: __("{0} g/bird", [f.current_qty
				? int(Math.round((f.cumulative_feed_kg * 1000) / f.current_qty)) : 0]) },
		];
		if (isLayer) {
			tiles.push({ l: __("HDP"), v: dec(f.hd_production_pct, 1), u: "%",
				d: __("peak {0}%", [dec(f.peak_production_pct, 1)]) });
			tiles.push({ l: __("Eggs"), v: int(f.cumulative_eggs),
				d: __("{0} per bird housed", [dec(f.eggs_per_bird_housed, 2)]) });
		} else {
			tiles.push({ l: __("FCR"), v: dec(f.fcr, 3), d: __("feed per kg live") });
			tiles.push({ l: __("EEF"), v: dec(f.eef, 0),
				d: f.eef >= 350 ? __("good") : f.eef >= 300 ? __("average") : __("below par"),
				cls: f.eef >= 350 ? "up" : f.eef >= 300 ? "flat" : "down" });
		}
		tiles.push({ l: __("Cost / Bird"), v: money(f.cost_per_bird),
			d: __("{0} per kg live", [money(f.cost_per_kg_live)]) });
		tiles.push({ l: __("Entries"), v: d.entry_count, d: __("days recorded") });

		const $g = $('<div class="f360-kpis"></div>').appendTo(this.$body);
		tiles.forEach((t) =>
			$(`<div class="f360-kpi"><div class="l">${t.l}</div>
				<div class="v">${t.v}${t.u ? `<span class="u">${t.u}</span>` : ""}</div>
				<div class="d ${t.cls || "flat"}">${t.d || ""}</div></div>`).appendTo($g)
		);
	}

	render_charts(d, isLayer) {
		const s = d.series;
		if (!s.age.length) {
			this.$body.append(this.empty(__("No daily entries recorded for this flock yet.")));
			return;
		}
		const $split = $('<div class="f360-split"></div>').appendTo(this.$body);

		const $a = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-standard", "md")}
			${isLayer ? __("Hen-Day Production vs Standard") : __("Body Weight vs Standard")}</h5>
			<div class="chart-a"></div></div>`).appendTo($split);
		new frappe.Chart($a.find(".chart-a")[0], {
			data: {
				labels: s.age.map((a) => `D${a}`),
				datasets: isLayer
					? [
						{ name: __("Actual HDP %"), values: s.hdp },
						{ name: __("Standard HDP %"), values: s.std_hdp },
					  ]
					: [
						{ name: __("Actual g"), values: s.weight },
						{ name: __("Standard g"), values: s.std_weight },
					  ],
			},
			type: "line",
			height: 250,
			colors: ["#449CF0", "#98A1A9"],
			lineOptions: { hideDots: 1, regionFill: 0 },
			axisOptions: { xIsSeries: 1 },
		});

		const $b = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-mortality", "md")}
			${__("Cumulative Mortality vs Standard")}</h5><div class="chart-b"></div></div>`)
			.appendTo($split);
		new frappe.Chart($b.find(".chart-b")[0], {
			data: {
				labels: s.age.map((a) => `D${a}`),
				datasets: [
					{ name: __("Actual %"), values: s.mortality },
					{ name: __("Standard %"), values: s.std_mortality },
				],
			},
			type: "line",
			height: 250,
			colors: ["#E24C4C", "#98A1A9"],
			lineOptions: { hideDots: 1, regionFill: 0 },
			axisOptions: { xIsSeries: 1 },
		});

		const $c = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-feed-bag", "md")}
			${__("Daily Feed (kg)")}</h5><div class="chart-c"></div></div>`).appendTo(this.$body);
		new frappe.Chart($c.find(".chart-c")[0], {
			data: { labels: s.age.map((a) => `D${a}`), datasets: [{ name: __("Feed kg"), values: s.feed }] },
			type: "bar",
			height: 210,
			colors: ["#E8A33D"],
			axisOptions: { xIsSeries: 1 },
		});
	}

	render_tables(d) {
		const $split = $('<div class="f360-split"></div>').appendTo(this.$body);

		const $p = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-schedule", "md")}
			${__("Vaccination Plan")}</h5></div>`).appendTo($split);
		if (!d.plan.length) {
			$p.append(`<div class="f360-empty">${__("No vaccination plan for this flock.")}</div>`);
		} else {
			$p.append(`<table class="f360-table">
				<thead><tr><th>${__("Day")}</th><th>${__("Vaccine")}</th><th>${__("Due")}</th>
				<th>${__("Status")}</th></tr></thead>
				<tbody>${d.plan.map((r) => `<tr>
					<td class="num">${r.age_days}</td>
					<td>${frappe.utils.escape_html(r.vaccine || "")}</td>
					<td>${r.due_date ? frappe.datetime.str_to_user(r.due_date) : ""}</td>
					<td><span class="f360-pill ${r.status}">${__(r.status)}</span></td>
				</tr>`).join("")}</tbody></table>`);
		}

		const $e = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-clipboard", "md")}
			${__("Recent Daily Entries")}</h5></div>`).appendTo($split);
		if (!d.recent.length) {
			$e.append(`<div class="f360-empty">${__("Nothing recorded yet.")}</div>`);
		} else {
			$e.append(`<table class="f360-table">
				<thead><tr><th>${__("Date")}</th><th class="num">${__("Age")}</th>
				<th class="num">${__("Lost")}</th><th class="num">${__("Feed kg")}</th>
				<th class="num">${__("Eggs")}</th><th></th></tr></thead>
				<tbody>${d.recent.map((r) => `<tr data-name="${r.name}" style="cursor:pointer">
					<td>${frappe.datetime.str_to_user(r.posting_date)}</td>
					<td class="num">${r.age_days}</td>
					<td class="num">${(r.mortality_qty || 0) + (r.cull_qty || 0)}</td>
					<td class="num">${flt(r.total_feed_kg, 1)}</td>
					<td class="num">${r.total_eggs || 0}</td>
					<td>${r.has_alert ? frappe.utils.icon("poultry-alert", "sm") : ""}</td>
				</tr>`).join("")}</tbody></table>`);
			$e.find("tr[data-name]").on("click", function () {
				frappe.set_route("Form", "Daily Flock Entry", $(this).data("name"));
			});
		}

		if (d.medications.length) {
			const $m = $(`<div class="f360-panel"><h5>${frappe.utils.icon("poultry-pill", "md")}
				${__("Medication and Withdrawal")}</h5></div>`).appendTo(this.$body);
			$m.append(`<table class="f360-table">
				<thead><tr><th>${__("Medication")}</th><th>${__("From")}</th><th>${__("To")}</th>
				<th>${__("Clears")}</th><th>${__("Reason")}</th></tr></thead>
				<tbody>${d.medications.map((r) => `<tr>
					<td>${frappe.utils.escape_html(r.medication)}</td>
					<td>${frappe.datetime.str_to_user(r.start_date)}</td>
					<td>${frappe.datetime.str_to_user(r.end_date)}</td>
					<td>${frappe.datetime.str_to_user(r.withdrawal_clear_date)}</td>
					<td>${frappe.utils.escape_html(r.reason || "")}</td>
				</tr>`).join("")}</tbody></table>`);
		}
	}
}
