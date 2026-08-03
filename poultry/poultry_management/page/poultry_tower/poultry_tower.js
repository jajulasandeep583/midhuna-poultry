frappe.pages["poultry-tower"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Poultry Control Tower"),
		single_column: true,
	});
	wrapper.poultry_tower = new PoultryControlTower(page);
};

frappe.pages["poultry-tower"].on_page_show = function (wrapper) {
	wrapper.poultry_tower && wrapper.poultry_tower.refresh();
};

class PoultryControlTower {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="pt-tower"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.refresh(), "refresh");
		this.page.add_menu_item(__("New Daily Entry"), () =>
			frappe.new_doc("Daily Flock Entry")
		);
		this.page.add_menu_item(__("Open Flock List"), () =>
			frappe.set_route("List", "Flock")
		);
		this.refresh();
	}

	inject_styles() {
		if (document.getElementById("pt-tower-styles")) return;
		$(`<style id="pt-tower-styles">
		.pt-tower { padding-bottom: 2rem; }
		/* frappe's .icon sets margin: 0 auto, which inside a flex row eats all the
		   free space and shunts the heading to the far right. */
		.pt-tower .icon { margin: 0; flex: none; }
		.pt-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
			gap: 10px; margin-bottom: 1.4rem; }
		.pt-kpi { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 12px 14px; }
		.pt-kpi .l { font-size: var(--text-xs); color: var(--text-muted);
			text-transform: uppercase; letter-spacing: .04em; }
		.pt-kpi .v { font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--text-color);
			white-space: nowrap; }
		.pt-kpi .s { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
		.pt-kpi.warn .v { color: var(--orange-500); }
		.pt-kpi.bad  .v { color: var(--red-500); }
		.pt-kpi.good .v { color: var(--green-600); }

		.pt-sec { display: flex; align-items: center; gap: 8px; margin: 1.6rem 0 .8rem; }
		.pt-sec h4 { margin: 0; font-size: var(--text-md); font-weight: 600; }
		.pt-sec .icon { width: 18px; height: 18px; }
		.pt-sec .count { font-size: var(--text-xs); color: var(--text-muted); }

		.pt-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
			gap: 12px; }
		.pt-card { position: relative; background: var(--card-bg);
			border: 1px solid var(--border-color); border-radius: var(--border-radius-md);
			padding: 14px 14px 12px 18px; cursor: pointer; transition: box-shadow .15s ease; }
		.pt-card:hover { box-shadow: var(--shadow-base); }
		.pt-card::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
			border-radius: var(--border-radius-md) 0 0 var(--border-radius-md); }
		.pt-card.green::before { background: var(--green-500); }
		.pt-card.amber::before { background: var(--orange-400); }
		.pt-card.red::before   { background: var(--red-500); }
		.pt-card .top { display: flex; justify-content: space-between; align-items: flex-start;
			gap: 8px; }
		.pt-card .name { font-weight: 600; color: var(--text-color); }
		.pt-card .meta { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
		.pt-chip { font-size: 11px; padding: 2px 8px; border-radius: 10px; white-space: nowrap;
			background: var(--bg-light-gray); color: var(--text-muted); }
		.pt-chip.broiler { background: var(--blue-100); color: var(--blue-600); }
		.pt-chip.layer   { background: var(--yellow-100); color: var(--yellow-700); }
		.pt-chip.rearing { background: var(--purple-100); color: var(--purple-600); }
		.pt-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;
			margin-top: 12px; }
		.pt-metrics div { text-align: left; }
		.pt-metrics .m-l { font-size: 10px; color: var(--text-muted); text-transform: uppercase; }
		.pt-metrics .m-v { font-size: var(--text-md); font-weight: 600; color: var(--text-color); }
		.pt-note { margin-top: 10px; font-size: var(--text-xs); border-radius: 6px;
			padding: 6px 8px; display: flex; gap: 6px; align-items: flex-start; }
		.pt-note.alert { background: var(--red-50); color: var(--red-600); }
		.pt-note.hold  { background: var(--orange-50); color: var(--orange-600); }
		.pt-note.miss  { background: var(--bg-light-gray); color: var(--text-muted); }

		.pt-split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
		@media (max-width: 900px) { .pt-split { grid-template-columns: 1fr; } }
		.pt-list { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); overflow: hidden; }
		.pt-list .row { display: flex; justify-content: space-between; gap: 10px;
			padding: 9px 14px; border-bottom: 1px solid var(--border-color);
			font-size: var(--text-sm); cursor: pointer; }
		.pt-list .row:last-child { border-bottom: 0; }
		.pt-list .row:hover { background: var(--bg-light-gray); }
		.pt-list .row .r { color: var(--text-muted); font-size: var(--text-xs);
			white-space: nowrap; }
		.pt-list .empty { padding: 18px 14px; color: var(--text-muted);
			font-size: var(--text-sm); text-align: center; }
		.pt-late { color: var(--red-500); font-weight: 600; }
		</style>`).appendTo(document.head);
	}

	refresh() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.control_tower" }).then((r) => {
			if (!r || !r.message) return;
			this.data = r.message;
			this.render();
		});
	}

	render() {
		const d = this.data;
		this.$body.empty();
		this.render_kpis(d.totals);
		this.render_cards(d.cards);
		this.render_panels(d);
	}

	render_kpis(t) {
		const fmt = (n) => frappe.format(n, { fieldtype: "Int" });
		const tiles = [
			{ l: __("Birds on Hand"), v: fmt(t.birds), s: __("across {0} flocks", [t.flocks]) },
			{ l: __("Sheds Occupied"), v: `${t.sheds_occupied} / ${t.sheds_total}`,
			  s: __("all-in all-out") },
			{ l: __("Eggs Today"), v: fmt(t.eggs_today), s: __("collected") },
			{ l: __("Feed Today"), v: `${fmt(t.feed_today_kg)} kg`, s: __("issued to sheds") },
			{ l: __("Losses Today"), v: fmt(t.losses_today), s: __("dead and culled"),
			  cls: t.losses_today > 0 ? "warn" : "good" },
			{ l: __("Entries Pending"), v: t.pending_entries, s: __("flocks not entered today"),
			  cls: t.pending_entries ? "warn" : "good" },
			{ l: __("Vaccinations Overdue"), v: t.overdue_vaccinations, s: __("past due date"),
			  cls: t.overdue_vaccinations ? "bad" : "good" },
			{ l: __("Under Withdrawal"), v: t.under_withdrawal, s: __("cannot be sold"),
			  cls: t.under_withdrawal ? "bad" : "good" },
		];
		const $g = $('<div class="pt-kpis"></div>').appendTo(this.$body);
		tiles.forEach((k) =>
			$(`<div class="pt-kpi ${k.cls || ""}">
				<div class="l">${k.l}</div><div class="v">${k.v}</div><div class="s">${k.s}</div>
			</div>`).appendTo($g)
		);
	}

	render_cards(cards) {
		const order = { red: 0, amber: 1, green: 2 };
		const sorted = [...cards].sort((a, b) => order[a.status] - order[b.status]);

		$(`<div class="pt-sec">${frappe.utils.icon("poultry-hen", "md")}
			<h4>${__("Flocks")}</h4>
			<span class="count">${__("needing attention first")}</span></div>`).appendTo(this.$body);

		const $g = $('<div class="pt-cards"></div>').appendTo(this.$body);
		if (!sorted.length) {
			$g.html(`<div class="pt-list"><div class="empty">${__("No active flocks.")}</div></div>`);
			return;
		}

		sorted.forEach((c) => {
			const isLayer = c.flock_type === "Layer" || c.flock_type === "Breeder";
			const chip = (c.flock_type || "").toLowerCase();
			const metrics = isLayer
				? [
					{ l: __("Birds"), v: frappe.format(c.birds, { fieldtype: "Int" }) },
					{ l: __("HDP"), v: `${c.hdp}%` },
					{ l: __("Livability"), v: `${c.livability_pct.toFixed(1)}%` },
					{ l: __("Age"), v: `${c.age_days}d` },
				  ]
				: [
					{ l: __("Birds"), v: frappe.format(c.birds, { fieldtype: "Int" }) },
					{ l: __("FCR"), v: c.fcr ? c.fcr.toFixed(2) : "-" },
					{ l: __("EEF"), v: c.eef ? Math.round(c.eef) : "-" },
					{ l: __("Age"), v: `${c.age_days}d` },
				  ];

			let note = "";
			if (c.alert) note = `<div class="pt-note alert">${frappe.utils.icon("poultry-alert", "sm")}<span>${frappe.utils.escape_html(c.alert)}</span></div>`;
			else if (c.withdrawal) note = `<div class="pt-note hold">${frappe.utils.icon("poultry-withdrawal", "sm")}<span>${__("Withdrawal")}: ${frappe.utils.escape_html(c.withdrawal)}</span></div>`;
			else if (!c.entered_today) note = `<div class="pt-note miss">${frappe.utils.icon("poultry-clipboard", "sm")}<span>${c.days_missing > 1 ? __("{0} days without an entry", [c.days_missing]) : __("Today's entry not in yet")}</span></div>`;

			const $c = $(`<div class="pt-card ${c.status}">
				<div class="top">
					<div>
						<div class="name">${frappe.utils.escape_html(c.flock_name)}</div>
						<div class="meta">${frappe.utils.escape_html(c.shed)} &middot; ${frappe.utils.escape_html(c.strain || "")}</div>
					</div>
					<span class="pt-chip ${chip}">${__(c.flock_type)}</span>
				</div>
				<div class="pt-metrics">
					${metrics.map((m) => `<div><div class="m-l">${m.l}</div><div class="m-v">${m.v}</div></div>`).join("")}
				</div>
				${note}
			</div>`).appendTo($g);

			$c.on("click", () => frappe.set_route("poultry-flock-360", { flock: c.flock }));
		});
	}

	render_panels(d) {
		const $split = $('<div class="pt-split" style="margin-top:1.6rem"></div>').appendTo(this.$body);

		const $left = $("<div></div>").appendTo($split);
		$(`<div class="pt-sec">${frappe.utils.icon("poultry-schedule", "md")}
			<h4>${__("Overdue Vaccinations")}</h4></div>`).appendTo($left);
		const $l1 = $('<div class="pt-list"></div>').appendTo($left);
		if (!d.overdue.length) {
			$l1.html(`<div class="empty">${__("Nothing overdue. Every planned dose is done.")}</div>`);
		} else {
			d.overdue.forEach((o) => {
				$(`<div class="row"><span>${frappe.utils.escape_html(o.vaccine)}
					<span class="r">&middot; ${frappe.utils.escape_html(o.flock)}</span></span>
					<span class="r pt-late">${__("{0}d late", [o.overdue_days])}</span></div>`)
					.appendTo($l1)
					.on("click", () => frappe.set_route("Form", "Flock", o.flock));
			});
		}

		const $right = $("<div></div>").appendTo($split);
		$(`<div class="pt-sec">${frappe.utils.icon("poultry-alert", "md")}
			<h4>${__("Alerts This Week")}</h4></div>`).appendTo($right);
		const $l2 = $('<div class="pt-list"></div>').appendTo($right);
		if (!d.alerts.length) {
			$l2.html(`<div class="empty">${__("No alerts raised in the last 7 days.")}</div>`);
		} else {
			d.alerts.forEach((a) => {
				const first = (a.alert_message || "").split("\n")[0];
				$(`<div class="row"><span>${frappe.utils.escape_html(first)}</span>
					<span class="r">${frappe.datetime.str_to_user(a.posting_date)}</span></div>`)
					.appendTo($l2)
					.on("click", () => frappe.set_route("Form", "Daily Flock Entry", a.name));
			});
		}
	}
}
