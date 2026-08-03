"""Every setting with the three numbers a hatchery is judged on.

Breeder age at set is carried on each row because it is the standard
explanation for hatchability variation (§5.8) - a flock at 28 weeks and the
same flock at 62 weeks are not comparable.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conds = ["s.docstatus = 1"]
	params = {}
	for key, clause in (("from_date", "s.set_date >= %(from_date)s"),
	                    ("to_date", "s.set_date <= %(to_date)s"),
	                    ("source_flock", "s.source_flock = %(source_flock)s"),
	                    ("setter", "s.setter = %(setter)s")):
		if filters.get(key):
			conds.append(clause)
			params[key] = filters.get(key)

	rows = frappe.db.sql(
		"""
		select s.name, s.set_date, s.source_flock, s.breeder_age_weeks, s.setter,
		       s.eggs_set, s.egg_age_days, s.fertile_eggs, s.fertility_pct,
		       s.chicks_hatched, s.hatchability_set_pct, s.hatchability_fertile_pct,
		       s.status, s.hatch_date,
		       (select coalesce(sum(h.saleable_chicks), 0) from `tabHatch Entry` h
		         where h.egg_setting = s.name and h.docstatus = 1) as saleable,
		       (select coalesce(sum(h.cripples), 0) from `tabHatch Entry` h
		         where h.egg_setting = s.name and h.docstatus = 1) as cripples
		from `tabEgg Setting` s
		where {conds}
		order by s.set_date desc
		""".format(conds=" and ".join(conds)), params, as_dict=True)

	data = []
	for r in rows:
		hatched = cint(r.chicks_hatched)
		data.append({
			"setting": r.name,
			"set_date": r.set_date,
			"source_flock": r.source_flock,
			"breeder_age_weeks": flt(r.breeder_age_weeks, 1),
			"setter": r.setter,
			"eggs_set": cint(r.eggs_set),
			"egg_age_days": cint(r.egg_age_days),
			"fertile_eggs": cint(r.fertile_eggs),
			"fertility_pct": flt(r.fertility_pct, 2),
			"chicks_hatched": hatched,
			"hatchability_set_pct": flt(r.hatchability_set_pct, 2),
			"hatchability_fertile_pct": flt(r.hatchability_fertile_pct, 2),
			"saleable": cint(r.saleable),
			"saleable_pct": (cint(r.saleable) / hatched * 100.0) if hatched else 0,
			"cripples": cint(r.cripples),
			"dead_in_shell": max(0, cint(r.fertile_eggs) - hatched),
			"status": r.status,
		})

	columns = [
		{"label": _("Setting"), "fieldname": "setting", "fieldtype": "Link",
		 "options": "Egg Setting", "width": 130},
		{"label": _("Set Date"), "fieldname": "set_date", "fieldtype": "Date", "width": 95},
		{"label": _("Source Flock"), "fieldname": "source_flock", "fieldtype": "Link",
		 "options": "Flock", "width": 130},
		{"label": _("Breeder Age (wk)"), "fieldname": "breeder_age_weeks", "fieldtype": "Float",
		 "precision": 1, "width": 130},
		{"label": _("Setter"), "fieldname": "setter", "fieldtype": "Link",
		 "options": "Hatchery Machine", "width": 110},
		{"label": _("Eggs Set"), "fieldname": "eggs_set", "fieldtype": "Int", "width": 95},
		{"label": _("Egg Age"), "fieldname": "egg_age_days", "fieldtype": "Int", "width": 80},
		{"label": _("Fertile"), "fieldname": "fertile_eggs", "fieldtype": "Int", "width": 90},
		{"label": _("Fertility %"), "fieldname": "fertility_pct", "fieldtype": "Percent",
		 "width": 100},
		{"label": _("Hatched"), "fieldname": "chicks_hatched", "fieldtype": "Int", "width": 90},
		{"label": _("Hatch of Set %"), "fieldname": "hatchability_set_pct",
		 "fieldtype": "Percent", "width": 125},
		{"label": _("Hatch of Fertile %"), "fieldname": "hatchability_fertile_pct",
		 "fieldtype": "Percent", "width": 140},
		{"label": _("Saleable"), "fieldname": "saleable", "fieldtype": "Int", "width": 90},
		{"label": _("Saleable %"), "fieldname": "saleable_pct", "fieldtype": "Percent",
		 "width": 100},
		{"label": _("Cripples"), "fieldname": "cripples", "fieldtype": "Int", "width": 85},
		{"label": _("Dead in Shell"), "fieldname": "dead_in_shell", "fieldtype": "Int",
		 "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 95},
	]

	done = [d for d in data if d["hatchability_set_pct"]]
	chart = {
		"data": {
			"labels": [str(d["breeder_age_weeks"]) for d in reversed(done)],
			"datasets": [
				{"name": _("Hatch of Set %"),
				 "values": [d["hatchability_set_pct"] for d in reversed(done)]},
				{"name": _("Fertility %"),
				 "values": [d["fertility_pct"] for d in reversed(done)]},
			],
		},
		"type": "line",
		"lineOptions": {"hideDots": 0, "regionFill": 0},
	}
	return columns, data, None, chart
