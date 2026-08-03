"""Correct the broiler feed standard and regenerate broiler daily entries.

The first curve under-fed the birds: it produced FCR 1.03-1.27 and EEF above
500, which is not achievable and would discredit the whole dataset. Real Cobb
500 at day 42 eats about 4.3 kg to reach 2.76 kg live, i.e. FCR ~1.57 and EEF
around 400.
"""

import frappe
from frappe.utils import flt

BROILER_DAILY_FEED = [(1, 16), (7, 32), (14, 64), (21, 100), (28, 140), (35, 175), (42, 200)]
BROILER_STANDARDS = ["Cobb 500 Broiler Standard", "Ross 308 Broiler Standard",
                     "Vencobb 430 Broiler Standard"]


def interpolate(anchors, upto):
	out = {}
	pts = sorted(anchors)
	for i in range(len(pts) - 1):
		a_age, a_val = pts[i]
		b_age, b_val = pts[i + 1]
		for age in range(a_age, b_age):
			frac = (age - a_age) / float(b_age - a_age)
			out[age] = a_val + (b_val - a_val) * frac
	out[pts[-1][0]] = pts[-1][1]
	# extend past the last anchor at the same rate
	last = pts[-1]
	for age in range(last[0] + 1, upto + 1):
		out[age] = last[1]
	return out


def fix_rows(rows):
	feed = interpolate(BROILER_DAILY_FEED, 60)
	cum = 0.0
	for r in sorted(rows, key=lambda x: x.age_days):
		daily = feed.get(r.age_days, r.std_daily_feed_g)
		cum += daily
		r.std_daily_feed_g = round(daily, 1)
		r.std_cumulative_feed_g = round(cum, 1)
		body_kg = flt(r.std_body_weight_g) / 1000.0
		r.std_fcr = round((cum / 1000.0) / body_kg, 3) if body_kg else 0


def update_standards():
	for name in BROILER_STANDARDS:
		if not frappe.db.exists("Breed Standard", name):
			continue
		doc = frappe.get_doc("Breed Standard", name)
		fix_rows(doc.details)
		doc.flags.ignore_permissions = True
		doc.save()
		print(f"  + standard corrected: {name} (day 42 FCR "
		      f"{[d.std_fcr for d in doc.details if d.age_days == 42]})")


def update_snapshots():
	for flock in frappe.get_all("Flock", filters={"flock_type": "Broiler"}, pluck="name"):
		doc = frappe.get_doc("Flock", flock)
		if not doc.standard_snapshot:
			continue
		fix_rows(doc.standard_snapshot)
		doc.flags.ignore_permissions = True
		doc.save()
		print("  + snapshot corrected:", flock)


def wipe_broiler_entries():
	for flock in frappe.get_all("Flock", filters={"flock_type": "Broiler"}, pluck="name"):
		for closure in frappe.get_all("Flock Closure",
		                              filters={"flock": flock, "docstatus": 1}, pluck="name"):
			doc = frappe.get_doc("Flock Closure", closure)
			doc.flags.ignore_permissions = True
			doc.cancel()
			frappe.delete_doc("Flock Closure", closure, force=1, ignore_permissions=True)
			print("  - closure removed:", closure)

		names = frappe.get_all("Daily Flock Entry",
		                       filters={"flock": flock, "docstatus": ["<", 2]},
		                       pluck="name", order_by="posting_date desc")
		for n in names:
			doc = frappe.get_doc("Daily Flock Entry", n)
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()
			frappe.delete_doc("Daily Flock Entry", n, force=1, ignore_permissions=True)
		frappe.db.commit()
		print(f"  - {len(names)} entries removed from {flock}")

		# weighings reference the standard too; regenerate them as well
		for n in frappe.get_all("Bird Weighing", filters={"flock": flock, "docstatus": 1},
		                        pluck="name"):
			doc = frappe.get_doc("Bird Weighing", n)
			doc.flags.ignore_permissions = True
			doc.cancel()
			frappe.delete_doc("Bird Weighing", n, force=1, ignore_permissions=True)
		frappe.db.commit()


def run():
	print("--- standards ---");  update_standards()
	print("--- snapshots ---");  update_snapshots()
	print("--- wipe ---");       wipe_broiler_entries()
	frappe.db.commit()
	print("FIX PREPARED - now re-run demo_ops entries/health/finish")
