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
def entry_board(days=14):
	"""Days across, flocks down - the catch-up grid a supervisor fills in on a
	farm visit (§11.6). Shows at a glance which days are missing."""
	days = cint(days) or 14
	today = getdate(nowdate())
	dates = [add_days(today, -i) for i in range(days - 1, -1, -1)]

	flocks = frappe.get_all(
		"Flock",
		filters={"status": ["in", ACTIVE]},
		fields=["name", "flock_name", "farm", "shed", "flock_type", "placement_date",
		        "current_qty"],
		order_by="farm asc, shed asc",
	)

	rows = frappe.get_all(
		"Daily Flock Entry",
		filters={"docstatus": 1, "posting_date": [">=", dates[0]],
		         "flock": ["in", [f.name for f in flocks]] if flocks else [""]},
		fields=["name", "flock", "posting_date", "mortality_qty", "cull_qty", "total_feed_kg",
		        "total_eggs", "has_alert"],
	)
	by_key = {(r.flock, str(r.posting_date)): r for r in rows}

	board = []
	for f in flocks:
		cells = []
		missing = 0
		for d in dates:
			before_placement = getdate(d) < getdate(f.placement_date)
			entry = by_key.get((f.name, str(d)))
			if before_placement:
				state = "na"
			elif entry:
				state = "alert" if entry.has_alert else "done"
			else:
				state = "missing"
				missing += 1
			cells.append({
				"date": str(d),
				"state": state,
				"entry": entry.name if entry else None,
				"losses": (cint(entry.mortality_qty) + cint(entry.cull_qty)) if entry else None,
				"feed": flt(entry.total_feed_kg, 1) if entry else None,
				"eggs": cint(entry.total_eggs) if entry else None,
			})
		board.append({
			"flock": f.name, "flock_name": f.flock_name, "farm": f.farm, "shed": f.shed,
			"flock_type": f.flock_type, "birds": f.current_qty, "missing": missing,
			"cells": cells,
		})

	board.sort(key=lambda r: (-r["missing"], r["farm"], r["shed"]))
	return {
		"dates": [str(d) for d in dates],
		"board": board,
		"total_missing": sum(r["missing"] for r in board),
		"coverage_pct": round(
			100.0 * (1 - sum(r["missing"] for r in board) /
			         max(1, sum(len([c for c in r["cells"] if c["state"] != "na"]) for r in board))),
			1),
	}


@frappe.whitelist()
def health_hub():
	"""Everything a vet or farm manager needs to keep vaccination and
	withdrawal under control, in one call."""
	today = getdate(nowdate())
	week = add_days(today, 7)

	plan_rows = frappe.db.sql(
		"""
		select p.flock, p.farm, f.flock_name, f.flock_type, f.current_qty,
		       d.vaccine, d.route, d.due_date, d.status, d.age_days
		from `tabFlock Vaccination Plan` p
		join `tabFlock Vaccination Plan Detail` d on d.parent = p.name
		join `tabFlock` f on f.name = p.flock
		where f.status in %(active)s and d.status != 'Done'
		order by d.due_date asc
		""", {"active": tuple(ACTIVE)}, as_dict=True)

	overdue, due_today, due_soon = [], [], []
	for r in plan_rows:
		if not r.due_date:
			continue
		d = getdate(r.due_date)
		r["days"] = (d - today).days
		if d < today:
			overdue.append(r)
		elif d == today:
			due_today.append(r)
		elif d <= week:
			due_soon.append(r)

	done = frappe.db.sql(
		"""
		select count(*) from `tabFlock Vaccination Plan Detail` d
		join `tabFlock Vaccination Plan` p on p.name = d.parent
		join `tabFlock` f on f.name = p.flock
		where f.status in %(active)s and d.status = 'Done'
		""", {"active": tuple(ACTIVE)})[0][0]
	planned_to_date = done + len(overdue) + len(due_today)
	compliance = round(100.0 * done / planned_to_date, 1) if planned_to_date else 100.0

	withdrawals = []
	for f in frappe.get_all("Flock", filters={"status": ["in", ACTIVE]},
	                        fields=["name", "flock_name", "farm", "shed", "current_qty"]):
		for w in active_withdrawals(f.name, today):
			withdrawals.append({
				"flock": f.name, "flock_name": f.flock_name, "farm": f.farm, "shed": f.shed,
				"birds": f.current_qty, "medication": w.medication,
				"clears_on": str(w.withdrawal_clear_date),
				"days_left": (getdate(w.withdrawal_clear_date) - today).days,
			})

	meds = frappe.db.sql(
		"""
		select m.name, m.flock, f.flock_name, m.medication, m.start_date, m.end_date,
		       m.withdrawal_clear_date, m.reason, m.birds_treated
		from `tabMedication Entry` m join `tabFlock` f on f.name = m.flock
		where m.docstatus = 1 order by m.start_date desc limit 10
		""", as_dict=True)

	reasons = frappe.db.sql(
		"""
		select coalesce(md.reason, 'Not specified') as reason, sum(md.qty) as qty
		from `tabFlock Mortality Detail` md
		join `tabDaily Flock Entry` e on e.name = md.parent
		where e.docstatus = 1 and e.posting_date >= %(since)s
		group by md.reason order by qty desc limit 8
		""", {"since": add_days(today, -30)}, as_dict=True)

	return {
		"totals": {
			"overdue": len(overdue),
			"due_today": len(due_today),
			"due_soon": len(due_soon),
			"compliance_pct": compliance,
			"under_withdrawal": len(withdrawals),
			"birds_blocked": sum(cint(w["birds"]) for w in withdrawals),
		},
		"overdue": overdue[:15],
		"due_today": due_today[:15],
		"due_soon": due_soon[:15],
		"withdrawals": sorted(withdrawals, key=lambda w: w["days_left"]),
		"medications": meds,
		"mortality_reasons": reasons,
	}


@frappe.whitelist()
def cost_hub():
	"""Where the money went, per flock and per kilogram."""
	today = getdate(nowdate())

	flocks = frappe.get_all(
		"Flock",
		fields=["name", "flock_name", "farm", "shed", "flock_type", "status", "age_days",
		        "opening_qty", "current_qty", "cumulative_feed_kg", "avg_body_weight_g",
		        "total_cost", "cost_per_bird", "cost_per_kg_live", "fcr", "cumulative_eggs"],
		filters={"status": ["!=", "Draft"]},
		order_by="status asc, name asc",
	)

	feed_cost = {}
	for r in frappe.db.sql(
		"""
		select se.poultry_flock as flock, sum(se.total_outgoing_value) as val
		from `tabStock Entry` se
		where se.docstatus = 1 and se.purpose = 'Material Issue'
		  and se.poultry_flock is not null group by se.poultry_flock
		""", as_dict=True):
		feed_cost[r.flock] = flt(r.val)

	rows = []
	for f in flocks:
		live_kg = flt(f.current_qty) * flt(f.avg_body_weight_g) / 1000.0
		rows.append({
			"flock": f.name, "flock_name": f.flock_name, "farm": f.farm, "shed": f.shed,
			"flock_type": f.flock_type, "status": f.status, "age_days": f.age_days,
			"birds": f.current_qty, "total_cost": flt(f.total_cost, 2),
			"feed_cost": flt(feed_cost.get(f.name, 0), 2),
			"feed_share_pct": round(100.0 * flt(feed_cost.get(f.name, 0)) / flt(f.total_cost), 1)
			if flt(f.total_cost) else 0,
			"cost_per_bird": flt(f.cost_per_bird, 2),
			"cost_per_kg_live": flt(f.cost_per_kg_live, 2),
			"fcr": flt(f.fcr, 3), "live_kg": round(live_kg, 1),
			"eggs": f.cumulative_eggs,
		})

	weeks = frappe.db.sql(
		"""
		select yearweek(e.posting_date, 3) as wk, min(e.posting_date) as start,
		       sum(fd.qty_kg) as kg
		from `tabDaily Flock Entry` e
		join `tabFlock Feed Detail` fd on fd.parent = e.name
		where e.docstatus = 1 and e.posting_date >= %(since)s
		group by yearweek(e.posting_date, 3) order by wk
		""", {"since": add_days(today, -70)}, as_dict=True)
	rates = {i.name: flt(i.valuation_rate) for i in frappe.get_all(
		"Item", filters={"item_group": "Poultry"}, fields=["name", "valuation_rate"])}
	avg_rate = (sum(rates.values()) / len(rates)) if rates else 0
	feed_trend = [{"label": str(w.start), "kg": flt(w.kg, 0),
	               "cost": round(flt(w.kg) * avg_rate, 0)} for w in weeks]

	closed = frappe.get_all(
		"Flock Closure", filters={"docstatus": 1},
		fields=["flock", "closure_date", "total_cost", "total_revenue", "margin",
		        "cost_per_kg_live", "fcr", "eef", "total_live_weight_kg"],
		order_by="closure_date desc", limit=10)

	revenue_30 = flt(frappe.db.sql(
		"""select coalesce(sum(base_grand_total),0) from `tabSales Invoice`
		   where docstatus=1 and posting_date >= %s""", add_days(today, -30))[0][0])
	feed_spend_30 = flt(frappe.db.sql(
		"""select coalesce(sum(total_outgoing_value),0) from `tabStock Entry`
		   where docstatus=1 and purpose='Material Issue' and posting_date >= %s
		     and poultry_flock is not null""", add_days(today, -30))[0][0])

	return {
		"totals": {
			"birds_value": round(sum(r["total_cost"] for r in rows
			                         if r["status"] not in ("Closed",)), 0),
			"feed_spend_30": round(feed_spend_30, 0),
			"revenue_30": round(revenue_30, 0),
			# Weighted across broilers only: a layer's cost per kg of liveweight
			# is not a number anyone manages on, and a plain mean lets a
			# 12-day-old flock (still carrying its chick cost over almost no
			# weight) drag the figure somewhere meaningless.
			"avg_cost_per_kg": _weighted_cost_per_kg(rows),
		},
		"rows": rows,
		"feed_trend": feed_trend,
		"closed": closed,
	}


@frappe.whitelist()
def trade_board():
	"""What went out and what came in - today, this week, this month."""
	today = getdate(nowdate())
	spans = {"today": today, "week": add_days(today, -6), "month": add_days(today, -29)}

	def sales_since(since):
		return frappe.db.sql(
			"""
			select coalesce(sum(si.base_grand_total), 0) as amount, count(*) as docs
			from `tabSales Invoice` si
			where si.docstatus = 1 and si.posting_date >= %(since)s
			""", {"since": since}, as_dict=True)[0]

	def purchases_since(since):
		pr = frappe.db.sql(
			"""
			select coalesce(sum(base_grand_total), 0) as amount, count(*) as docs
			from `tabPurchase Receipt` where docstatus = 1 and posting_date >= %(since)s
			""", {"since": since}, as_dict=True)[0]
		pi = frappe.db.sql(
			"""
			select coalesce(sum(base_grand_total), 0) as amount, count(*) as docs
			from `tabPurchase Invoice` where docstatus = 1 and posting_date >= %(since)s
			""", {"since": since}, as_dict=True)[0]
		return {"amount": flt(pr.amount) + flt(pi.amount), "docs": cint(pr.docs) + cint(pi.docs)}

	sold_items = frappe.db.sql(
		"""
		select sii.item_code, i.item_name, i.stock_uom,
		       sum(sii.stock_qty) as qty, sum(sii.base_net_amount) as amount
		from `tabSales Invoice Item` sii
		join `tabSales Invoice` si on si.name = sii.parent
		join `tabItem` i on i.name = sii.item_code
		where si.docstatus = 1 and si.posting_date >= %(since)s
		group by sii.item_code, i.item_name, i.stock_uom
		order by amount desc
		""", {"since": spans["month"]}, as_dict=True)

	bought_items = frappe.db.sql(
		"""
		select pri.item_code, i.item_name, i.stock_uom,
		       sum(pri.stock_qty) as qty, sum(pri.base_net_amount) as amount
		from `tabPurchase Receipt Item` pri
		join `tabPurchase Receipt` pr on pr.name = pri.parent
		join `tabItem` i on i.name = pri.item_code
		where pr.docstatus = 1 and pr.posting_date >= %(since)s
		group by pri.item_code, i.item_name, i.stock_uom
		order by amount desc
		""", {"since": spans["month"]}, as_dict=True)

	customers = frappe.db.sql(
		"""
		select customer, sum(base_grand_total) as amount, count(*) as invoices
		from `tabSales Invoice` where docstatus = 1 and posting_date >= %(since)s
		group by customer order by amount desc limit 6
		""", {"since": spans["month"]}, as_dict=True)

	suppliers = frappe.db.sql(
		"""
		select supplier, sum(base_grand_total) as amount, count(*) as receipts
		from `tabPurchase Receipt` where docstatus = 1 and posting_date >= %(since)s
		group by supplier order by amount desc limit 6
		""", {"since": spans["month"]}, as_dict=True)

	recent_sales = frappe.get_all(
		"Sales Invoice", filters={"docstatus": 1},
		fields=["name", "customer", "posting_date", "base_grand_total", "status"],
		order_by="posting_date desc, creation desc", limit=8)
	recent_purchases = frappe.get_all(
		"Purchase Receipt", filters={"docstatus": 1},
		fields=["name", "supplier", "posting_date", "base_grand_total", "status"],
		order_by="posting_date desc, creation desc", limit=8)

	trend = frappe.db.sql(
		"""
		select posting_date as d, sum(base_grand_total) as amount
		from `tabSales Invoice` where docstatus = 1 and posting_date >= %(since)s
		group by posting_date order by posting_date
		""", {"since": spans["month"]}, as_dict=True)

	return {
		"sales": {k: sales_since(v) for k, v in spans.items()},
		"purchases": {k: purchases_since(v) for k, v in spans.items()},
		"sold_items": sold_items,
		"bought_items": bought_items,
		"customers": customers,
		"suppliers": suppliers,
		"recent_sales": recent_sales,
		"recent_purchases": recent_purchases,
		"sales_trend": [{"d": str(r.d), "amount": flt(r.amount, 0)} for r in trend],
		"receivable": flt(frappe.db.sql(
			"""select coalesce(sum(outstanding_amount),0) from `tabSales Invoice`
			   where docstatus=1 and outstanding_amount > 0""")[0][0]),
	}


@frappe.whitelist()
def stock_board():
	"""Everything on hand, grouped the way a poultry manager thinks: birds,
	eggs, feed - not by item group."""
	rows = frappe.db.sql(
		"""
		select b.item_code, i.item_name, i.stock_uom, b.warehouse,
		       b.actual_qty, b.stock_value, b.valuation_rate
		from `tabBin` b join `tabItem` i on i.name = b.item_code
		where b.actual_qty != 0
		order by i.item_name, b.warehouse
		""", as_dict=True)

	def bucket(code):
		if code.startswith("BIRD"):
			return "Live Birds"
		if code.startswith("EGG"):
			return "Eggs"
		if code.startswith("FEED"):
			return "Feed"
		return "Other"

	groups, items = {}, {}
	for r in rows:
		g = bucket(r.item_code)
		groups.setdefault(g, {"group": g, "qty": 0.0, "value": 0.0, "lines": 0})
		groups[g]["qty"] += flt(r.actual_qty)
		groups[g]["value"] += flt(r.stock_value)
		groups[g]["lines"] += 1

		key = r.item_code
		items.setdefault(key, {
			"item_code": r.item_code, "item_name": r.item_name, "uom": r.stock_uom,
			"group": g, "qty": 0.0, "value": 0.0, "rate": flt(r.valuation_rate),
			"warehouses": [],
		})
		items[key]["qty"] += flt(r.actual_qty)
		items[key]["value"] += flt(r.stock_value)
		items[key]["warehouses"].append({
			"warehouse": r.warehouse, "qty": flt(r.actual_qty, 1),
			"value": flt(r.stock_value, 0),
		})

	order = {"Live Birds": 0, "Eggs": 1, "Feed": 2, "Other": 3}
	item_rows = sorted(items.values(), key=lambda x: (order.get(x["group"], 9), -x["value"]))
	for it in item_rows:
		it["qty"] = flt(it["qty"], 1)
		it["value"] = flt(it["value"], 0)
		it["warehouses"].sort(key=lambda w: -w["qty"])

	return {
		"groups": sorted(groups.values(), key=lambda g: order.get(g["group"], 9)),
		"items": item_rows,
		"total_value": round(sum(g["value"] for g in groups.values()), 0),
	}


@frappe.whitelist()
def management():
	"""Top line for the management landing page - one call, small payload."""
	today = getdate(nowdate())
	sales_today = flt(frappe.db.sql(
		"""select coalesce(sum(base_grand_total),0) from `tabSales Invoice`
		   where docstatus=1 and posting_date=%s""", today)[0][0])
	purch_today = flt(frappe.db.sql(
		"""select coalesce(sum(base_grand_total),0) from `tabPurchase Receipt`
		   where docstatus=1 and posting_date=%s""", today)[0][0])
	stock_value = flt(frappe.db.sql(
		"""select coalesce(sum(stock_value),0) from `tabBin`""")[0][0])
	eggs_stock = flt(frappe.db.sql(
		"""select coalesce(sum(b.actual_qty),0) from `tabBin` b
		   where b.item_code like 'EGG%%'""")[0][0])
	birds_stock = flt(frappe.db.sql(
		"""select coalesce(sum(b.actual_qty),0) from `tabBin` b
		   where b.item_code like 'BIRD%%'""")[0][0])
	feed_stock = flt(frappe.db.sql(
		"""select coalesce(sum(b.actual_qty),0) from `tabBin` b
		   where b.item_code like 'FEED%%'""")[0][0])
	eggs_today = flt(frappe.db.sql(
		"""select coalesce(sum(total_eggs),0) from `tabDaily Flock Entry`
		   where docstatus=1 and posting_date=%s""", today)[0][0])

	return {
		"sales_today": round(sales_today, 0),
		"purchases_today": round(purch_today, 0),
		"stock_value": round(stock_value, 0),
		"eggs_stock": int(eggs_stock),
		"birds_stock": int(birds_stock),
		"feed_stock_kg": round(feed_stock, 0),
		"eggs_today": int(eggs_today),
		"flocks": frappe.db.count("Flock", {"status": ["in", ACTIVE]}),
		"sheds_occupied": frappe.db.count("Shed", {"status": "Occupied"}),
		"overdue_vaccinations": cint(frappe.db.sql(
			"""select coalesce(sum(overdue_count),0) from `tabFlock Vaccination Plan`""")[0][0]),
	}


def _weighted_cost_per_kg(rows):
	broilers = [r for r in rows if r["flock_type"] == "Broiler" and r["live_kg"]]
	kg = sum(r["live_kg"] for r in broilers)
	cost = sum(r["total_cost"] for r in broilers)
	return round(cost / kg, 2) if kg else 0.0


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
