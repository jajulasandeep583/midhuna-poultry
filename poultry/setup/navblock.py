"""A Custom HTML Block of big navigation tiles, placed at the top of each
workspace.

Frappe renders a Custom HTML Block inside a **shadow root**, so neither the
icon sprite (`<use href="#icon-...">` cannot cross the boundary) nor the desk
stylesheet reaches it. Every icon is therefore inlined with its own explicit
stroke, and the tiles use plain anchors so no script is needed either.
"""

import frappe

BLOCK = "Poultry Navigator"

# path geometry copied from public/icons/poultry-icons.svg
GLYPHS = {
	"alert": '<path d="M10.3 3.9 1.9 18a2 2 0 0 0 1.7 3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>'
	         '<path d="M12 9.2v4.4M12 17.2h.01"/>',
	"board": '<rect x="2.8" y="4.4" width="18.4" height="15.2" rx="2"/>'
	         '<path d="M2.8 9.2h18.4M8.4 9.2v10.4M14.6 9.2v10.4"/>'
	         '<path d="M4.8 12.4h2M11 12.4h2M17.2 12.4h2"/>',
	"target": '<circle cx="12" cy="12" r="8.8"/><circle cx="12" cy="12" r="5"/>'
	          '<circle cx="12" cy="12" r="1.4"/>',
	"syringe": '<path d="M17.6 2.6 21.4 6.4"/><path d="M15.9 4.3 19.7 8.1"/>'
	           '<path d="M13.4 6.8 17.2 10.6 9.1 18.7 4.6 19.9 5.8 15.4Z"/>'
	           '<path d="M10.3 9.9 14.1 13.7"/><path d="M2.6 21.4 4.6 19.4"/>',
	"cost": '<circle cx="12" cy="12" r="9.2"/>'
	        '<path d="M9 7.6h6M9 10.6h6M9 7.6c2.6 0 3.6 1.4 3.6 3s-1 3-3.6 3l5.4 5"/>',
	"guide": '<path d="M2.8 4.6a2 2 0 0 1 2-2H10a2.6 2.6 0 0 1 2 1.2 2.6 2.6 0 0 1 2-1.2h5.2a2 2 0 0 1 2 2v12.6a1.6 1.6 0 0 1-1.6 1.6H14.4A2.4 2.4 0 0 0 12 21a2.4 2.4 0 0 0-2.4-2.2H4.4a1.6 1.6 0 0 1-1.6-1.6Z"/>'
	         '<path d="M12 3.8V21"/><path d="M5.6 7.4h3.6M5.6 10.6h3.6M14.8 7.4h3.6M14.8 10.6h3.6"/>',
	"manage": '<rect x="2.8" y="2.8" width="7.6" height="7.6" rx="1.6"/>'
	          '<rect x="13.6" y="2.8" width="7.6" height="7.6" rx="1.6"/>'
	          '<rect x="2.8" y="13.6" width="7.6" height="7.6" rx="1.6"/>'
	          '<rect x="13.6" y="13.6" width="7.6" height="7.6" rx="1.6"/>',
	"sales": '<path d="M3.4 5.4a2 2 0 0 1 2-2h5.3a2 2 0 0 1 1.4.6l8 8a2 2 0 0 1 0 2.8l-5.3 5.3a2 2 0 0 1-2.8 0l-8-8a2 2 0 0 1-.6-1.4Z"/>'
	         '<circle cx="8.2" cy="8.2" r="1.6"/>'
	         '<path d="M13.6 12.2h3.4M13.6 15h3.4M13.6 12.2c1.5 0 2.1.8 2.1 1.7s-.6 1.7-2.1 1.7l3.1 2.9"/>',
	"stock": '<rect x="2.6" y="12.6" width="8" height="8" rx="1.2"/>'
	         '<rect x="13.4" y="12.6" width="8" height="8" rx="1.2"/>'
	         '<rect x="8" y="3.4" width="8" height="8" rx="1.2"/>'
	         '<path d="M4.8 12.6v-1M18.6 12.6v-1M12 12.6v-1.2"/>',
	"hatchery": '<rect x="3.4" y="4.2" width="17.2" height="16.4" rx="2.4"/>'
	            '<path d="M12 8.4c1.7 0 3.1 2.1 3.1 4.3 0 2.3-1.4 3.8-3.1 3.8s-3.1-1.5-3.1-3.8c0-2.2 1.4-4.3 3.1-4.3Z"/>'
	            '<path d="M3.4 8.6h17.2"/><path d="M7 6.4h.01M9.6 6.4h.01"/>',
	"hen": '<path d="M8.8 6.4c.9-1.3 2.7-1.3 3.6 0 1-1.1 2.8-.6 3 1"/>'
	       '<circle cx="11.4" cy="13.4" r="6.2"/>'
	       '<path d="M17.6 12.6 21.8 13.8 17.6 15"/><circle cx="14.2" cy="11.6" r="1"/>',
}

TILES = [
	("poultry-manage", "manage", "#4B6A88", "Management",
	 "Sales, purchases, stock and every screen in one place"),
	("poultry-trade", "sales", "#1F9254", "Sales &amp; Purchases",
	 "Sold and bought today, this week, this month"),
	("poultry-stock", "stock", "#4178D4", "Stock on Hand",
	 "Birds, eggs and feed by item and location"),
	("poultry-tower", "alert", "#E2703A", "Control Tower",
	 "Every flock ranked by what needs attention"),
	("poultry-entry-board", "board", "#4B6A88", "Daily Entry Board",
	 "Days across, flocks down. Fill the gaps"),
	("poultry-flock-360", "target", "#6C4BE0", "Flock 360",
	 "One flock, end to end, against its standard"),
	("poultry-health-hub", "syringe", "#17B897", "Vaccination &amp; Health",
	 "Doses due, overdue, and what cannot be sold"),
	("poultry-cost-hub", "cost", "#1F9254", "Cost &amp; Profitability",
	 "Cost per bird and per kilogram, by flock"),
	("hatchery", "hatchery", "#D9694B", "Hatchery",
	 "Setting, candling, hatch and chick dispatch"),
	("flock-operations", "hen", "#E8A33D", "Flock Operations",
	 "Flocks, daily entries, weighings and closure"),
	("poultry-guide", "guide", "#3E7BB6", "How to Use Poultry",
	 "The guide, with a button to every screen"),
]

STYLE = """
.pnav { display: grid; grid-template-columns: repeat(auto-fit, minmax(248px, 1fr));
	gap: 12px; margin: 2px 0 4px;
	font-family: var(--font-stack, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif); }
.pnav-tile { display: flex; gap: 12px; align-items: flex-start; text-decoration: none;
	background: var(--card-bg, #fff); border: 1px solid var(--border-color, #e2e4e9);
	border-radius: 10px; padding: 14px 15px; position: relative; overflow: hidden;
	transition: box-shadow .15s ease, transform .15s ease; }
.pnav-tile::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
	background: var(--c); }
.pnav-tile:hover { box-shadow: 0 4px 14px rgba(0,0,0,.08); transform: translateY(-1px);
	text-decoration: none; }
.pnav-ic { width: 40px; height: 40px; border-radius: 11px; flex: none;
	display: flex; align-items: center; justify-content: center; background: var(--tint); }
.pnav-ic svg { width: 22px; height: 22px; }
.pnav-t { font-weight: 600; color: var(--text-color, #1f272e); font-size: 14px;
	line-height: 1.3; display: block; }
.pnav-s { color: var(--text-muted, #7c7f83); font-size: 11.5px; margin-top: 3px;
	line-height: 1.45; display: block; }
"""


def tint(hexcolour):
	"""A soft wash of the tile colour, computed here because color-mix is not
	safe to rely on inside the shadow root."""
	r, g, b = (int(hexcolour[i:i + 2], 16) for i in (1, 3, 5))
	return f"rgba({r},{g},{b},0.13)"


def html():
	tiles = []
	for route, glyph, colour, title, sub in TILES:
		svg = (f'<svg viewBox="0 0 24 24" fill="none" stroke="{colour}" stroke-width="1.7" '
		       f'stroke-linecap="round" stroke-linejoin="round">{GLYPHS[glyph]}</svg>')
		tiles.append(
			f'<a class="pnav-tile" href="/app/{route}" '
			f'style="--c:{colour};--tint:{tint(colour)}">'
			f'<span class="pnav-ic">{svg}</span>'
			f'<span><span class="pnav-t">{title}</span>'
			f'<span class="pnav-s">{sub}</span></span></a>'
		)
	return '<div class="pnav">' + "".join(tiles) + "</div>"


def install():
	import json

	if frappe.db.exists("Custom HTML Block", BLOCK):
		doc = frappe.get_doc("Custom HTML Block", BLOCK)
	else:
		doc = frappe.new_doc("Custom HTML Block")
		doc.name = BLOCK
	doc.html = html()
	doc.style = STYLE
	doc.script = ""
	doc.private = 0
	doc.flags.ignore_permissions = True
	doc.save()
	print(f"  + custom html block: {BLOCK}")

	for ws in ("Poultry", "Management", "Flock Operations", "Poultry Health",
	           "Hatchery", "Poultry Setup", "Poultry Analytics"):
		if not frappe.db.exists("Workspace", ws):
			continue
		w = frappe.get_doc("Workspace", ws)
		if not any(r.custom_block_name == BLOCK for r in w.custom_blocks):
			w.append("custom_blocks", {"custom_block_name": BLOCK, "label": BLOCK})
		blocks = [b for b in json.loads(w.content or "[]") if b.get("type") != "custom_block"]
		blocks.insert(0, {"id": "pnav000", "type": "custom_block",
		                  "data": {"custom_block_name": BLOCK, "col": 12}})
		w.content = json.dumps(blocks)
		w.flags.ignore_permissions = True
		w.save()
		print(f"  + navigator on {ws}")

	frappe.db.commit()
	frappe.clear_cache()


run = install
