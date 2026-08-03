"""Reference masters that ship with the product.

Breed standards for common strains are what make the app usable on day one
rather than a blank framework (§5.3.5). None of this is site-specific: no
company, no items, no farms. Feed Type and Egg Grade are created without an
Item link — each installation points them at its own items.
"""

import frappe


def _insert(doc):
	d = frappe.get_doc(doc)
	d.flags.ignore_permissions = True
	d.flags.ignore_mandatory = True
	d.insert()
	return d


BREEDS = [
	("Cobb", "Broiler"), ("Ross", "Broiler"), ("Vencobb", "Broiler"),
	("Hy-Line", "Layer"), ("Lohmann", "Layer"), ("BV", "Layer"),
]

STRAINS = [
	("Cobb 500", "Cobb", 42), ("Ross 308", "Ross", 42), ("Vencobb 430", "Vencobb", 40),
	("Hy-Line W-36", "Hy-Line", 518), ("Lohmann Brown", "Lohmann", 518), ("BV-300", "BV", 504),
]

# anchors: (age_days, value) - everything between is interpolated
BROILER_WEIGHT = [(1, 42), (7, 185), (14, 465), (21, 940), (28, 1500), (35, 2130), (42, 2760)]
BROILER_DAILY_FEED = [(1, 16), (7, 32), (14, 64), (21, 100), (28, 140), (35, 175), (42, 200)]
BROILER_MORT = [(1, 0.05), (7, 0.55), (14, 0.95), (21, 1.40), (28, 1.90), (35, 2.45), (42, 3.05)]

LAYER_WEIGHT = [(1, 38), (42, 400), (84, 780), (126, 1180), (154, 1420), (210, 1560),
                (350, 1690), (518, 1740)]
LAYER_DAILY_FEED = [(1, 11), (42, 42), (84, 62), (126, 88), (154, 105), (210, 112),
                    (350, 110), (518, 106)]
LAYER_MORT = [(1, 0.05), (42, 1.2), (84, 2.0), (126, 2.7), (154, 3.1), (210, 4.0),
              (350, 6.5), (518, 9.5)]
LAYER_HDP = [(1, 0), (140, 5), (147, 30), (154, 62), (161, 82), (175, 92), (196, 94.5),
             (280, 91), (350, 86), (420, 79), (518, 68)]

MORTALITY_REASONS = [
	("Chick Mortality (First Week)", "Environmental", 0, 0),
	("Ascites", "Disease", 0, 1),
	("Colibacillosis", "Disease", 0, 1),
	("Coccidiosis", "Disease", 0, 1),
	("Newcastle Suspected", "Disease", 0, 1),
	("Runt / Weak Bird Culled", "Culling", 1, 0),
	("Leg Weakness Culled", "Culling", 1, 0),
	("Heat Stress", "Environmental", 0, 0),
	("Smothering", "Handling", 0, 0),
	("Predation", "Predation", 0, 0),
	("Cannibalism", "Cannibalism", 0, 0),
	("Unknown", "Unknown", 0, 0),
]

FEED_TYPES = [
	("Broiler Pre-Starter", "Broiler", 1, 10),
	("Broiler Starter", "Broiler", 11, 24),
	("Broiler Finisher", "Broiler", 25, 60),
	("Chick Mash", "Layer", 1, 56),
	("Grower Mash", "Layer", 57, 126),
	("Layer Phase-1", "Layer", 127, 350),
	("Layer Phase-2", "Layer", 351, 600),
	("Pullet Chick Mash", "Rearing", 1, 56),
	("Pullet Grower Mash", "Rearing", 57, 126),
]

EGG_GRADES = [
	("S", "Small", 0, 52, 1, 0),
	("M", "Medium", 52, 58, 1, 0),
	("L", "Large", 58, 64, 1, 0),
	("XL", "Jumbo", 64, 90, 1, 0),
	("CR", "Crack", 0, 0, 0, 1),
]

DISEASES = [
	("Newcastle Disease", 1), ("Infectious Bursal Disease", 0), ("Infectious Bronchitis", 0),
	("Avian Influenza", 1), ("Coccidiosis", 0), ("Colibacillosis", 0), ("Marek's Disease", 0),
	("Fowl Pox", 0),
]

VACCINES = [
	("Marek's HVT", "Marek's Disease", "Subcutaneous", "Live", 0),
	("ND B1 / Lasota", "Newcastle Disease", "Eye Drop", "Live", 0),
	("IBD Intermediate", "Infectious Bursal Disease", "Drinking Water", "Live", 0),
	("IBD Intermediate Plus", "Infectious Bursal Disease", "Drinking Water", "Live", 0),
	("ND Lasota Booster", "Newcastle Disease", "Drinking Water", "Live", 0),
	("IB H120", "Infectious Bronchitis", "Spray", "Live", 0),
	("ND Killed (R2B)", "Newcastle Disease", "Intramuscular", "Killed", 21),
	("Fowl Pox", "Fowl Pox", "Wing Web", "Live", 0),
]

MEDICATIONS = [
	("Enrofloxacin 10%", "Enrofloxacin", "1 ml / 2 litre water", 8),
	("Amoxicillin Soluble", "Amoxicillin trihydrate", "1 g / 2 litre water", 7),
	("Tylosin Tartrate", "Tylosin", "0.5 g / litre water", 5),
	("Toltrazuril 2.5%", "Toltrazuril", "1 ml / litre water", 14),
	("Vitamin AD3E + C", "Multivitamin", "1 ml / 4 litre water", 0),
	("Liver Tonic", "Herbal", "1 ml / litre water", 0),
]

BROILER_SCHEDULE = [
	(1, "Marek's HVT", "Subcutaneous"), (5, "ND B1 / Lasota", "Eye Drop"),
	(12, "IBD Intermediate", "Drinking Water"), (19, "IBD Intermediate Plus", "Drinking Water"),
	(24, "ND Lasota Booster", "Drinking Water"),
]

LAYER_SCHEDULE = BROILER_SCHEDULE[:4] + [
	(28, "ND Lasota Booster", "Drinking Water"), (42, "IB H120", "Spray"),
	(56, "Fowl Pox", "Wing Web"), (84, "ND Killed (R2B)", "Intramuscular"),
	(112, "ND Lasota Booster", "Drinking Water"),
]


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
	return {a: v for a, v in out.items() if a <= upto}


def make_standard(name, strain, flock_type, upto, weight, feed, mort, hdp=None, step=1):
	if frappe.db.exists("Breed Standard", name):
		return
	w, f, m = interpolate(weight, upto), interpolate(feed, upto), interpolate(mort, upto)
	h = interpolate(hdp, upto) if hdp else {}

	doc = frappe.get_doc({
		"doctype": "Breed Standard", "standard_name": name, "strain": strain,
		"flock_type": flock_type, "is_default": 1,
		"source": "Breeder management guide",
	})
	cum = 0.0
	for age in range(1, upto + 1):
		if age not in w:
			continue
		cum += f.get(age, 0)
		body_kg = w[age] / 1000.0
		doc.append("details", {
			"age_days": age, "age_weeks": round(age / 7.0, 1),
			"std_body_weight_g": round(w[age], 1),
			"std_daily_feed_g": round(f.get(age, 0), 1),
			"std_cumulative_feed_g": round(cum, 1),
			"std_fcr": round((cum / 1000.0) / body_kg, 3) if body_kg else 0,
			"std_cumulative_mortality_pct": round(m.get(age, 0), 2),
			"std_hd_production_pct": round(h.get(age, 0), 1) if h else 0,
			"std_egg_weight_g": 58.0 if h and h.get(age, 0) > 0 else 0,
			"std_uniformity_pct": 85.0, "std_water_feed_ratio": 1.8,
		})
	if step > 1:
		doc.details = [d for d in doc.details if d.age_days % step == 0 or d.age_days == 1]
		for i, d in enumerate(doc.details):
			d.idx = i + 1
	doc.flags.ignore_permissions = True
	doc.insert()


def install():
	for breed, bird_type in BREEDS:
		if not frappe.db.exists("Breed", breed):
			_insert({"doctype": "Breed", "breed_name": breed, "bird_type": bird_type})

	for strain, breed, cycle in STRAINS:
		if not frappe.db.exists("Strain", strain):
			_insert({"doctype": "Strain", "strain_name": strain, "breed": breed,
			         "typical_cycle_days": cycle})

	for name, strain in [("Cobb 500 Broiler Standard", "Cobb 500"),
	                     ("Ross 308 Broiler Standard", "Ross 308"),
	                     ("Vencobb 430 Broiler Standard", "Vencobb 430")]:
		make_standard(name, strain, "Broiler", 49, BROILER_WEIGHT, BROILER_DAILY_FEED,
		              BROILER_MORT)
	for name, strain in [("BV-300 Layer Standard", "BV-300"),
	                     ("Hy-Line W-36 Layer Standard", "Hy-Line W-36")]:
		make_standard(name, strain, "Layer", 518, LAYER_WEIGHT, LAYER_DAILY_FEED, LAYER_MORT,
		              LAYER_HDP, step=7)

	for reason, cat, culling, pm in MORTALITY_REASONS:
		if not frappe.db.exists("Mortality Reason", reason):
			_insert({"doctype": "Mortality Reason", "reason": reason, "category": cat,
			         "is_culling": culling, "requires_postmortem": pm})

	for name, ftype, a, b in FEED_TYPES:
		if not frappe.db.exists("Feed Type", name):
			_insert({"doctype": "Feed Type", "feed_type_name": name, "flock_type": ftype,
			         "age_from_days": a, "age_to_days": b, "bag_weight_kg": 50})

	for code, name, lo, hi, saleable, reject in EGG_GRADES:
		if not frappe.db.exists("Egg Grade", code):
			_insert({"doctype": "Egg Grade", "grade_code": code, "grade_name": name,
			         "min_weight_g": lo, "max_weight_g": hi, "is_saleable": saleable,
			         "is_reject": reject})

	for d, notifiable in DISEASES:
		if not frappe.db.exists("Poultry Disease", d):
			_insert({"doctype": "Poultry Disease", "disease_name": d, "is_notifiable": notifiable})

	for name, disease, route, live, wd in VACCINES:
		if not frappe.db.exists("Vaccine", name):
			_insert({"doctype": "Vaccine", "vaccine_name": name, "disease": disease, "route": route,
			         "live_or_killed": live, "withdrawal_days": wd, "dose_per_bird": 1})

	for name, ing, dose, wd in MEDICATIONS:
		if not frappe.db.exists("Poultry Medication", name):
			_insert({"doctype": "Poultry Medication", "medication_name": name,
			         "active_ingredient": ing, "dose": dose, "withdrawal_days": wd,
			         "route": "Drinking Water"})

	for tname, ftype, rows in [
		("Broiler Standard Schedule", "Broiler", BROILER_SCHEDULE),
		("Layer Standard Schedule", "Layer", LAYER_SCHEDULE),
		("Pullet Rearing Schedule", "Rearing", LAYER_SCHEDULE),
	]:
		if frappe.db.exists("Vaccination Schedule Template", tname):
			continue
		doc = frappe.get_doc({"doctype": "Vaccination Schedule Template", "template_name": tname,
		                      "flock_type": ftype, "is_default": 1})
		for age, vaccine, route in rows:
			doc.append("schedule_details", {"age_days": age, "vaccine": vaccine, "route": route,
			                                "dose_per_bird": 1, "is_mandatory": 1})
		doc.flags.ignore_permissions = True
		doc.insert()

	print("  + reference masters")
