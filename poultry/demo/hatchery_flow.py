"""Make the egg store behave like a real one.

Eggs do not sit in a cold store for a month - a commercial hatchery sets them
within about a week, because hatchability falls roughly a point a day after
that. Every receipt older than the storage window is therefore actually set,
and if its 21 days are up it is candled, hatched, dispatched and broken out.
"""

import random

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

COMPANY = "Midhuna Poultry"
ABBR = "MP"
TODAY = getdate(nowdate())
STORAGE_WINDOW = 7

random.seed(20260806)


def wh(n):
	return f"{n} - {ABBR}"


def setters():
	return frappe.get_all("Hatchery Machine", filters={"machine_type": "Setter"}, pluck="name")


def hatchers():
	return frappe.get_all("Hatchery Machine", filters={"machine_type": "Hatcher"}, pluck="name")


def std_for(chick_type):
	row = frappe.db.get_value(
		"Chick Type", chick_type,
		["std_fertility_pct", "std_hatchability_pct", "std_chick_weight_g", "chick_item"],
		as_dict=True) or frappe._dict()
	return row


def run():
	st, ht = setters(), hatchers()
	if not st:
		print("  ! no setters")
		return

	receipts = frappe.get_all(
		"Hatching Egg Receipt", filters={"docstatus": 1, "eggs_in_store": [">", 0]},
		fields=["name", "posting_date", "chick_type", "eggs_in_store", "avg_egg_weight_g",
		        "breeder_age_weeks", "source_flock"],
		order_by="posting_date asc")

	made = {"set": 0, "candled": 0, "hatched": 0, "dispatched": 0, "breakout": 0}

	for i, r in enumerate(receipts):
		age = (TODAY - getdate(r.posting_date)).days
		if age <= STORAGE_WINDOW:
			continue  # genuinely still in store, leave it

		set_date = add_days(getdate(r.posting_date), random.randint(2, 5))
		if getdate(set_date) > TODAY:
			continue
		# set nearly all of it; a hatchery keeps only a small carry-over
		eggs = int(cint(r.eggs_in_store) * random.uniform(0.90, 0.97) / 100) * 100
		if eggs < 5000:
			continue

		s = frappe.get_doc({
			"doctype": "Egg Setting",
			"set_date": set_date,
			"source_flock": r.source_flock,
			"setter": st[i % len(st)],
			"company": COMPANY,
			"egg_item": "EGG-HAT-BRL",
			"egg_receipt": r.name,
			"chick_type": r.chick_type,
			"eggs_set": eggs,
			"egg_age_days": (getdate(set_date) - getdate(r.posting_date)).days,
			"breeder_age_weeks": r.breeder_age_weeks,
			"storage_temp_c": round(random.uniform(16.8, 18.4), 1),
			"prewarm_hours": round(random.uniform(6, 12), 1),
			"setter_temp_c": round(random.uniform(37.4, 37.8), 2),
			"setter_humidity_pct": round(random.uniform(53, 58), 1),
			"turning_per_day": 24,
		})
		s.flags.ignore_permissions = True
		s.insert()
		s.submit()
		made["set"] += 1

		std = std_for(r.chick_type)
		days_in = (TODAY - getdate(set_date)).days

		# candling on day 18
		if days_in >= 18:
			target_fert = flt(std.std_fertility_pct) or 92.0
			fert = target_fert / 100.0 * random.uniform(0.97, 1.02)
			infert = eggs - int(eggs * fert)
			clear = int(infert * 0.70)
			dead = int(infert * 0.20)
			cont = max(0, infert - clear - dead)
			c = frappe.get_doc({
				"doctype": "Candling Entry", "egg_setting": s.name,
				"posting_date": add_days(set_date, 18),
				"clear_eggs": clear, "dead_germ": dead, "contaminated": cont,
				"remarks": "Candled at day 18, clears removed",
			})
			c.flags.ignore_permissions = True
			c.insert()
			c.submit()
			made["candled"] += 1

		# hatch on day 21
		if days_in >= 21:
			s.reload()
			fertile = cint(s.fertile_eggs)
			target_hos = flt(std.std_hatchability_pct) or 83.0
			hatched = int(eggs * target_hos / 100.0 * random.uniform(0.97, 1.03))
			hatched = min(hatched, fertile)
			cripples = int(hatched * random.uniform(0.015, 0.03))
			h = frappe.get_doc({
				"doctype": "Hatch Entry", "egg_setting": s.name,
				"posting_date": add_days(set_date, 21),
				"hatcher": ht[i % len(ht)] if ht else None,
				"chicks_hatched": hatched, "cripples": cripples,
				"avg_chick_weight_g": round(
					flt(std.std_chick_weight_g or 40) * random.uniform(0.96, 1.05), 1),
				"hatcher_temp_c": round(random.uniform(36.8, 37.2), 2),
				"hatcher_humidity_pct": round(random.uniform(64, 72), 1),
				"chick_item": std.chick_item or "CHICK-DOC",
				"warehouse": wh("Hatchery Chick Hold"),
			})
			h.flags.ignore_permissions = True
			h.insert()
			h.submit()
			made["hatched"] += 1

			h.reload()
			saleable = cint(h.saleable_chicks)
			boxes = int(saleable / 100)
			if boxes:
				d = frappe.get_doc({
					"doctype": "Chick Dispatch", "hatch_entry": h.name,
					"posting_date": add_days(set_date, 21),
					"destination_type": "Own Farm" if i % 3 == 0 else "Customer",
					"to_farm": "Ramgundam Broiler Farm" if i % 3 == 0 else None,
					"customer": None if i % 3 == 0 else random.choice(
						["Balaji Chicken Centre", "Sri Lakshmi Poultry Traders"]),
					"boxes": boxes, "chicks_per_box": 100,
					"extras": saleable - boxes * 100,
					"transit_temp_c": round(random.uniform(24, 28), 1),
					"transit_hours": round(random.uniform(2, 8), 1),
					"doa_chicks": int(saleable * random.uniform(0.0005, 0.003)),
					"in_ovo_vaccinated": 1,
					"driver_name": random.choice(["S. Naresh", "K. Ramulu", "M. Yadagiri"]),
					"vehicle_no": f"TS{random.randint(10, 39)}AB{random.randint(1000, 9999)}",
				})
				d.flags.ignore_permissions = True
				d.insert()
				d.submit()
				made["dispatched"] += 1

			# break out the residue
			residue = eggs - hatched
			if residue > 0:
				w = {"infertile": random.uniform(42, 52), "early": random.uniform(16, 23),
				     "mid": random.uniform(6, 10), "late": random.uniform(12, 18),
				     "pipped": random.uniform(4, 8), "contam": random.uniform(0.8, 2.0),
				     "malpos": random.uniform(2, 6)}
				tot = sum(w.values())
				sh = {k: v / tot for k, v in w.items()}
				vals = {k: int(residue * v) for k, v in sh.items()}
				vals["malpos"] = max(0, residue - sum(v for k, v in vals.items() if k != "malpos"))
				b = frappe.get_doc({
					"doctype": "Breakout Analysis", "egg_setting": s.name,
					"posting_date": add_days(set_date, 21), "eggs_broken": residue,
					"infertile": vals["infertile"], "early_dead": vals["early"],
					"mid_dead": vals["mid"], "late_dead": vals["late"],
					"pipped_not_hatched": vals["pipped"], "contaminated": vals["contam"],
					"malpositioned": vals["malpos"],
					"remarks": "Residue broken out and classified after take-off",
				})
				b.flags.ignore_permissions = True
				b.insert()
				b.submit()
				made["breakout"] += 1

		frappe.db.commit()

	print(f"  + settings {made['set']}, candled {made['candled']}, hatched {made['hatched']}, "
	      f"dispatched {made['dispatched']}, breakouts {made['breakout']}")

	print("--- egg store now ---")
	for r in frappe.get_all("Hatching Egg Receipt", filters={"docstatus": 1},
	                        fields=["name", "chick_type", "eggs_in_store", "storage_days"],
	                        order_by="posting_date desc"):
		if cint(r.eggs_in_store) > 0:
			print(f"    {r.name} {r.chick_type}: {r.eggs_in_store} eggs, {r.storage_days} days old")
	print("HATCHERY FLOW DONE")
