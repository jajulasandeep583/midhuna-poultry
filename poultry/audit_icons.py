"""Audit: what icon is configured where, and is anything duplicated."""

import os
import re
from collections import Counter

import frappe


def run():
	sprite = frappe.get_app_path("poultry", "public", "icons", "poultry-icons.svg")
	ids = re.findall(r'id="icon-(poultry-[a-z0-9-]+)"', open(sprite, encoding="utf-8").read())
	print(f"SPRITE: {len(ids)} poultry symbols")
	# frappe ships these; using one is deliberate, not a missing icon
	FRAPPE_BUILTINS = {"home", "setting", "list", "table", "organization", "users"}
	ids = list(ids) + sorted(FRAPPE_BUILTINS)

	print("\nWORKSPACES (module Poultry Management)")
	ws = frappe.get_all("Workspace", filters={"module": "Poultry Management"},
	                    fields=["name", "icon", "parent_page", "public", "sequence_id"],
	                    order_by="sequence_id")
	for w in ws:
		mark = "" if (w.icon or "") in ids else "   <-- NOT IN SPRITE"
		print(f"  {w.name:<22} icon={str(w.icon):<20} parent={str(w.parent_page):<10}{mark}")
	print(f"  total workspaces: {len(ws)}")
	dupes = [i for i, n in Counter([w.icon for w in ws]).items() if n > 1]
	print(f"  duplicate workspace icons: {dupes or 'none'}")

	print("\nWORKSPACE SIDEBARS")
	for sb in frappe.get_all("Workspace Sidebar", filters={"app": "poultry"},
	                         fields=["name", "header_icon"], order_by="name"):
		items = frappe.db.sql(
			"""select label, icon from `tabWorkspace Sidebar Item`
			   where parent = %s order by idx""", sb.name, as_dict=True)
		icons = [i.icon for i in items]
		blank = [i.label for i in items if not i.icon]
		missing = sorted({i for i in icons if i and i not in ids})
		dup = [i for i, n in Counter([i for i in icons if i]).items() if n > 1]
		print(f"  {sb.name:<22} header={str(sb.header_icon):<18} items={len(items)}")
		if blank:
			print(f"      blank icons: {blank}")
		if missing:
			print(f"      NOT IN SPRITE: {missing}")
		if dup:
			print(f"      repeated within this sidebar: {dup}")

	print("\nDOCTYPE ICONS")
	dts = frappe.get_all("DocType", filters={"module": "Poultry Management", "istable": 0},
	                     fields=["name", "icon"], order_by="name")
	no_icon = [d.name for d in dts if not d.icon]
	bad = [(d.name, d.icon) for d in dts if d.icon and d.icon not in ids]
	print(f"  {len(dts)} doctypes, {len(dts) - len(no_icon)} with an icon")
	if no_icon:
		print(f"  without an icon: {no_icon}")
	if bad:
		print(f"  icon not in sprite: {bad}")

	print("\nDESK PAGES")
	for p in frappe.get_all("Page", filters={"module": "Poultry Management"},
	                        fields=["name", "title", "icon"], order_by="name"):
		mark = "" if (p.icon or "") in ids else "   <-- NOT IN SPRITE"
		print(f"  {p.name:<22} {p.title:<24} icon={str(p.icon)}{mark}")

	used = set()
	for w in ws:
		used.add(w.icon)
	for i in frappe.db.sql(
		"""select distinct icon from `tabWorkspace Sidebar Item`
		   where parent in (select name from `tabWorkspace Sidebar` where app='poultry')"""):
		used.add(i[0])
	for d in dts:
		used.add(d.icon)
	unused = sorted(set(ids) - {u for u in used if u})
	print(f"\nSPRITE COVERAGE: {len(ids)} drawn, {len({u for u in used if u} & set(ids))} in use")
	print(f"  never used: {unused}")
