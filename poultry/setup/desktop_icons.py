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


def install():
	g = glyphs()
	base = frappe.get_app_path("poultry", "public", "icons", "desktop_icons")
	for variant in ("solid", "subtle"):
		os.makedirs(os.path.join(base, variant), exist_ok=True)

	written = 0
	for label, (symbol, colour) in TILES.items():
		inner = g.get(symbol)
		if not inner:
			print(f"  ! no glyph for {symbol}")
			continue
		fname = frappe.scrub(label) + ".svg"
		for variant, solid in (("solid", True), ("subtle", False)):
			with open(os.path.join(base, variant, fname), "w", encoding="utf-8") as fh:
				fh.write(tile(inner, colour, solid))
		written += 1
	print(f"  + desktop icon files: {written} x 2 variants")

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

		# Route explicitly rather than through a Workspace Sidebar link.
		# desktop.js resolves a "Workspace Sidebar" icon by looking the label up
		# in frappe.boot.workspace_sidebar_item and reading its first link; if
		# that lookup misses on a given site there is NO fallback and clicking
		# the tile only says "Icon is not correctly configured". An External
		# link needs no boot lookup and works on any site.
		doc.link_type = "External"
		doc.link = f"/app/{frappe.scrub(label).replace('_', '-')}"
		doc.link_to = None
		if frappe.db.exists("Workspace Sidebar", label):
			doc.sidebar = label
		doc.flags.ignore_permissions = True
		doc.save()
	frappe.db.commit()
	frappe.clear_cache()
	print(f"  + desktop icon records: {len(TILES)}")


run = install
