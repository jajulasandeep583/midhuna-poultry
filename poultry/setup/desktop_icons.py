"""Workspace header icons.

Frappe's sidebar_header.set_header_icon() assigns the Workspace Sidebar's
header_icon and then immediately overwrites it with a generated letter tile, so
that field never reaches the screen. The only path that renders a real image is
a Desktop Icon whose label matches the sidebar title, backed by a file at
  <app>/public/icons/desktop_icons/{solid,subtle}/<scrub(label)>.svg
which frappe indexes into boot.desktop_icon_urls.

So each workspace gets a proper 54x54 app tile, generated from the same glyph
geometry as the sprite so the desk and the tile agree.
"""

import os
import re

import frappe

# workspace -> (sprite symbol, tile colour)
TILES = {
	"Poultry": ("poultry-farm", "#4178D4"),
	"Management": ("poultry-manage", "#4B6A88"),
	"Flock Operations": ("poultry-hen", "#E8A33D"),
	"Poultry Health": ("poultry-syringe", "#17B897"),
	"Hatchery": ("poultry-hatchery", "#D9694B"),
	"Poultry Setup": ("poultry-settings", "#6B7A8F"),
	"Poultry Analytics": ("poultry-chart", "#2CA58D"),
}

# the rounded square erpnext uses, so our tiles sit in the same grid
SQUIRCLE = ("M38.5714 0H15.4286C6.90761 0 0 6.90761 0 15.4286V38.5714C0 47.0924 6.90761 54 "
            "15.4286 54H38.5714C47.0924 54 54 47.0924 54 38.5714V15.4286C54 6.90761 47.0924 0 "
            "38.5714 0Z")

SCALE = 1.45          # 24 -> 34.8 within a 54 canvas
OFFSET = (54 - 24 * SCALE) / 2


def glyphs():
	"""Pull each symbol's inner geometry straight out of the sprite."""
	path = frappe.get_app_path("poultry", "public", "icons", "poultry-icons.svg")
	src = open(path, encoding="utf-8").read()
	out = {}
	for m in re.finditer(r'<symbol[^>]*id="icon-(poultry-[a-z0-9-]+)"[^>]*>(.*?)</symbol>',
	                     src, re.S):
		out[m.group(1)] = m.group(2).strip()
	return out


def tile(inner, colour, solid):
	bg = (f'<path d="{SQUIRCLE}" fill="{colour}"/>' if solid
	      else f'<path d="{SQUIRCLE}" fill="{colour}" fill-opacity="0.12"/>')
	stroke = "#FFFFFF" if solid else colour
	return (
		'<svg width="54" height="54" viewBox="0 0 54 54" fill="none" '
		'xmlns="http://www.w3.org/2000/svg">\n'
		f"{bg}\n"
		f'<g transform="translate({OFFSET:.2f} {OFFSET:.2f}) scale({SCALE})" fill="none" '
		f'stroke="{stroke}" stroke-width="1.9" stroke-linecap="round" '
		f'stroke-linejoin="round">\n{inner}\n</g>\n</svg>\n'
	)


def write_tile_files():
	"""Regenerate the tile SVGs from the sprite - build-time convenience only.

	The generated files are COMMITTED to the repo, so a deployed site never
	needs this to run. That matters: on Frappe Cloud the app tree is not
	writable at runtime, and when this ran FIRST inside install() the
	open()-for-write raised, aborted the rest of setup, and the Desktop Icon
	records were never made - the desk then showed letter tiles. Best-effort:
	skip files whose content already matches, swallow filesystem errors.
	"""
	written = 0
	try:
		g = glyphs()
		base = frappe.get_app_path("poultry", "public", "icons", "desktop_icons")
		for variant in ("solid", "subtle"):
			os.makedirs(os.path.join(base, variant), exist_ok=True)
		for label, (symbol, colour) in TILES.items():
			inner = g.get(symbol)
			if not inner:
				print(f"  ! no glyph for {symbol}")
				continue
			fname = frappe.scrub(label) + ".svg"
			for variant, solid in (("solid", True), ("subtle", False)):
				target = os.path.join(base, variant, fname)
				content = tile(inner, colour, solid)
				if os.path.exists(target) and open(target, encoding="utf-8").read() == content:
					continue
				with open(target, "w", encoding="utf-8") as fh:
					fh.write(content)
				written += 1
	except OSError as e:
		print(f"  ! app tree not writable ({e}) - keeping the committed tile files")
		return
	print(f"  + desktop icon files refreshed: {written}")


def install():
	# Records first, files last: the records are what make the desk tiles and
	# workspace header icons render, and the file write may legitimately fail
	# on a read-only app tree (Frappe Cloud).
	# a Desktop Icon record must exist, with app=poultry, for the lookup to fire
	for label, (symbol, colour) in TILES.items():
		if not frappe.db.exists("Workspace", label):
			continue
		name = frappe.db.get_value("Desktop Icon", {"label": label})
		if name:
			doc = frappe.get_doc("Desktop Icon", name)
		else:
			doc = frappe.new_doc("Desktop Icon")
			doc.label = label
		doc.app = "poultry"
		doc.icon = symbol
		doc.icon_type = "Link"
		doc.standard = 1
		doc.hidden = 0
		# Each workspace stands on its own on the desk. Left nested under the
		# app tile they never appear there at all - only the three that
		# happened to have no parent were showing.
		doc.parent_icon = None

		# Link through the Workspace Sidebar, never as "External". On current
		# version-16 (what Frappe Cloud runs) desktop.js prefixes an External
		# icon's link with window.location.origin and then puts
		# target="_blank" on any route that starts with http - every tile
		# opens a NEW TAB. External icons are also dropped from the
		# app-switcher sibling menu (build_folder_map filters them out).
		# The sidebar records this points at ship as app-level JSON in
		# poultry/workspace_sidebar/ and are synced on every migrate, and
		# sidebar.install() runs before this in setup, so the boot lookup
		# desktop.js does (frappe.boot.workspace_sidebar_item[label.lower()])
		# cannot miss on a migrated site.
		doc.link = None
		if frappe.db.exists("Workspace Sidebar", label):
			doc.link_type = "Workspace Sidebar"
			doc.link_to = label
			doc.sidebar = label
		doc.flags.ignore_permissions = True
		doc.save()

	# frappe generates an "App"-type icon for every installed app from the
	# add_to_apps_screen hook, always link_type External - which current
	# version-16 opens in a NEW TAB (origin-prefixed route -> target=_blank).
	# Ours has no child icons (the workspace tiles sit flat on the desk, not
	# nested under it), so it is only a redundant duplicate of the Poultry
	# tile. Hide it.
	if frappe.db.exists("Desktop Icon", {"label": "Poultry Management", "icon_type": "App"}):
		frappe.db.set_value(
			"Desktop Icon",
			{"label": "Poultry Management", "icon_type": "App"},
			"hidden",
			1,
		)
	frappe.db.commit()
	frappe.clear_cache()
	print(f"  + desktop icon records: {len(TILES)}")

	write_tile_files()


run = install
