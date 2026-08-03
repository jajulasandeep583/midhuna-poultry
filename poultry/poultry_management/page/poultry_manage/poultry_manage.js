frappe.pages["poultry-manage"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Management"),
		single_column: true,
	});
	wrapper.poultry_manage = new PoultryManage(page);
};

frappe.pages["poultry-manage"].on_page_show = function (wrapper) {
	wrapper.poultry_manage && wrapper.poultry_manage.load();
};

const PM_TILES = [
	{ route: "poultry-trade", icon: "poultry-sales", c: "#1F9254", t: "Sales & Purchases",
	  s: "What went out and what came in, today and this month" },
	{ route: "poultry-stock", icon: "poultry-stock", c: "#4178D4", t: "Stock on Hand",
	  s: "Birds, eggs and feed, item by item and shed by shed" },
	{ route: "poultry-cost-hub", icon: "poultry-cost", c: "#B4763A", t: "Cost & Profitability",
	  s: "Cost per bird and per kilogram, closed-batch margin" },
	{ route: "poultry-tower", icon: "poultry-alert", c: "#E2703A", t: "Control Tower",
	  s: "Every flock ranked by what needs attention" },
	{ route: "poultry-health-hub", icon: "poultry-syringe", c: "#17B897", t: "Vaccination & Health",
	  s: "Doses due, overdue, and what cannot be sold" },
	{ route: "poultry-entry-board", icon: "poultry-board", c: "#4B6A88", t: "Daily Entry Board",
	  s: "Days across, flocks down. Fill the gaps" },
	{ route: "poultry-flock-360", icon: "poultry-target", c: "#6C4BE0", t: "Flock 360",
	  s: "One flock, end to end, against its standard" },
	{ route: "poultry-guide", icon: "poultry-guide", c: "#3E7BB6", t: "How to Use Poultry",
	  s: "The guide, with a button to every screen" },
];

class PoultryManage {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="pm"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.load();
	}

	inject_styles() {
		if (document.getElementById("pm-styles")) return;
		$(`<style id="pm-styles">
		.pm { padding-bottom: 2.5rem; }
		.pm .icon { margin: 0; flex: none; }
		.pm-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(176px, 1fr));
			gap: 12px; margin-bottom: 1.6rem; }
		.pm-s { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 13px 15px; display: flex;
			gap: 11px; align-items: center; }
		.pm-s .ic { width: 36px; height: 36px; border-radius: 10px; flex: none;
			display: flex; align-items: center; justify-content: center; }
		.pm-s .l { font-size: var(--text-xs); color: var(--text-muted);
			text-transform: uppercase; letter-spacing: .04em; }
		.pm-s .v { font-size: 19px; font-weight: 700; color: var(--text-color);
			white-space: nowrap; line-height: 1.2; }
		.pm-h { display: flex; align-items: center; gap: 9px; margin: 0 0 12px; }
		.pm-h h4 { margin: 0; font-size: var(--text-md); font-weight: 600; }
		.pm-h .sub { color: var(--text-muted); font-size: var(--text-xs); }
		.pm-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(268px, 1fr));
			gap: 13px; }
		.pm-tile { display: flex; gap: 13px; align-items: flex-start; cursor: pointer;
			background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 16px 16px; position: relative;
			overflow: hidden; transition: box-shadow .15s ease, transform .15s ease; }
		.pm-tile::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0;
			width: 4px; background: var(--c); }
		.pm-tile:hover { box-shadow: var(--shadow-base); transform: translateY(-1px); }
		.pm-tile .ic { width: 42px; height: 42px; border-radius: 12px; flex: none;
			display: flex; align-items: center; justify-content: center; }
		.pm-tile .ic .icon { width: 22px; height: 22px; }
		.pm-tile .t { font-weight: 600; color: var(--text-color); font-size: var(--text-md); }
		.pm-tile .s { color: var(--text-muted); font-size: var(--text-xs); margin-top: 3px;
			line-height: 1.5; }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.management" }).then((r) => {
			this.data = (r && r.message) || {};
			this.render();
		});
	}

	render() {
		const d = this.data;
		const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
		const num = (n) => Number(n || 0).toLocaleString("en-IN");
		this.$body.empty();

		const strip = [
			{ icon: "poultry-sales", c: "#1F9254", l: __("Sales Today"), v: money(d.sales_today) },
			{ icon: "poultry-purchase", c: "#D97757", l: __("Purchases Today"),
			  v: money(d.purchases_today) },
			{ icon: "poultry-stock", c: "#4178D4", l: __("Stock Value"), v: money(d.stock_value) },
			{ icon: "poultry-hen", c: "#E8A33D", l: __("Birds in Stock"), v: num(d.birds_stock) },
			{ icon: "poultry-egg", c: "#F0B429", l: __("Eggs in Store"), v: num(d.eggs_stock) },
			{ icon: "poultry-feed-bag", c: "#A9743F", l: __("Feed on Hand"),
			  v: `${num(d.feed_stock_kg)} kg` },
		];
		const $s = $('<div class="pm-strip"></div>').appendTo(this.$body);
		strip.forEach((k) =>
			$(`<div class="pm-s">
				<div class="ic" style="background:${this.tint(k.c)}">${frappe.utils.icon(k.icon, "md")}</div>
				<div><div class="l">${k.l}</div><div class="v">${k.v}</div></div>
			</div>`).appendTo($s)
		);

		$(`<div class="pm-h">${frappe.utils.icon("poultry-manage", "md")}
			<h4>${__("All screens")}</h4>
			<span class="sub">${__("everything the farm office needs, in one place")}</span>
		</div>`).appendTo(this.$body);

		const $g = $('<div class="pm-grid"></div>').appendTo(this.$body);
		PM_TILES.forEach((t) => {
			$(`<div class="pm-tile" style="--c:${t.c}">
				<div class="ic" style="background:${this.tint(t.c)}">${frappe.utils.icon(t.icon, "md")}</div>
				<div><div class="t">${__(t.t)}</div><div class="s">${__(t.s)}</div></div>
			</div>`).appendTo($g).on("click", () => frappe.set_route(t.route));
		});
	}

	tint(hex) {
		const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
		return `rgba(${r},${g},${b},0.13)`;
	}
}
