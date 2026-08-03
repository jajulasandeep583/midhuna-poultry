"""Field-client API (§8).

Design rules that shape every response here:
  - minimal payloads, because the client runs on 2G
  - idempotent writes keyed on (flock, date), so an offline retry is safe
  - every field except the flock reference is optional
  - no derived metrics go back to the field: a status colour and one plain
    sentence, never "FCR 1.62", which means nothing in a shed

v16 rejects state-changing whitelisted methods called over GET, so all three
write endpoints declare methods=["POST"] explicitly (§8.1).
"""

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from poultry.poultry_utils import age_days, standard_row


# ------------------------------------------------------------------ reads
@frappe.whitelist()
def get_my_flocks():
	"""Active flocks for the caller, with today's entry status and how many
	days are outstanding."""
	flocks = frappe.get_all(
		"Flock",
		filters={"status": ["not in", ["Draft", "Closed"]]},
		fields=["name", "flock_name", "farm", "shed", "flock_type", "placement_date",
		        "current_qty", "status"],
		order_by="farm asc, shed asc",
	)
	today = getdate(nowdate())
	out = []
	for f in flocks:
		# NOT "max(posting_date)": v16's query builder rejects aggregates in the
		# select list (§2.4.2). Order and take the first row instead.
		last = frappe.db.get_value(
			"Daily Flock Entry", {"flock": f.name, "docstatus": 1}, "posting_date",
			order_by="posting_date desc"
		)
		# days still owed: every date after the last submitted entry, up to today
		if last:
			pending = max(0, (today - getdate(last)).days)
		else:
			pending = age_days(f.placement_date, today)
		out.append({
			"flock": f.name,
			"name": f.flock_name,
			"farm": f.farm,
			"shed": f.shed,
			"birds": cint(f.current_qty),
			"age_days": age_days(f.placement_date, today),
			"entered_today": bool(last and getdate(last) == today),
			"pending_days": cint(pending),
		})
	return out


@frappe.whitelist()
def get_flock(flock):
	"""Everything the entry screen needs in one call, including the feed to
	suggest for today's age."""
	doc = frappe.get_doc("Flock", flock)
	age = age_days(doc.placement_date, nowdate())
	std = standard_row(flock, age)

	feed_types = frappe.get_all(
		"Feed Type",
		filters={"flock_type": doc.flock_type},
		fields=["name", "item", "bag_weight_kg", "age_from_days", "age_to_days"],
	)
	suggested = None
	for ft in feed_types:
		if cint(ft.age_from_days) <= age <= (cint(ft.age_to_days) or 999):
			suggested = ft
			break

	yesterday_feed = frappe.db.sql(
		"""
		select total_feed_kg from `tabDaily Flock Entry`
		where flock = %s and docstatus = 1 order by posting_date desc limit 1
		""",
		flock,
	)

	return {
		"flock": doc.name,
		"name": doc.flock_name,
		"farm": doc.farm,
		"shed": doc.shed,
		"birds": cint(doc.current_qty),
		"age_days": age,
		"feed_types": feed_types,
		"suggested_feed": suggested,
		# feed rarely changes day to day, so default today to yesterday (§11.4)
		"last_feed_kg": flt(yesterday_feed[0][0]) if yesterday_feed else 0.0,
		"mortality_reasons": frappe.get_all("Mortality Reason", pluck="name"),
		"egg_grades": frappe.get_all("Egg Grade", filters={"is_reject": 0}, pluck="name")
		if doc.flock_type in ("Layer", "Breeder") else [],
		"standard_feed_g": flt(std.std_daily_feed_g) if std else 0.0,
	}


@frappe.whitelist()
def get_flock_status(flock):
	"""Status colour and one sentence, without writing anything."""
	doc = frappe.db.get_value(
		"Flock", flock, ["flock_name", "current_qty", "mortality_pct", "status"], as_dict=True
	)
	if not doc:
		frappe.throw(_("Unknown flock"))
	last = frappe.db.get_value(
		"Daily Flock Entry", {"flock": flock, "docstatus": 1}, "posting_date",
		order_by="posting_date desc"
	)
	alert = frappe.db.get_value(
		"Daily Flock Entry",
		{"flock": flock, "docstatus": 1, "has_alert": 1},
		["alert_message", "posting_date"],
		order_by="posting_date desc",
		as_dict=True,
	)
	if alert and last and getdate(alert.posting_date) == getdate(last):
		return {"colour": "red", "message": alert.alert_message.split("\n")[0]}
	if not last or getdate(last) < getdate(nowdate()):
		return {"colour": "amber", "message": _("Today's entry is not in yet.")}
	return {"colour": "green", "message": _("{0} birds, all normal.").format(cint(doc.current_qty))}


# ------------------------------------------------------------------ writes
@frappe.whitelist(methods=["POST"])
def submit_daily_entry(flock, posting_date=None, mortality_qty=0, cull_qty=0, feed_bags=0,
                       feed_type=None, water_litres=0, avg_body_weight_g=0, egg_trays=0,
                       egg_grade=None, remarks=None, entry_source="Field App"):
	"""The single write. Accepts bags and trays; conversion is server-side.

	Idempotent on (flock, posting_date): re-posting the same day updates the
	draft rather than creating a duplicate, so an offline client can retry.
	"""
	posting_date = posting_date or nowdate()
	existing = frappe.db.get_value(
		"Daily Flock Entry",
		{"flock": flock, "posting_date": posting_date, "docstatus": ["<", 2]},
		["name", "docstatus"], as_dict=True,
	)
	if existing and existing.docstatus == 1:
		return {"ok": True, "entry": existing.name, "message": _("Already recorded for this day.")}

	doc = frappe.get_doc("Daily Flock Entry", existing.name) if existing else frappe.new_doc(
		"Daily Flock Entry")
	doc.flock = flock
	doc.posting_date = posting_date
	doc.entry_source = entry_source
	doc.mortality_qty = cint(mortality_qty)
	doc.cull_qty = cint(cull_qty)
	doc.water_litres = flt(water_litres)
	doc.avg_body_weight_g = flt(avg_body_weight_g)
	doc.remarks = remarks

	doc.set("feed_details", [])
	if flt(feed_bags):
		ft = feed_type or _default_feed_type(flock, posting_date)
		doc.append("feed_details", {"feed_type": ft, "bags": flt(feed_bags)})

	doc.set("egg_details", [])
	if flt(egg_trays):
		doc.append("egg_details", {"egg_grade": egg_grade or _default_egg_grade(),
		                           "trays": flt(egg_trays)})

	doc.flags.ignore_permissions = True
	doc.save()
	doc.submit()
	return {"ok": True, "entry": doc.name, "message": _("Saved.")}


@frappe.whitelist(methods=["POST"])
def submit_nothing_happened(flock, posting_date=None):
	"""Most days on a healthy flock are exactly this: no deaths, standard feed.
	One action, one tap (§11.4)."""
	posting_date = posting_date or nowdate()
	info = get_flock(flock)
	bag_weight = flt((info.get("suggested_feed") or {}).get("bag_weight_kg")) or 50.0
	bags = flt(info.get("last_feed_kg")) / bag_weight if info.get("last_feed_kg") else 0
	return submit_daily_entry(
		flock=flock, posting_date=posting_date, mortality_qty=0, cull_qty=0,
		feed_bags=bags, feed_type=(info.get("suggested_feed") or {}).get("name"),
		entry_source="Field App", remarks="Nothing happened",
	)


@frappe.whitelist(methods=["POST"])
def sync_batch(entries):
	"""Bulk upload of queued offline rows. Each row succeeds or fails on its
	own - one bad day never blocks the rest."""
	if isinstance(entries, str):
		entries = json.loads(entries)
	results = []
	for row in entries:
		try:
			res = submit_daily_entry(**row)
			frappe.db.commit()
			results.append({"flock": row.get("flock"), "date": row.get("posting_date"), **res})
		except Exception as e:
			frappe.db.rollback()
			results.append({
				"flock": row.get("flock"), "date": row.get("posting_date"),
				"ok": False, "message": str(e),
			})
	return results


def _default_feed_type(flock, posting_date):
	doc = frappe.db.get_value("Flock", flock, ["flock_type", "placement_date"], as_dict=True)
	age = age_days(doc.placement_date, posting_date)
	for ft in frappe.get_all(
		"Feed Type", filters={"flock_type": doc.flock_type},
		fields=["name", "age_from_days", "age_to_days"], order_by="age_from_days asc"
	):
		if cint(ft.age_from_days) <= age <= (cint(ft.age_to_days) or 999):
			return ft.name
	return None


def _default_egg_grade():
	return frappe.db.get_value("Egg Grade", {"is_reject": 0, "is_saleable": 1}, "name")
