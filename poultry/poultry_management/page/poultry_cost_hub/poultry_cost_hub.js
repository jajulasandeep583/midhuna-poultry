frappe.pages["poultry-cost-hub"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Cost & Profitability"),
		single_column: true,
	});
	wrapper.cost_hub = new CostHub(page);
};

frappe.pages["poultry-cost-hub"].on_page_show = function (wrapper) {
	wrapper.cost_hub && wrapper.cost_hub.load();
};

const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const money2 = (n) => "₹" + Number(n || 0).toLocaleString("en-IN",
	{ minimumFractionDigits: 2, maximumFractionDigits: 2 });

class CostHub {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="ch"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.load();
	}

	inject_styles() {
		if (document.getElementById("ch-styles")) return;
		$(`<style id="ch-styles">
		.ch { padding-bottom: 2.5rem; }
		.ch .icon { margin: 0; flex: none; }
		.ch-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
			gap: 12px; margin-bottom: 1.5rem; }
		.ch-kpi { border-radius: var(--border-radius-md); padding: 15px 17px; color: #fff;
			position: relative; overflow: hidden; }
		.ch-kpi .l { font-size: var(--text-xs); text-transform: uppercase;
			letter-spacing: .05em; opacity: .85; }
		.ch-kpi .v { font-size: 25px; font-weight: 700; margin-top: 4px; white-space: nowrap; }
		.ch-kpi .s { font-size: var(--text-xs); opacity: .85; margin-top: 2px; }
		.ch-kpi .bg { position: absolute; right: -6px; bottom: -12px; opacity: .18; }
		.ch-kpi .bg .icon { width: 78px; height: 78px; stroke: #fff !important; }
		.ch-green { background: linear-gradient(135deg,#2CA58D,#1F9254); }
		.ch-brown { background: linear-gradient(135deg,#B4763A,#8E5A2B); }
		.ch-blue  { background: linear-gradient(135deg,#5B8DEF,#4178D4); }
		.ch-plum  { background: linear-gradient(135deg,#7C5CFC,#6C4BE0); }
		.ch-card { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); margin-bottom: 16px; overflow: hidden; }
		.ch-card h5 { display: flex; align-items: center; gap: 8px; margin: 0; padding: 13px 16px;
			font-size: var(--text-md); font-weight: 600;
			border-bottom: 1px solid var(--border-color); }
		.ch-card h5 .note { margin-left: auto; font-size: var(--text-xs);
			color: var(--text-muted); font-weight: 400; }
		.ch-tbl { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
		.ch-tbl th { text-align: left; font-weight: 500; color: var(--text-muted);
			font-size: var(--text-xs); text-transform: uppercase; padding: 9px 14px;
			border-bottom: 1px solid var(--border-color); white-space: nowrap; }
		.ch-tbl td { padding: 10px 14px; border-bottom: 1px solid var(--border-color);
			white-space: nowrap; }
		.ch-tbl tbody tr:last-child td { border-bottom: 0; }
		.ch-tbl tbody tr { cursor: pointer; }
		.ch-tbl tbody tr:hover { background: var(--bg-light-gray); }
		.ch-tbl .num { text-align: right; font-variant-numeric: tabular-nums; }
		.ch-name { font-weight: 600; color: var(--text-color); }
		.ch-sub { font-size: var(--text-xs); color: var(--text-muted); }
		.ch-share { display: flex; align-items: center; gap: 8px; }
		.ch-share .bar { width: 62px; height: 6px; border-radius: 3px;
			background: var(--bg-light-gray); overflow: hidden; }
		.ch-share .bar i { display: block; height: 100%; background: #B4763A; }
		.ch-chip { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
		.ch-chip.Closed { background: var(--bg-light-gray); color: var(--text-muted); }
		.ch-chip.Laying, .ch-chip.Growing, .ch-chip.Placed, .ch-chip.Depleting {
			background: var(--green-100); color: var(--green-700); }
		.ch-pos { color: var(--green-600); font-weight: 600; }
		.ch-neg { color: var(--red-500); font-weight: 600; }
		.ch-empty { padding: 26px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.cost_hub" }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data, t = d.totals;
		this.$body.empty();

		const kpis = [
			{ cls: "ch-blue", icon: "poultry-hen", l: __("Value of Birds on Hand"),
			  v: money(t.birds_value), s: __("accumulated cost in live flocks") },
			{ cls: "ch-brown", icon: "poultry-feed-bag", l: __("Feed Issued (30 Days)"),
			  v: money(t.feed_spend_30), s: __("at valuation rate") },
			{ cls: "ch-green", icon: "poultry-cost", l: __("Revenue (30 Days)"),
			  v: money(t.revenue_30), s: __("invoiced") },
			{ cls: "ch-plum", icon: "poultry-scale", l: __("Avg Cost / kg Live"),
			  v: money2(t.avg_cost_per_kg), s: __("broilers, weighted by live weight") },
		];
		const $k = $('<div class="ch-kpis"></div>').appendTo(this.$body);
		kpis.forEach((k) =>
			$(`<div class="ch-kpi ${k.cls}">
				<div class="l">${k.l}</div><div class="v">${k.v}</div><div class="s">${k.s}</div>
				<div class="bg">${frappe.utils.icon(k.icon, "lg")}</div>
			</div>`).appendTo($k)
		);

		// cost per flock
		const $c = $(`<div class="ch-card"><h5>${frappe.utils.icon("poultry-cost", "md")}
			${__("Cost by flock")}
			<span class="note">${__("cost pool = day-old chicks + feed issued, read from the stock ledger")}</span>
			</h5></div>`).appendTo(this.$body);
		if (!d.rows.length) {
			$c.append(`<div class="ch-empty">${__("No flocks yet.")}</div>`);
		} else {
			const body = d.rows.map((r) => `<tr data-flock="${r.flock}">
				<td><div class="ch-name">${frappe.utils.escape_html(r.flock_name)}</div>
					<div class="ch-sub">${frappe.utils.escape_html(r.shed)}</div></td>
				<td><span class="ch-chip ${r.status}">${__(r.status)}</span></td>
				<td class="num">${Number(r.birds).toLocaleString("en-IN")}</td>
				<td class="num">${money(r.total_cost)}</td>
				<td><div class="ch-share"><div class="bar"><i style="width:${r.feed_share_pct}%"></i></div>
					<span class="ch-sub">${r.feed_share_pct}%</span></div></td>
				<td class="num">${money2(r.cost_per_bird)}</td>
				<td class="num">${r.cost_per_kg_live ? money2(r.cost_per_kg_live) : "-"}</td>
				<td class="num">${r.fcr ? r.fcr.toFixed(3) : "-"}</td>
			</tr>`).join("");
			$c.append(`<div style="overflow-x:auto"><table class="ch-tbl">
				<thead><tr><th>${__("Flock")}</th><th>${__("Status")}</th>
				<th class="num">${__("Birds")}</th><th class="num">${__("Total Cost")}</th>
				<th>${__("Feed Share")}</th><th class="num">${__("Cost / Bird")}</th>
				<th class="num">${__("Cost / kg")}</th><th class="num">${__("FCR")}</th></tr></thead>
				<tbody>${body}</tbody></table></div>`);
			$c.find("tbody tr").on("click", function () {
				frappe.set_route("poultry-flock-360", { flock: $(this).data("flock") });
			});
		}

		// feed trend chart
		if (d.feed_trend.length) {
			const $t = $(`<div class="ch-card"><h5>${frappe.utils.icon("poultry-feed-bag", "md")}
				${__("Feed drawn per week")}</h5><div class="c" style="padding:8px"></div></div>`)
				.appendTo(this.$body);
			// One scale only. Kilograms and rupees differ by two orders of
			// magnitude, so plotting both flattens the bars to nothing.
			new frappe.Chart($t.find(".c")[0], {
				data: {
					labels: d.feed_trend.map((x) => frappe.datetime.str_to_user(x.label)),
					datasets: [{ name: __("Feed cost ₹"), values: d.feed_trend.map((x) => x.cost) }],
				},
				type: "bar",
				height: 240,
				colors: ["#B4763A"],
				axisOptions: { xIsSeries: 1 },
				tooltipOptions: {
					formatTooltipY: (v) => "₹" + Number(v).toLocaleString("en-IN"),
				},
			});
		}

		// closed batches
		const $cl = $(`<div class="ch-card"><h5>${frappe.utils.icon("poultry-closure", "md")}
			${__("Closed batches")}</h5></div>`).appendTo(this.$body);
		if (!d.closed.length) {
			$cl.append(`<div class="ch-empty">${__("No flock has been closed yet.")}</div>`);
		} else {
			const body = d.closed.map((r) => `<tr data-flock="${r.flock}">
				<td class="ch-name">${frappe.utils.escape_html(r.flock)}</td>
				<td>${frappe.datetime.str_to_user(r.closure_date)}</td>
				<td class="num">${Number(r.total_live_weight_kg || 0).toLocaleString("en-IN")} kg</td>
				<td class="num">${r.fcr ? Number(r.fcr).toFixed(3) : "-"}</td>
				<td class="num">${r.eef ? Math.round(r.eef) : "-"}</td>
				<td class="num">${money(r.total_cost)}</td>
				<td class="num">${money(r.total_revenue)}</td>
				<td class="num ${Number(r.margin) >= 0 ? "ch-pos" : "ch-neg"}">${money(r.margin)}</td>
			</tr>`).join("");
			$cl.append(`<div style="overflow-x:auto"><table class="ch-tbl">
				<thead><tr><th>${__("Flock")}</th><th>${__("Closed")}</th>
				<th class="num">${__("Live Weight")}</th><th class="num">${__("FCR")}</th>
				<th class="num">${__("EEF")}</th><th class="num">${__("Cost")}</th>
				<th class="num">${__("Revenue")}</th><th class="num">${__("Margin")}</th></tr></thead>
				<tbody>${body}</tbody></table></div>`);
			$cl.find("tbody tr").on("click", function () {
				frappe.set_route("Form", "Flock", $(this).data("flock"));
			});
		}
	}
}
