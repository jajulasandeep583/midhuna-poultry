frappe.pages["poultry-trade"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sales & Purchases"),
		single_column: true,
	});
	wrapper.poultry_trade = new TradeBoard(page);
};

frappe.pages["poultry-trade"].on_page_show = function (wrapper) {
	wrapper.poultry_trade && wrapper.poultry_trade.load();
};

const rup = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const qty = (n) => Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 1 });

class TradeBoard {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="tb"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.page.add_menu_item(__("New Sales Invoice"), () => frappe.new_doc("Sales Invoice"));
		this.page.add_menu_item(__("New Purchase Receipt"), () =>
			frappe.new_doc("Purchase Receipt"));
		this.load();
	}

	inject_styles() {
		if (document.getElementById("tb-styles")) return;
		$(`<style id="tb-styles">
		.tb { padding-bottom: 2.5rem; }
		.tb .icon { margin: 0; flex: none; }
		.tb-top { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 1.5rem; }
		@media (max-width: 900px) { .tb-top { grid-template-columns: 1fr; } }
		.tb-panel { border-radius: var(--border-radius-md); padding: 16px 18px; color: #fff;
			position: relative; overflow: hidden; }
		.tb-sell { background: linear-gradient(135deg,#2CA58D,#1F9254); }
		.tb-buy  { background: linear-gradient(135deg,#D97757,#B4563A); }
		.tb-panel .hd { display: flex; align-items: center; gap: 8px; font-size: var(--text-sm);
			opacity: .9; text-transform: uppercase; letter-spacing: .05em; }
		.tb-panel .hd .icon { stroke: #fff !important; width: 18px; height: 18px; }
		.tb-panel .big { font-size: 30px; font-weight: 700; margin: 6px 0 2px; white-space: nowrap; }
		.tb-panel .sub { font-size: var(--text-xs); opacity: .9; }
		.tb-panel .split { display: flex; gap: 22px; margin-top: 14px;
			border-top: 1px solid rgba(255,255,255,.25); padding-top: 11px; }
		.tb-panel .split div .l { font-size: 10px; opacity: .85; text-transform: uppercase; }
		.tb-panel .split div .v { font-size: 16px; font-weight: 600; white-space: nowrap; }
		.tb-panel .bg { position: absolute; right: -10px; bottom: -14px; opacity: .16; }
		.tb-panel .bg .icon { width: 96px; height: 96px; stroke: #fff !important; }
		.tb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
		@media (max-width: 1000px) { .tb-grid { grid-template-columns: 1fr; } }
		.tb-card { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); margin-bottom: 16px; overflow: hidden; }
		.tb-card h5 { display: flex; align-items: center; gap: 8px; margin: 0; padding: 12px 16px;
			font-size: var(--text-md); font-weight: 600;
			border-bottom: 1px solid var(--border-color); }
		.tb-card h5 .note { margin-left: auto; font-weight: 400; font-size: var(--text-xs);
			color: var(--text-muted); }
		.tb-tbl { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
		.tb-tbl th { text-align: left; font-weight: 500; color: var(--text-muted);
			font-size: var(--text-xs); text-transform: uppercase; padding: 8px 14px;
			border-bottom: 1px solid var(--border-color); white-space: nowrap; }
		.tb-tbl td { padding: 9px 14px; border-bottom: 1px solid var(--border-color);
			white-space: nowrap; }
		.tb-tbl tbody tr:last-child td { border-bottom: 0; }
		.tb-tbl tbody tr:hover { background: var(--bg-light-gray); }
		.tb-tbl .num { text-align: right; font-variant-numeric: tabular-nums; }
		.tb-nm { font-weight: 600; color: var(--text-color); }
		.tb-sub { font-size: var(--text-xs); color: var(--text-muted); }
		.tb-bar { height: 6px; border-radius: 3px; background: var(--bg-light-gray);
			overflow: hidden; margin-top: 4px; width: 110px; }
		.tb-bar i { display: block; height: 100%; }
		.tb-empty { padding: 24px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		.tb-link { cursor: pointer; }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.trade_board" }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data;
		this.$body.empty();

		const $t = $('<div class="tb-top"></div>').appendTo(this.$body);
		$(`<div class="tb-panel tb-sell">
			<div class="hd">${frappe.utils.icon("poultry-sales", "sm")} ${__("Sales today")}</div>
			<div class="big">${rup(d.sales.today.amount)}</div>
			<div class="sub">${__("{0} invoices", [d.sales.today.docs])}</div>
			<div class="split">
				<div><div class="l">${__("Last 7 days")}</div><div class="v">${rup(d.sales.week.amount)}</div></div>
				<div><div class="l">${__("Last 30 days")}</div><div class="v">${rup(d.sales.month.amount)}</div></div>
				<div><div class="l">${__("Outstanding")}</div><div class="v">${rup(d.receivable)}</div></div>
			</div>
			<div class="bg">${frappe.utils.icon("poultry-sales", "lg")}</div>
		</div>`).appendTo($t);

		$(`<div class="tb-panel tb-buy">
			<div class="hd">${frappe.utils.icon("poultry-purchase", "sm")} ${__("Purchases today")}</div>
			<div class="big">${rup(d.purchases.today.amount)}</div>
			<div class="sub">${__("{0} documents", [d.purchases.today.docs])}</div>
			<div class="split">
				<div><div class="l">${__("Last 7 days")}</div><div class="v">${rup(d.purchases.week.amount)}</div></div>
				<div><div class="l">${__("Last 30 days")}</div><div class="v">${rup(d.purchases.month.amount)}</div></div>
			</div>
			<div class="bg">${frappe.utils.icon("poultry-purchase", "lg")}</div>
		</div>`).appendTo($t);

		if (d.sales_trend.length) {
			const $c = $(`<div class="tb-card"><h5>${frappe.utils.icon("poultry-trend-up", "md")}
				${__("Sales, last 30 days")}</h5><div class="c" style="padding:6px"></div></div>`)
				.appendTo(this.$body);
			new frappe.Chart($c.find(".c")[0], {
				data: {
					labels: d.sales_trend.map((x) => frappe.datetime.str_to_user(x.d)),
					datasets: [{ name: __("Sales ₹"), values: d.sales_trend.map((x) => x.amount) }],
				},
				type: "bar", height: 210, colors: ["#2CA58D"],
				axisOptions: { xIsSeries: 1 },
				tooltipOptions: { formatTooltipY: (v) => rup(v) },
			});
		}

		const $g = $('<div class="tb-grid"></div>').appendTo(this.$body);
		const $l = $("<div></div>").appendTo($g);
		const $r = $("<div></div>").appendTo($g);

		this.item_card($l, __("What we sold — 30 days"), "poultry-egg-tray", d.sold_items,
			"#2CA58D", "Sales Invoice");
		this.party_card($l, __("Top customers"), "poultry-customer", d.customers,
			"customer", "invoices", "#7C5CFC");
		this.doc_card($l, __("Recent invoices"), "poultry-sales", d.recent_sales,
			"customer", "Sales Invoice");

		this.item_card($r, __("What we bought — 30 days"), "poultry-feed-bag", d.bought_items,
			"#D97757", "Purchase Receipt");
		this.party_card($r, __("Top suppliers"), "poultry-dispatch", d.suppliers,
			"supplier", "receipts", "#D97757");
		this.doc_card($r, __("Recent purchase receipts"), "poultry-purchase", d.recent_purchases,
			"supplier", "Purchase Receipt");
	}

	item_card($p, title, icon, rows, colour, dt) {
		const $c = $(`<div class="tb-card"><h5>${frappe.utils.icon(icon, "md")} ${title}</h5></div>`)
			.appendTo($p);
		if (!rows.length) {
			$c.append(`<div class="tb-empty">${__("Nothing in this period.")}</div>`);
			return;
		}
		const max = Math.max(...rows.map((r) => Number(r.amount) || 0)) || 1;
		const body = rows.map((r) => `<tr>
			<td><div class="tb-nm">${frappe.utils.escape_html(r.item_name)}</div>
				<div class="tb-bar"><i style="width:${Math.round((r.amount / max) * 100)}%;background:${colour}"></i></div></td>
			<td class="num">${qty(r.qty)} <span class="tb-sub">${frappe.utils.escape_html(r.stock_uom || "")}</span></td>
			<td class="num tb-nm">${rup(r.amount)}</td>
		</tr>`).join("");
		$c.append(`<table class="tb-tbl"><thead><tr><th>${__("Item")}</th>
			<th class="num">${__("Qty")}</th><th class="num">${__("Value")}</th></tr></thead>
			<tbody>${body}</tbody></table>`);
	}

	party_card($p, title, icon, rows, field, countfield, colour) {
		const $c = $(`<div class="tb-card"><h5>${frappe.utils.icon(icon, "md")} ${title}</h5></div>`)
			.appendTo($p);
		if (!rows.length) {
			$c.append(`<div class="tb-empty">${__("Nothing in this period.")}</div>`);
			return;
		}
		const max = Math.max(...rows.map((r) => Number(r.amount) || 0)) || 1;
		const body = rows.map((r) => `<tr>
			<td><div class="tb-nm">${frappe.utils.escape_html(r[field])}</div>
				<div class="tb-bar"><i style="width:${Math.round((r.amount / max) * 100)}%;background:${colour}"></i></div></td>
			<td class="num tb-sub">${r[countfield]}</td>
			<td class="num tb-nm">${rup(r.amount)}</td>
		</tr>`).join("");
		$c.append(`<table class="tb-tbl"><thead><tr><th>${__("Party")}</th>
			<th class="num">${__("Docs")}</th><th class="num">${__("Value")}</th></tr></thead>
			<tbody>${body}</tbody></table>`);
	}

	doc_card($p, title, icon, rows, field, dt) {
		const $c = $(`<div class="tb-card"><h5>${frappe.utils.icon(icon, "md")} ${title}</h5></div>`)
			.appendTo($p);
		if (!rows.length) {
			$c.append(`<div class="tb-empty">${__("Nothing yet.")}</div>`);
			return;
		}
		const body = rows.map((r) => `<tr class="tb-link" data-name="${r.name}">
			<td><div class="tb-nm">${frappe.utils.escape_html(r[field])}</div>
				<div class="tb-sub">${r.name}</div></td>
			<td class="tb-sub">${frappe.datetime.str_to_user(r.posting_date)}</td>
			<td class="num tb-nm">${rup(r.base_grand_total)}</td>
		</tr>`).join("");
		$c.append(`<table class="tb-tbl"><thead><tr><th>${__("Party")}</th>
			<th>${__("Date")}</th><th class="num">${__("Value")}</th></tr></thead>
			<tbody>${body}</tbody></table>`);
		$c.find("tr.tb-link").on("click", function () {
			frappe.set_route("Form", dt, $(this).data("name"));
		});
	}
}
