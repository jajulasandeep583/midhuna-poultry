"""Data behind the Poultry desk dashboards.

Deliberately one round trip per page: these screens are opened on a laptop in a
farm office, and a dozen chained calls is what makes a dashboard feel slow.
"""

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, nowdate

from poultry.poultry_utils import active_withdrawals, standard_row

ACTIVE = ["Placed", "Growing", "Laying", "Depleting"]


@frappe.whitelist()
def control_tower():
	today = getdate(nowdate())
	flocks = frappe.get_all(
		"Flock",
		filters={"status": ["in", ACTIVE]},
		fields=["name", "flock_name", "farm", "shed", "flock_type", "strain", "status",
		        "placement_date", "opening_qty", "current_qty", "age_days", "mortality_pct",
		        "livability_pct", "fcr", "eef", "avg_body_weight_g", "hd_production_pct",
		        "cumulative_feed_kg", "cost_per_bird"],
		order_by="farm asc, shed asc",
	)

	cards = []
	for f in flocks:
		# v16's query builder rejects aggregate expressions as select fields
		# (§2.4.2), so take the latest row by order rather than max().
		last = frappe.db.get_value(
			"Daily Flock Entry", {"flock": f.name, "docstatus": 1}, "posting_date",
			order_by="posting_date desc")
		entered_today = bool(last and getdate(last) == today)
		days_missing = (today - getdate(last)).days if last else cint(f.age_days)

		alert = frappe.db.get_value(
			"Daily Flock Entry",
			{"flock": f.name, "docstatus": 1, "has_alert": 1},
			["alert_message", "posting_date"], order_by="posting_date desc", as_dict=True,
		)
		recent_alert = None
		if alert and (today - getdate(alert.posting_date)).days <= 3:
			recent_alert = alert.alert_message.split("\n")[0]

		wd = active_withdrawals(f.name, today)
		std = standard_row(f.name, cint(f.age_days))

		# green normal, amber needs attention, red acting now
		if recent_alert or wd:
			status = "red" if recent_alert else "amber"
		elif not entered_today:
			status = "amber"
		else:
			status = "green"

		weight_var = 0.0
		if std and flt(std.std_body_weight_g) and flt(f.avg_body_weight_g):
			weight_var = (flt(f.avg_body_weight_g) - flt(std.std_body_weight_g)) / flt(
				std.std_body_weight_g) * 100.0

		cards.append({
			"flock": f.name,
			"flock_name": f.flock_name,
			"farm": f.farm,
			"shed": f.shed,
			"flock_type": f.flock_type,
			"strain": f.strain,
			"age_days": f.age_days,
			"placed": f.opening_qty,
			"birds": f.current_qty,
			"livability_pct": flt(f.livability_pct, 2),
			"fcr": flt(f.fcr, 3),
			"eef": flt(f.eef, 1),
			"hdp": flt(f.hd_production_pct, 1),
			"body_weight_g": flt(f.avg_body_weight_g, 0),
			"std_body_weight_g": flt(std.std_body_weight_g, 0) if std else 0,
			"weight_variance_pct": flt(weight_var, 1),
			"cost_per_bird": flt(f.cost_per_bird, 2),
			"entered_today": entered_today,
			"days_missing": max(0, days_missing),
			"alert": recent_alert,
			"withdrawal": (
				_("{0} until {1}").format(wd[0].medication, wd[0].withdrawal_clear_date)
				if wd else None
			),
			"status": status,
		})

	overdue = frappe.db.sql(
		"""
		select p.flock, p.farm, d.vaccine, d.due_date, d.age_days
		from `tabFlock Vaccination Plan` p
		join `tabFlock Vaccination Plan Detail` d on d.parent = p.name
		join `tabFlock` f on f.name = p.flock
		where d.status != 'Done' and d.due_date < %(today)s and f.status in %(active)s
		order by d.due_date asc
		limit 12
		""", {"today": today, "active": tuple(ACTIVE)}, as_dict=True)
	for o in overdue:
		o["overdue_days"] = (today - getdate(o.due_date)).days

	# A standing condition (a withdrawal window, say) re-raises the same line
	# every day. Showing it eight times is noise, so keep the latest of each.
	raw = frappe.db.sql(
		"""
		select name, flock, posting_date, alert_message
		from `tabDaily Flock Entry`
		where docstatus = 1 and has_alert = 1 and posting_date >= %(since)s
		order by posting_date desc
		""", {"since": add_days(today, -7)}, as_dict=True)
	seen, alerts = set(), []
	for a in raw:
		first = (a.alert_message or "").split("\n")[0]
		key = (a.flock, first)
		if key in seen:
			continue
		seen.add(key)
		a["alert_message"] = first
		alerts.append(a)
		if len(alerts) >= 12:
			break

	totals = {
		"birds": sum(cint(c["birds"]) for c in cards),
		"flocks": len(cards),
		"sheds_occupied": frappe.db.count("Shed", {"status": "Occupied"}),
		"sheds_total": frappe.db.count("Shed"),
		"eggs_today": flt(frappe.db.sql(
			"""select coalesce(sum(total_eggs),0) from `tabDaily Flock Entry`
			   where docstatus=1 and posting_date=%s""", today)[0][0]),
		"feed_today_kg": flt(frappe.db.sql(
			"""select coalesce(sum(total_feed_kg),0) from `tabDaily Flock Entry`
			   where docstatus=1 and posting_date=%s""", today)[0][0]),
		"losses_today": cint(frappe.db.sql(
			"""select coalesce(sum(mortality_qty),0)+coalesce(sum(cull_qty),0)
			   from `tabDaily Flock Entry` where docstatus=1 and posting_date=%s""", today)[0][0]),
		"pending_entries": sum(1 for c in cards if not c["entered_today"]),
		"overdue_vaccinations": len(overdue),
		"under_withdrawal": sum(1 for c in cards if c["withdrawal"]),
	}

	return {"totals": totals, "cards": cards, "overdue": overdue, "alerts": alerts,
	        "today": str(today)}


@frappe.whitelist()
def flock_360(flock):
	doc = frappe.get_doc("Flock", flock)
	std = {
		cint(r.age_days): r
		for r in frappe.get_all(
			"Breed Standard Detail",
			filters={"parent": flock, "parenttype": "Flock"},
			fields=["age_days", "std_body_weight_g", "std_cumulative_mortality_pct",
			        "std_hd_production_pct", "std_daily_feed_g"],
		)
	}

	entries = frappe.get_all(
		"Daily Flock Entry",
		filters={"flock": flock, "docstatus": 1},
		fields=["name", "posting_date", "age_days", "opening_qty", "mortality_qty", "cull_qty",
		        "closing_qty", "cumulative_mortality_pct", "total_feed_kg", "cumulative_feed_kg",
		        "avg_body_weight_g", "total_eggs", "hd_production_pct", "water_feed_ratio",
		        "has_alert", "alert_message", "entry_source"],
		order_by="posting_date asc",
	)

	series = {"age": [], "weight": [], "std_weight": [], "mortality": [], "std_mortality": [],
	          "hdp": [], "std_hdp": [], "feed": []}
	for e in entries:
		s = _nearest(std, e.age_days)
		series["age"].append(cint(e.age_days))
		series["weight"].append(flt(e.avg_body_weight_g, 0))
		series["std_weight"].append(flt(s.std_body_weight_g, 0) if s else 0)
		series["mortality"].append(flt(e.cumulative_mortality_pct, 2))
		series["std_mortality"].append(flt(s.std_cumulative_mortality_pct, 2) if s else 0)
		series["hdp"].append(flt(e.hd_production_pct, 1))
		series["std_hdp"].append(flt(s.std_hd_production_pct, 1) if s else 0)
		series["feed"].append(flt(e.total_feed_kg, 1))

	plan = []
	plan_name = frappe.db.get_value("Flock Vaccination Plan", {"flock": flock}, "name")
	if plan_name:
		plan = frappe.get_all(
			"Flock Vaccination Plan Detail",
			filters={"parent": plan_name},
			fields=["age_days", "vaccine", "due_date", "status", "done_on"],
			order_by="age_days asc",
		)

	meds = frappe.get_all(
		"Medication Entry", filters={"flock": flock, "docstatus": 1},
		fields=["name", "medication", "start_date", "end_date", "withdrawal_clear_date", "reason"],
		order_by="start_date desc",
	)

	weighings = frappe.get_all(
		"Bird Weighing", filters={"flock": flock, "docstatus": 1},
		fields=["posting_date", "age_days", "avg_body_weight_g", "std_body_weight_g",
		        "variance_pct", "uniformity_pct"],
		order_by="posting_date desc", limit=8,
	)

	return {
		"flock": doc.as_dict(no_nulls=True),
		"series": series,
		"recent": list(reversed(entries[-14:])),
		"plan": plan,
		"medications": meds,
		"weighings": weighings,
		"withdrawals": active_withdrawals(flock),
		"entry_count": len(entries),
	}


@frappe.whitelist()
def flock_options():
	return frappe.get_all(
		"Flock",
		fields=["name", "flock_name", "farm", "shed", "flock_type", "status"],
		order_by="status asc, farm asc, shed asc",
	)


def _nearest(std, age):
	best = None
	for a in sorted(std):
		if a <= cint(age):
			best = std[a]
		else:
			break
	return best
