frappe.pages["poultry-entry-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Daily Entry Board"),
		single_column: true,
	});
	wrapper.entry_board = new EntryBoard(page);
};

frappe.pages["poultry-entry-board"].on_page_show = function (wrapper) {
	wrapper.entry_board && wrapper.entry_board.load();
};

class EntryBoard {
	constructor(page) {
		this.page = page;
		this.days = 14;
		this.inject_styles();

		this.range = this.page.add_select(__("Days"), ["7", "14", "21", "30"]);
		this.range.val("14");
		this.range.on("change", () => {
			this.days = parseInt(this.range.val(), 10);
			this.load();
		});

		this.$body = $('<div class="eb"></div>').appendTo(this.page.main);
		this.page.set_primary_action(__("Refresh"), () => this.load(), "refresh");
		this.load();
	}

	inject_styles() {
		if (document.getElementById("eb-styles")) return;
		$(`<style id="eb-styles">
		.eb { padding-bottom: 2rem; }
		.eb .icon { margin: 0; flex: none; }
		.eb-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
			margin-bottom: 1rem; }
		.eb-lede { color: var(--text-muted); font-size: var(--text-sm); }
		.eb-stat { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); padding: 8px 14px; }
		.eb-stat .l { font-size: var(--text-xs); color: var(--text-muted);
			text-transform: uppercase; letter-spacing: .04em; }
		.eb-stat .v { font-size: 18px; font-weight: 700; color: var(--text-color); }
		.eb-stat.bad .v { color: var(--red-500); }
		.eb-stat.good .v { color: var(--green-600); }
		.eb-wrap { background: var(--card-bg); border: 1px solid var(--border-color);
			border-radius: var(--border-radius-md); overflow-x: auto; }
		.eb-grid { border-collapse: separate; border-spacing: 0; width: 100%;
			font-size: var(--text-sm); }
		.eb-grid th, .eb-grid td { padding: 0; }
		.eb-grid thead th { position: sticky; top: 0; background: var(--card-bg); z-index: 2;
			font-weight: 500; font-size: 10px; color: var(--text-muted); text-align: center;
			padding: 8px 0 6px; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
		.eb-grid th.flockcol, .eb-grid td.flockcol { position: sticky; left: 0; z-index: 3;
			background: var(--card-bg); text-align: left; padding: 8px 12px; min-width: 230px;
			border-right: 1px solid var(--border-color); }
		.eb-grid tbody td { border-bottom: 1px solid var(--border-color); }
		.eb-grid tbody tr:last-child td { border-bottom: 0; }
		.eb-name { font-weight: 600; color: var(--text-color); white-space: nowrap; }
		.eb-sub { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap;
			overflow: hidden; text-overflow: ellipsis; max-width: 300px; }
		.eb-cell { width: 30px; height: 30px; margin: 3px auto; border-radius: 5px;
			cursor: pointer; display: flex; align-items: center; justify-content: center;
			font-size: 10px; font-weight: 600; }
		.eb-cell.done    { background: var(--green-100); color: var(--green-700); }
		.eb-cell.alert   { background: var(--red-100);   color: var(--red-600); }
		.eb-cell.missing { background: var(--bg-light-gray); color: var(--text-light);
			border: 1px dashed var(--border-color); }
		.eb-cell.na      { background: transparent; cursor: default; }
		.eb-cell:hover:not(.na) { outline: 2px solid var(--blue-400); }
		.eb-miss { font-size: var(--text-xs); font-weight: 600; }
		.eb-miss.zero { color: var(--green-600); }
		.eb-miss.some { color: var(--red-500); }
		.eb-legend { display: flex; gap: 16px; align-items: center; margin-top: 12px;
			font-size: var(--text-xs); color: var(--text-muted); }
		.eb-legend span.k { width: 14px; height: 14px; border-radius: 4px;
			display: inline-block; vertical-align: -3px; margin-right: 5px; }
		.eb-empty { padding: 24px; text-align: center; color: var(--text-muted); }
		</style>`).appendTo(document.head);
	}

	load() {
		this.$body.html(`<div class="text-muted" style="padding:2rem 0">${__("Loading...")}</div>`);
		frappe.call({ method: "poultry.dashboard.entry_board", args: { days: this.days } })
			.then((r) => {
				if (!r || !r.message) return;
				this.data = r.message;
				this.render();
			});
	}

	render() {
		const d = this.data;
		this.$body.empty();

		$(`<div class="eb-head">
			${frappe.utils.icon("poultry-board", "lg")}
			<div>
				<div class="eb-lede">${__("Every active flock against the last {0} days. A gap is a day nobody recorded — click it to enter that day.", [this.days])}</div>
			</div>
			<span style="flex:1"></span>
			<div class="eb-stat ${d.total_missing ? "bad" : "good"}">
				<div class="l">${__("Days Missing")}</div><div class="v">${d.total_missing}</div>
			</div>
			<div class="eb-stat ${d.coverage_pct >= 95 ? "good" : "bad"}">
				<div class="l">${__("Coverage")}</div><div class="v">${d.coverage_pct}%</div>
			</div>
		</div>`).appendTo(this.$body);

		if (!d.board.length) {
			$(`<div class="eb-wrap"><div class="eb-empty">${__("No active flocks.")}</div></div>`)
				.appendTo(this.$body);
			return;
		}

		const head = d.dates.map((x) => {
			const dt = frappe.datetime.str_to_obj(x);
			const dd = String(dt.getDate()).padStart(2, "0");
			const mon = dt.toLocaleString("en", { month: "short" });
			return `<th title="${frappe.datetime.str_to_user(x)}">${dd}<br>${mon}</th>`;
		}).join("");

		const body = d.board.map((row) => {
			const cells = row.cells.map((c) => {
				const tip = c.state === "na"
					? __("Before placement")
					: c.entry
						? `${frappe.datetime.str_to_user(c.date)} — ${__("lost")} ${c.losses}, ${__("feed")} ${c.feed} kg${c.eggs ? `, ${__("eggs")} ${c.eggs}` : ""}`
						: `${frappe.datetime.str_to_user(c.date)} — ${__("no entry")}`;
				const mark = c.state === "done" ? "✓" : c.state === "alert" ? "!" : "";
				return `<td><div class="eb-cell ${c.state}" title="${tip}"
					data-flock="${row.flock}" data-date="${c.date}"
					data-entry="${c.entry || ""}" data-state="${c.state}">${mark}</div></td>`;
			}).join("");
			return `<tr>
				<td class="flockcol">
					<div class="eb-name">${frappe.utils.escape_html(row.flock_name)}</div>
					<div class="eb-sub">${frappe.utils.escape_html(row.shed)} &middot; ${Number(row.birds || 0).toLocaleString("en-IN")} ${__("birds")} &middot; <span class="eb-miss ${row.missing ? "some" : "zero"}">${row.missing ? __("{0} missing", [row.missing]) : __("complete")}</span></div>
				</td>${cells}</tr>`;
		}).join("");

		const $wrap = $(`<div class="eb-wrap"><table class="eb-grid">
			<thead><tr><th class="flockcol">${__("Flock")}</th>${head}</tr></thead>
			<tbody>${body}</tbody></table></div>`).appendTo(this.$body);

		$wrap.on("click", ".eb-cell", function () {
			const $c = $(this);
			if ($c.data("state") === "na") return;
			const entry = $c.data("entry");
			if (entry) {
				frappe.set_route("Form", "Daily Flock Entry", entry);
			} else {
				frappe.new_doc("Daily Flock Entry", {
					flock: $c.data("flock"),
					posting_date: $c.data("date"),
					entry_source: "Catch-up",
				});
			}
		});

		$(`<div class="eb-legend">
			<div><span class="k" style="background:var(--green-100)"></span>${__("Recorded")}</div>
			<div><span class="k" style="background:var(--red-100)"></span>${__("Recorded with an alert")}</div>
			<div><span class="k" style="background:var(--bg-light-gray);border:1px dashed var(--border-color)"></span>${__("Missing — click to enter")}</div>
		</div>`).appendTo(this.$body);
	}
}
