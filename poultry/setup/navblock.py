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
}

TILES = [
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

	for ws in ("Poultry", "Poultry Setup", "Poultry Health", "Poultry Analytics"):
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
