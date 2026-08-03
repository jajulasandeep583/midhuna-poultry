frappe.pages["poultry-stock"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Stock on Hand"),
		single_column: true,
	});
	wrapper.poultry_stock = new StockBoard(page);
};

frappe.pages["poultry-stock"].on_page_show = function (wrapper) {
	wrapper.poultry_stock && wrapper.poultry_stock.load();
};

const GROUP_META = {
	"Live Birds": { icon: "poultry-hen", c: "#E8A33D", unit: "birds" },
	Eggs: { icon: "poultry-egg", c: "#F0B429", unit: "eggs" },
	Feed: { icon: "poultry-feed-bag", c: "#A9743F", unit: "kg" },
	Other: { icon: "poultry-stock", c: "#6B7A8F", unit: "" },
};

class StockBoard {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="sb"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.page.add_menu_item(__("Stock Ledger"), () =>
			frappe.set_route("query-report", "Stock Ledger"));
		this.page.add_menu_item(__("Stock Balance"), () =>
			frappe.set_route("query-report", "Stock Balance"));
		this.load();
	}

	inject_styles() {
		if (document.getElementById("sb-styles")) return;
		$(`<style id="sb-styles">
		.sb { padding-bottom: 2.5rem; }
		.sb .icon { margin: 0; flex: none; }
		.sb-groups { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
			gap: 12px; margin-bottom: 1.6rem; }
		.sb-g { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 14px 16px; position: relative;
			overflow: hidden; }
		.sb-g::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
			background: var(--c); }
		.sb-g .hd { display: flex; align-items: center; gap: 8px; }
		.sb-g .hd .ic { width: 30px; height: 30px; border-radius: 9px; flex: none;
			display: flex; align-items: center; justify-content: center; }
		.sb-g .hd .n { font-weight: 600; font-size: var(--text-sm); color: var(--text-color); }
		.sb-g .q { font-size: 22px; font-weight: 700; margin-top: 9px; color: var(--text-color);
			white-space: nowrap; }
		.sb-g .q small { font-size: 12px; font-weight: 500; color: var(--text-muted);
			margin-left: 3px; }
		.sb-g .v { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
		.sb-card { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); overflow: hidden; margin-bottom: 16px; }
		.sb-card h5 { display: flex; align-items: center; gap: 8px; margin: 0; padding: 12px 16px;
			font-size: var(--text-md); font-weight: 600;
			border-bottom: 1px solid var(--border-color); }
		.sb-card h5 .tot { margin-left: auto; font-weight: 600; font-size: var(--text-sm);
			color: var(--text-color); }
		.sb-item { border-bottom: 1px solid var(--border-color); }
		.sb-item:last-child { border-bottom: 0; }
		.sb-row { display: flex; align-items: center; gap: 12px; padding: 11px 16px;
			cursor: pointer; }
		.sb-row:hover { background: var(--bg-light-gray); }
		.sb-row .nm { flex: 1; min-width: 0; }
		.sb-row .nm .t { font-weight: 600; color: var(--text-color); white-space: nowrap;
			overflow: hidden; text-overflow: ellipsis; }
		.sb-row .nm .s { font-size: var(--text-xs); color: var(--text-muted); }
		.sb-row .q { text-align: right; font-variant-numeric: tabular-nums;
			font-weight: 600; white-space: nowrap; min-width: 118px; }
		.sb-row .q small { font-weight: 500; color: var(--text-muted); margin-left: 3px; }
		.sb-row .val { text-align: right; font-variant-numeric: tabular-nums;
			color: var(--text-muted); font-size: var(--text-sm); min-width: 110px;
			white-space: nowrap; }
		.sb-row .caret { color: var(--text-muted); font-size: 11px; width: 12px; }
		.sb-wh { display: none; padding: 2px 16px 12px 44px; }
		.sb-wh.open { display: block; }
		.sb-wh div { display: flex; justify-content: space-between; gap: 12px;
			font-size: var(--text-xs); color: var(--text-muted); padding: 4px 0;
			border-bottom: 1px dashed var(--border-color); }
		.sb-wh div:last-child { border-bottom: 0; }
		.sb-wh b { color: var(--text-color); font-variant-numeric: tabular-nums; }
		.sb-empty { padding: 26px; text-align: center; color: var(--text-muted);
			font-size: var(--text-sm); }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.stock_board" }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data;
		const rup = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
		const num = (n) => Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 1 });
		this.$body.empty();

		const $g = $('<div class="sb-groups"></div>').appendTo(this.$body);
		d.groups.forEach((grp) => {
			const m = GROUP_META[grp.group] || GROUP_META.Other;
			$(`<div class="sb-g" style="--c:${m.c}">
				<div class="hd"><div class="ic" style="background:${this.tint(m.c)}">
					${frappe.utils.icon(m.icon, "md")}</div>
					<div class="n">${__(grp.group)}</div></div>
				<div class="q">${num(grp.qty)}<small>${m.unit}</small></div>
				<div class="v">${rup(grp.value)} &middot; ${__("{0} lines", [grp.lines])}</div>
			</div>`).appendTo($g);
		});
		$(`<div class="sb-g" style="--c:#1F9254">
			<div class="hd"><div class="ic" style="background:${this.tint("#1F9254")}">
				${frappe.utils.icon("poultry-cost", "md")}</div>
				<div class="n">${__("Total Stock Value")}</div></div>
			<div class="q">${rup(d.total_value)}</div>
			<div class="v">${__("at valuation rate")}</div>
		</div>`).appendTo($g);

		["Live Birds", "Eggs", "Feed", "Other"].forEach((g) => {
			const items = d.items.filter((i) => i.group === g);
			if (!items.length) return;
			const m = GROUP_META[g] || GROUP_META.Other;
			const total = items.reduce((s, i) => s + i.value, 0);
			const $c = $(`<div class="sb-card"><h5>${frappe.utils.icon(m.icon, "md")} ${__(g)}
				<span class="tot">${rup(total)}</span></h5></div>`).appendTo(this.$body);

			items.forEach((it) => {
				const $i = $('<div class="sb-item"></div>').appendTo($c);
				$(`<div class="sb-row">
					<span class="caret">▸</span>
					<div class="nm"><div class="t">${frappe.utils.escape_html(it.item_name)}</div>
						<div class="s">${it.item_code} &middot; ${__("{0} location(s)", [it.warehouses.length])}</div></div>
					<div class="q">${num(it.qty)}<small>${frappe.utils.escape_html(it.uom || "")}</small></div>
					<div class="val">${rup(it.value)}</div>
				</div>`).appendTo($i);
				const $w = $('<div class="sb-wh"></div>').appendTo($i);
				it.warehouses.forEach((w) =>
					$(`<div><span>${frappe.utils.escape_html(w.warehouse)}</span>
						<b>${num(w.qty)} ${frappe.utils.escape_html(it.uom || "")} &middot; ${rup(w.value)}</b></div>`)
						.appendTo($w));
				$i.find(".sb-row").on("click", () => {
					$w.toggleClass("open");
					$i.find(".caret").text($w.hasClass("open") ? "▾" : "▸");
				});
			});
		});

		if (!d.items.length) {
			this.$body.append(`<div class="sb-card"><div class="sb-empty">${__("Nothing in stock.")}</div></div>`);
		}
	}

	tint(hex) {
		const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
		return `rgba(${r},${g},${b},0.13)`;
	}
}
