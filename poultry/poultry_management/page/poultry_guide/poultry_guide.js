frappe.pages["poultry-guide"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("How to Use Poultry"),
		single_column: true,
	});
	wrapper.poultry_guide = new PoultryGuide(page);
};

const GUIDE = [
	{
		id: "start",
		icon: "poultry-guide",
		title: "Start here",
		lede: "What the system is doing for you, in one page.",
		blocks: [
			{ type: "text", html:
				"The <b>flock is the spine</b>. Feed, mortality, eggs, vaccines and cost all hang off it. Nothing is entered twice." },
			{ type: "text", html:
				"Two numbers a day are mandatory: <b>mortality</b> and <b>feed</b>. From those, plus the placement details and the breed standard, the system works out livability, FCR, ADG, EEF, HDP and full costing. Everything else is optional — give more and you get more, give only the two numbers and you still get a complete picture." },
			{ type: "table", head: ["Rule", "What it means for you"], rows: [
				["Derived, never entered",
				 "Age, closing count, FCR, EEF and HDP are greyed out. You cannot type them, and you never need to."],
				["Recomputed, never incremented",
				 "Totals are re-added from the daily entries each time. Cancel a wrong day and every total corrects itself."],
				["Standards are snapshotted",
				 "The breed standard is frozen onto the flock at placement, so editing a master later never rewrites history."],
			] },
		],
	},
	{
		id: "day",
		icon: "poultry-alert",
		title: "Your day",
		lede: "The five-minute morning routine.",
		blocks: [
			{ type: "steps", items: [
				"Open the <b>Control Tower</b>. Red cards first — an alert fired or the flock cannot be sold. Amber means today's entry is not in yet.",
				"Open the <b>Daily Entry Board</b> and fill any gaps from yesterday. A grey square is a day nobody recorded; click it to enter that day.",
				"Record today's entries: mortality and feed at minimum.",
				"Check <b>Overdue Vaccinations</b> at the bottom of the Control Tower.",
				"Before promising a load to a buyer, check <b>Withdrawal Period Alert</b>.",
			] },
			{ type: "actions", items: [
				["Poultry Control Tower", "page", "poultry-tower"],
				["Daily Entry Board", "page", "poultry-entry-board"],
				["New Daily Entry", "new", "Daily Flock Entry"],
			] },
		],
	},
	{
		id: "setup",
		icon: "poultry-settings",
		title: "Set up a farm",
		lede: "Once per site, in this order.",
		blocks: [
			{ type: "steps", items: [
				"<b>Farm</b> — name, type, company, capacity, village and district. Set a Cost Center here; flocks inherit it.",
				"<b>Shed</b> — farm, shed code, capacity, housing system. On save the shed <b>creates its own warehouse</b>. Never create these by hand.",
				"<b>Breed</b> and <b>Strain</b> — Cobb, Ross, Hy-Line, BV and so on.",
				"<b>Breed Standard</b> — the target curve per age in days. Tick <i>Is Default for Strain</i> so flocks pick it up automatically.",
				"<b>Feed Type</b> — link a feed to an Item, an age window and a bag weight. The age window is what makes the app suggest the right feed.",
				"<b>Egg Grade</b>, <b>Vaccine</b>, <b>Medication</b> — medication carries withdrawal days, which is what later blocks sales.",
				"<b>Poultry Settings</b> — thresholds, tier, backdating window, mortality account, egg warehouse.",
			] },
			{ type: "actions", items: [
				["Farm", "list", "Farm"], ["Shed", "list", "Shed"],
				["Breed Standard", "list", "Breed Standard"], ["Feed Type", "list", "Feed Type"],
				["Poultry Settings", "form", "Poultry Settings"],
			] },
		],
	},
	{
		id: "place",
		icon: "poultry-chick",
		title: "Place a flock",
		lede: "One action does seven things.",
		blocks: [
			{ type: "text", html:
				"Create the <b>Flock</b> — name, farm, shed, type, breed, strain, placement date, bird item and the number placed. Then press <b>Place Flock</b>." },
			{ type: "list", items: [
				"creates the ERPNext <b>Batch</b> named after the flock",
				"<b>snapshots the breed standard</b> onto the flock",
				"opens a <b>Project</b> as the costing container",
				"generates the <b>Vaccination Plan</b> with real due dates",
				"marks the shed <b>Occupied</b>",
				"posts a <b>Stock Entry</b> receiving the chicks into the shed warehouse",
			] },
			{ type: "note", tone: "info", html:
				"Placing more birds than the shed's capacity gives a <b>warning, not a block</b> — overcrowding is a business decision. Placing a second flock in an occupied shed <b>is blocked</b>: all-in all-out is a biosecurity requirement." },
			{ type: "actions", items: [["Flock list", "list", "Flock"], ["New Flock", "new", "Flock"]] },
		],
	},
	{
		id: "daily",
		icon: "poultry-clipboard",
		title: "The daily entry",
		lede: "One per flock per day. Enter only what you have.",
		blocks: [
			{ type: "table", head: ["Field", "Notes"], rows: [
				["Mortality / Culls", "The first mandatory number. Add a detail row to say why."],
				["Feed", "The second. Enter <b>bags</b> — the system converts to kg."],
				["Eggs", "Enter <b>trays</b>; converted at 30 per tray."],
				["Water, weight, uniformity", "Optional. Weekly weighing is enough."],
				["Environment", "Temperature, humidity, litter, light hours. Optional."],
			] },
			{ type: "text", html:
				"Everything else fills itself: age, opening count (read from the ledger, not carried forward), closing count, mortality %, cumulative feed, feed per bird, water:feed and hen-day production. On submit it posts feed out of the shed, dead birds to the mortality account and eggs into the cold store." },
			{ type: "table", head: ["The system will argue when", "What happens"], rows: [
				["Deaths exceed birds alive", "<b>Blocked</b>"],
				["More than 5% of the flock lost in a day", "Warning; confirm and continue"],
				["Feed above 250 g per bird per day", "Warning; confirm and continue"],
				["Duplicate entry for the same flock and date", "<b>Blocked</b>"],
				["Backdated beyond the window (default 30 days)", "<b>Blocked</b> — a manager raises the limit"],
			] },
			{ type: "note", tone: "ok", html:
				"Backdating <i>within</i> the window is allowed on purpose. Farms miss days, and late data is far more useful than absent data." },
			{ type: "actions", items: [
				["Daily Flock Entry", "list", "Daily Flock Entry"],
				["New entry", "new", "Daily Flock Entry"],
				["Entry Board", "page", "poultry-entry-board"],
			] },
		],
	},
	{
		id: "health",
		icon: "poultry-syringe",
		title: "Health and withdrawal",
		lede: "The highest-value control in the system.",
		blocks: [
			{ type: "text", html:
				"The vaccination plan is generated at placement. Record the real event as a <b>Vaccination Entry</b> including the <b>vial batch and serial</b> — that is what an audit asks for. Submitting it closes the matching planned dose, so compliance reporting reflects reality." },
			{ type: "text", html:
				"Record a <b>Medication Entry</b> and the system sets <b>withdrawal clear date = end date + withdrawal days</b>. Until that date the flock is flagged on every dashboard, listed in the Withdrawal Period Alert report, and <b>any Delivery Note or Sales Invoice carrying its batch is blocked on submit</b>, naming the drug and the date it clears." },
			{ type: "actions", items: [
				["Vaccination Entry", "list", "Vaccination Entry"],
				["Medication Entry", "list", "Medication Entry"],
				["Withdrawal Period Alert", "report", "Withdrawal Period Alert"],
				["Vaccination Compliance", "report", "Vaccination Compliance"],
			] },
		],
	},
	{
		id: "hatchery",
		icon: "poultry-hatchery",
		title: "Hatchery",
		lede: "Setting to dispatch, and the three numbers it is judged on.",
		blocks: [
			{ type: "steps", items: [
				"<b>Egg Setting</b> on day 0 — eggs set, the setter, the source flock and <b>breeder age</b>. Candling, transfer and hatch dates are worked out for you.",
				"<b>Candling Entry</b> on day 18 — clear, dead germ and contaminated. What remains is fertile, and that gives <b>fertility %</b>.",
				"<b>Hatch Entry</b> on day 21 — chicks hatched and cripples. This gives <b>hatchability of set</b> and <b>of fertile</b>; saleable chicks go straight into stock.",
				"<b>Chick Dispatch</b> — boxes, chicks per box, transit temperature, in-ovo vaccination, and whether they go to your own farm or a customer.",
			] },
			{ type: "note", tone: "info", html:
				"<b>Always record breeder age at set.</b> It is the standard explanation for hatchability variation — the same flock at 28 weeks and at 62 weeks are not comparable." },
			{ type: "table", head: ["Number", "What it means"], rows: [
				["Fertility %", "Fertile eggs ÷ eggs set. A breeder-flock and mating problem, not an incubation one."],
				["Hatchability of set %", "Chicks ÷ eggs set. The commercial number."],
				["Hatchability of fertile %", "Chicks ÷ fertile eggs. This one is about the machine and the handling."],
				["Saleable chick %", "Saleable ÷ hatched, after cripples and culls."],
			] },
			{ type: "actions", items: [
				["Egg Setting", "list", "Egg Setting"],
				["Candling Entry", "list", "Candling Entry"],
				["Hatch Entry", "list", "Hatch Entry"],
				["Chick Dispatch", "list", "Chick Dispatch"],
				["Hatchery Performance", "report", "Hatchery Performance"],
			] },
		],
	},
	{
		id: "screens",
		icon: "poultry-board",
		title: "The screens",
		lede: "What each one is for.",
		blocks: [
			{ type: "table", head: ["Screen", "Open it when"], rows: [
				["<b>Management</b>", "One place for sales, purchases, stock and every other screen."],
				["<b>Poultry Control Tower</b>", "The morning check. Every flock as a card, worst first."],
				["<b>Flock 360</b>", "You want one flock end to end, plotted against its standard."],
				["<b>Daily Entry Board</b>", "Catching up after a farm visit; days across, flocks down."],
				["<b>Sales &amp; Purchases</b>", "What went out and came in, today and this month."],
				["<b>Stock on Hand</b>", "Birds, eggs and feed by item and location."],
				["<b>Vaccination &amp; Health</b>", "Doses due, overdue, and what cannot be sold."],
				["<b>Cost &amp; Profitability</b>", "Cost per bird and per kilogram, closed-batch margin."],
			] },
			{ type: "actions", items: [
				["Management", "page", "poultry-manage"],
				["Control Tower", "page", "poultry-tower"],
				["Flock 360", "page", "poultry-flock-360"],
				["Entry Board", "page", "poultry-entry-board"],
				["Sales & Purchases", "page", "poultry-trade"],
				["Stock on Hand", "page", "poultry-stock"],
			] },
		],
	},
	{
		id: "reports",
		icon: "poultry-chart",
		title: "Reports",
		lede: "Eight, and when to read each.",
		blocks: [
			{ type: "table", head: ["Report", "Read it when"], rows: [
				["Flock Performance vs Standard", "You want the day-by-day story of one flock."],
				["Broiler Batch Summary", "Ranking batches by EEF, with cost per kg."],
				["Layer Production Curve", "Checking HDP against standard, and persistency after peak."],
				["Mortality Analysis", "By reason, category, age band, shed, farm or flock."],
				["Feed Consumption and FCR Trend", "Feed cost and the FCR it bought."],
				["Vaccination Compliance", "Before an audit, or when something went wrong."],
				["Withdrawal Period Alert", "Before committing a load to a buyer."],
				["Shed Utilisation and Downtime", "Which sheds are earning and which sit empty."],
			] },
			{ type: "note", tone: "info", html:
				"<b>How to read EEF:</b> below 250 poor, around 300 average, 350+ good, 400+ excellent." },
			{ type: "actions", items: [
				["Broiler Batch Summary", "report", "Broiler Batch Summary"],
				["Flock Performance vs Standard", "report", "Flock Performance vs Standard"],
				["Mortality Analysis", "report", "Mortality Analysis"],
				["All reports", "workspace", "poultry-analytics"],
			] },
		],
	},
	{
		id: "erpnext",
		icon: "poultry-cost",
		title: "What lands in ERPNext",
		lede: "The app drives standard documents; it never replaces them.",
		blocks: [
			{ type: "list", items: [
				"<b>Stock Ledger</b> — chicks in, feed out per shed, mortality written off, eggs in. Every line tagged with its flock.",
				"<b>Stock Balance</b> — live birds per shed, eggs in the cold store.",
				"<b>Batch</b> — one per flock, so a tray of eggs traces back to its feed and medication history.",
				"<b>Project</b> — one per flock, carrying the cost.",
				"<b>Profit and Loss</b> — with mortality write-off as its own expense line.",
			] },
			{ type: "actions", items: [
				["Stock Ledger", "report", "Stock Ledger"],
				["Stock Balance", "report", "Stock Balance"],
				["Stock Entry", "list", "Stock Entry"],
			] },
		],
	},
	{
		id: "trouble",
		icon: "poultry-help",
		title: "When something blocks you",
		lede: "The messages you are most likely to hit.",
		blocks: [
			{ type: "table", head: ["Message", "What to do"], rows: [
				["Shed already holds active flock X", "All-in all-out is enforced. Close the existing flock first."],
				["Entry is N days old; the limit is 30", "Raise <i>Max Backdate Days</i> in Poultry Settings."],
				["Sale blocked with a drug name", "The flock is inside a withdrawal window; the message gives the clear date."],
				["Insufficient stock on a feed issue", "Feed was never received into that <b>shed's</b> warehouse."],
				["Stock Balance disagrees with the flock", "Backdated postings queue repost jobs; let the scheduler finish."],
			] },
			{ type: "actions", items: [["Poultry Settings", "form", "Poultry Settings"]] },
		],
	},
];

class PoultryGuide {
	constructor(page) {
		this.page = page;
		this.inject_styles();
		this.$body = $('<div class="pg"></div>').appendTo(this.page.main);
		this.render();
	}

	inject_styles() {
		if (document.getElementById("pg-styles")) return;
		$(`<style id="pg-styles">
		.pg { display: grid; grid-template-columns: 220px 1fr; gap: 24px; padding-bottom: 3rem; }
		@media (max-width: 900px) { .pg { grid-template-columns: 1fr; } .pg-nav { position: static !important; } }
		.pg .icon { margin: 0; flex: none; }
		.pg-nav { position: sticky; top: 12px; align-self: start; }
		.pg-nav a { display: flex; align-items: center; gap: 8px; padding: 7px 10px;
			border-radius: var(--border-radius-md); color: var(--text-muted);
			font-size: var(--text-sm); text-decoration: none; }
		.pg-nav a:hover { background: var(--bg-light-gray); color: var(--text-color); }
		.pg-nav a.on { background: var(--bg-light-gray); color: var(--text-color); font-weight: 600; }
		.pg-sec { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 20px 22px; margin-bottom: 16px;
			scroll-margin-top: 12px; }
		.pg-sec h3 { display: flex; align-items: center; gap: 9px; margin: 0;
			font-size: 17px; font-weight: 600; }
		.pg-lede { color: var(--text-muted); font-size: var(--text-sm); margin: 4px 0 14px 0; }
		.pg-sec p { font-size: var(--text-md); line-height: 1.65; color: var(--text-color);
			margin: 0 0 10px; }
		.pg-steps { counter-reset: s; padding: 0; margin: 0 0 6px; list-style: none; }
		.pg-steps li { counter-increment: s; position: relative; padding: 0 0 12px 34px;
			font-size: var(--text-md); line-height: 1.6; }
		.pg-steps li::before { content: counter(s); position: absolute; left: 0; top: 0;
			width: 22px; height: 22px; border-radius: 50%; background: var(--bg-light-gray);
			color: var(--text-muted); font-size: 11px; font-weight: 700;
			display: flex; align-items: center; justify-content: center; }
		.pg-list { margin: 0 0 8px; padding-left: 20px; }
		.pg-list li { font-size: var(--text-md); line-height: 1.6; margin-bottom: 5px; }
		.pg-table { width: 100%; border-collapse: collapse; margin: 4px 0 12px;
			font-size: var(--text-sm); }
		.pg-table th { text-align: left; font-weight: 500; color: var(--text-muted);
			font-size: var(--text-xs); text-transform: uppercase; padding: 7px 10px;
			border-bottom: 1px solid var(--border-color); }
		.pg-table td { padding: 9px 10px; border-bottom: 1px solid var(--border-color);
			vertical-align: top; line-height: 1.55; }
		.pg-table tr:last-child td { border-bottom: 0; }
		.pg-note { border-radius: 7px; padding: 10px 12px; font-size: var(--text-sm);
			line-height: 1.6; margin: 4px 0 12px; }
		.pg-note.info { background: var(--blue-50); color: var(--blue-700); }
		.pg-note.ok { background: var(--green-50); color: var(--green-700); }
		.pg-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
		.pg-hero { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 18px 22px; margin-bottom: 16px;
			display: flex; align-items: center; gap: 14px; }
		.pg-hero .t { font-size: 19px; font-weight: 700; color: var(--text-color); }
		.pg-hero .s { color: var(--text-muted); font-size: var(--text-sm); margin-top: 2px; }
		</style>`).appendTo(document.head);
	}

	render() {
		const $nav = $('<div class="pg-nav"></div>').appendTo(this.$body);
		const $main = $('<div class="pg-main"></div>').appendTo(this.$body);

		GUIDE.forEach((s) =>
			$(`<a href="#" data-id="${s.id}">${frappe.utils.icon(s.icon, "sm")}
				<span>${__(s.title)}</span></a>`)
				.appendTo($nav)
				.on("click", (e) => {
					e.preventDefault();
					const el = document.getElementById(`pg-${s.id}`);
					el && el.scrollIntoView({ behavior: "smooth", block: "start" });
					$nav.find("a").removeClass("on");
					$(e.currentTarget).addClass("on");
				})
		);
		$nav.find("a").first().addClass("on");

		$(`<div class="pg-hero">${frappe.utils.icon("poultry-hen", "lg")}
			<div><div class="t">${__("How to use Poultry Management")}</div>
			<div class="s">${__("Written for the people who run the farm, not for the people who built it.")}</div>
			</div></div>`).appendTo($main);

		GUIDE.forEach((s) => {
			const $s = $(`<div class="pg-sec" id="pg-${s.id}">
				<h3>${frappe.utils.icon(s.icon, "md")} ${__(s.title)}</h3>
				<div class="pg-lede">${__(s.lede)}</div>
			</div>`).appendTo($main);
			s.blocks.forEach((b) => this.block($s, b));
		});
	}

	block($s, b) {
		if (b.type === "text") {
			$(`<p>${b.html}</p>`).appendTo($s);
		} else if (b.type === "steps") {
			$(`<ol class="pg-steps">${b.items.map((i) => `<li>${i}</li>`).join("")}</ol>`).appendTo($s);
		} else if (b.type === "list") {
			$(`<ul class="pg-list">${b.items.map((i) => `<li>${i}</li>`).join("")}</ul>`).appendTo($s);
		} else if (b.type === "table") {
			$(`<table class="pg-table">
				<thead><tr>${b.head.map((h) => `<th>${__(h)}</th>`).join("")}</tr></thead>
				<tbody>${b.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody>
			</table>`).appendTo($s);
		} else if (b.type === "note") {
			$(`<div class="pg-note ${b.tone}">${b.html}</div>`).appendTo($s);
		} else if (b.type === "actions") {
			const $a = $('<div class="pg-actions"></div>').appendTo($s);
			b.items.forEach(([label, kind, target]) => {
				$(`<button class="btn btn-default btn-sm">${__(label)}</button>`)
					.appendTo($a)
					.on("click", () => this.go(kind, target));
			});
		}
	}

	go(kind, target) {
		if (kind === "page" || kind === "workspace") frappe.set_route(target);
		else if (kind === "list") frappe.set_route("List", target);
		else if (kind === "form") frappe.set_route("Form", target, target);
		else if (kind === "new") frappe.new_doc(target);
		else if (kind === "report") frappe.set_route("query-report", target);
	}
}
