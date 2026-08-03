import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, getdate, nowdate

from poultry.poultry_utils import (
	age_days,
	eggs_per_tray,
	recompute_flock,
	settings,
	standard_row,
)


class DailyFlockEntry(Document):
	"""The primary transaction. One per flock per day, enforced.

	Everything below the two mandatory numbers - mortality and feed - is
	derived. The system is fully functional on those two alone (§11.2).
	"""

	def validate(self):
		self.cfg = settings()
		self.flock_doc = frappe.get_doc("Flock", self.flock)
		self.validate_flock_active()
		self.validate_date()
		self.validate_duplicate()
		self.derive_header()
		self.derive_feed()
		self.derive_eggs()
		self.derive_counts()
		self.derive_ratios()
		self.run_sanity_checks()
		self.evaluate_alerts()

	def on_submit(self):
		if cint(settings().create_stock_entries):
			self.post_stock()
		recompute_flock(self.flock)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("Stock Entry", "Stock Ledger Entry", "GL Entry")
		self.reverse_stock()
		recompute_flock(self.flock)

	# ------------------------------------------------------------ validation
	def validate_flock_active(self):
		if self.flock_doc.status in ("Draft", "Closed"):
			frappe.throw(
				_("Flock {0} is {1}. Daily entries are only accepted for a placed flock.").format(
					frappe.bold(self.flock), frappe.bold(self.flock_doc.status)
				)
			)

	def validate_date(self):
		posting = getdate(self.posting_date)
		if posting < getdate(self.flock_doc.placement_date):
			frappe.throw(_("Date is before the flock was placed on {0}.").format(
				self.flock_doc.placement_date))
		if posting > getdate(nowdate()):
			frappe.throw(_("Date is in the future."))

		back = date_diff(getdate(nowdate()), posting)
		if back > 0:
			if not cint(self.cfg.allow_backdated_entry):
				frappe.throw(_("Backdated entry is switched off in Poultry Settings."))
			# Blocking late entry is the main reason field staff abandon these
			# systems; late data beats absent data (§7.4).
			if back > cint(self.cfg.max_backdate_days):
				frappe.throw(
					_("Entry is {0} days old; the limit is {1}. A manager must raise it in Poultry Settings.")
					.format(back, cint(self.cfg.max_backdate_days))
				)

	def validate_duplicate(self):
		existing = frappe.db.get_value(
			"Daily Flock Entry",
			{"flock": self.flock, "posting_date": self.posting_date,
			 "docstatus": ["<", 2], "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(_("Entry {0} already exists for this flock on {1}.").format(
				frappe.bold(existing), self.posting_date))

	# ------------------------------------------------------------ derivation
	def derive_header(self):
		self.age_days = age_days(self.flock_doc.placement_date, self.posting_date)
		self.farm = self.flock_doc.farm
		self.shed = self.flock_doc.shed
		self.company = self.flock_doc.company
		self.flock_type = self.flock_doc.flock_type

	def derive_feed(self):
		"""Staff count bags; the ledger needs kilograms. The conversion is always
		server-side and auditable (§7.2)."""
		total = 0.0
		shed_wh = frappe.db.get_value("Shed", self.shed, "warehouse")
		for row in self.feed_details:
			if row.feed_type and not row.item:
				row.item = frappe.db.get_value("Feed Type", row.feed_type, "item")
			if not row.bag_weight_kg:
				row.bag_weight_kg = flt(
					frappe.db.get_value("Feed Type", row.feed_type, "bag_weight_kg")
				) or flt(self.cfg.default_bag_weight_kg) or 50.0
			if flt(row.bags):
				row.qty_kg = flt(row.bags) * flt(row.bag_weight_kg)
			if not row.warehouse:
				row.warehouse = shed_wh
			total += flt(row.qty_kg)
		self.total_feed_kg = flt(total, 3)

	def derive_eggs(self):
		"""Trays in, eggs out - same reason as feed bags."""
		per_tray = eggs_per_tray()
		total = 0
		for row in self.egg_details:
			if row.egg_grade and not row.item:
				row.item = frappe.db.get_value("Egg Grade", row.egg_grade, "item")
			if flt(row.trays):
				row.qty = cint(flt(row.trays) * per_tray)
			if not row.warehouse:
				row.warehouse = self.cfg.egg_warehouse
			total += cint(row.qty)
		self.total_eggs = total

	def derive_counts(self):
		"""Opening comes from the ledger of prior entries, never carried forward
		on the document (§3.7)."""
		prior = frappe.db.sql(
			"""
			select coalesce(sum(mortality_qty), 0) + coalesce(sum(cull_qty), 0)
			from `tabDaily Flock Entry`
			where flock = %s and docstatus = 1 and posting_date < %s and name != %s
			""",
			(self.flock, self.posting_date, self.name or ""),
		)[0][0]

		placed = cint(self.flock_doc.opening_qty)
		self.opening_qty = placed - cint(prior) - cint(self.flock_doc.cumulative_sold)
		self.closing_qty = self.opening_qty - cint(self.mortality_qty) - cint(self.cull_qty)

		losses_today = cint(self.mortality_qty) + cint(self.cull_qty)
		self.mortality_pct_today = (losses_today / self.opening_qty * 100.0) if self.opening_qty else 0.0
		self.cumulative_mortality_pct = ((cint(prior) + losses_today) / placed * 100.0) if placed else 0.0

		cum_feed = frappe.db.sql(
			"""
			select coalesce(sum(total_feed_kg), 0)
			from `tabDaily Flock Entry`
			where flock = %s and docstatus = 1 and posting_date < %s and name != %s
			""",
			(self.flock, self.posting_date, self.name or ""),
		)[0][0]
		self.cumulative_feed_kg = flt(cum_feed) + flt(self.total_feed_kg)

	def derive_ratios(self):
		birds = self.closing_qty or self.opening_qty
		self.feed_per_bird_g = (flt(self.total_feed_kg) * 1000.0 / birds) if birds else 0.0
		self.water_feed_ratio = (
			flt(self.water_litres) / flt(self.total_feed_kg) if flt(self.total_feed_kg) else 0.0
		)
		# HDP is eggs per hen alive that day, not per hen placed (§7.1)
		self.hd_production_pct = (
			(cint(self.total_eggs) / birds * 100.0) if (birds and self.total_eggs) else 0.0
		)

	# ------------------------------------------------------------ safety
	def run_sanity_checks(self):
		"""Typo-shaped values are caught before they reach the ledger (§7.6).
		A single mistyped figure would otherwise distort the whole flock."""
		losses = cint(self.mortality_qty) + cint(self.cull_qty)
		if losses > self.opening_qty:
			frappe.throw(
				_("{0} deaths recorded but only {1} birds are alive.").format(losses, self.opening_qty)
			)
		if self.opening_qty and losses > 0.05 * self.opening_qty:
			frappe.msgprint(
				_("{0} birds is {1}% of the flock in one day. Please confirm this is correct.").format(
					losses, round(losses / self.opening_qty * 100, 1)
				),
				title=_("Unusually High Mortality"), indicator="red",
			)
		if flt(self.feed_per_bird_g) > 250:
			frappe.msgprint(
				_("Feed works out to {0} g per bird today. Please confirm the bag count.").format(
					round(flt(self.feed_per_bird_g))
				),
				title=_("Unusually High Feed"), indicator="orange",
			)

	def evaluate_alerts(self):
		"""Managers should not have to open a report to discover a problem
		(§7.5) - the entry carries its own verdict."""
		alerts = []
		std = standard_row(self.flock, self.age_days)

		spike = flt(self.cfg.mortality_spike_threshold_pct) or 0.5
		if flt(self.mortality_pct_today) > spike:
			alerts.append(
				_("Mortality {0}% today is above the {1}% spike threshold.").format(
					round(flt(self.mortality_pct_today), 2), spike)
			)

		if std:
			dev = flt(self.cfg.weight_deviation_threshold_pct) or 10.0
			if flt(self.avg_body_weight_g) and flt(std.std_body_weight_g):
				diff = (flt(self.avg_body_weight_g) - flt(std.std_body_weight_g)) / flt(
					std.std_body_weight_g) * 100.0
				if abs(diff) > dev:
					alerts.append(
						_("Body weight {0} g is {1}% off the standard {2} g for day {3}.").format(
							round(flt(self.avg_body_weight_g)), round(diff, 1),
							round(flt(std.std_body_weight_g)), self.age_days)
					)

			factor = flt(self.cfg.cumulative_mortality_factor) or 1.5
			if flt(std.std_cumulative_mortality_pct) and flt(self.cumulative_mortality_pct) > (
					factor * flt(std.std_cumulative_mortality_pct)):
				alerts.append(
					_("Cumulative mortality {0}% is more than {1}x the standard {2}% for day {3}.").format(
						round(flt(self.cumulative_mortality_pct), 2), factor,
						round(flt(std.std_cumulative_mortality_pct), 2), self.age_days)
				)

			wf = flt(self.cfg.water_feed_factor) or 1.25
			if flt(self.water_feed_ratio) and flt(std.std_water_feed_ratio) and (
					flt(self.water_feed_ratio) > wf * flt(std.std_water_feed_ratio)):
				# Often precedes anything visible in the shed.
				alerts.append(
					_("Water:feed {0} is above {1}x the standard {2}.").format(
						round(flt(self.water_feed_ratio), 2), wf, round(flt(std.std_water_feed_ratio), 2))
				)

		for w in active_withdrawal_messages(self.flock, self.posting_date):
			alerts.append(w)

		self.has_alert = 1 if alerts else 0
		self.alert_message = "\n".join(alerts) if alerts else None

	# ------------------------------------------------------------ stock
	def post_stock(self):
		if flt(self.total_feed_kg):
			self.feed_stock_entry = self.make_feed_issue()
		losses = cint(self.mortality_qty) + cint(self.cull_qty)
		if losses and self.flock_doc.bird_item:
			self.mortality_stock_entry = self.make_mortality_issue(losses)
		if cint(self.total_eggs):
			self.egg_stock_entry = self.make_egg_receipt()
		self.db_set("feed_stock_entry", self.feed_stock_entry, update_modified=False)
		self.db_set("mortality_stock_entry", self.mortality_stock_entry, update_modified=False)
		self.db_set("egg_stock_entry", self.egg_stock_entry, update_modified=False)

	def _new_entry(self, purpose):
		return frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": purpose,
			"purpose": purpose,
			"company": self.company,
			"posting_date": self.posting_date,
			"set_posting_time": 1,
			"poultry_flock": self.flock,
			"project": self.flock_doc.project,
			"remarks": f"Daily Flock Entry {self.name}",
			"items": [],
		})

	def make_feed_issue(self):
		se = self._new_entry("Material Issue")
		for row in self.feed_details:
			if not (row.item and flt(row.qty_kg)):
				continue
			se.append("items", {
				"item_code": row.item,
				"qty": flt(row.qty_kg),
				"s_warehouse": row.warehouse,
				"cost_center": self.flock_doc.cost_center,
			})
		if not se.items:
			return None
		return _submit(se)

	def make_mortality_issue(self, losses):
		shed_wh = frappe.db.get_value("Shed", self.shed, "warehouse")
		se = self._new_entry("Material Issue")
		item = {
			"item_code": self.flock_doc.bird_item,
			"qty": losses,
			"s_warehouse": shed_wh,
			"cost_center": self.flock_doc.cost_center,
		}
		if self.cfg.mortality_expense_account:
			item["expense_account"] = self.cfg.mortality_expense_account
		if self.flock_doc.batch_no:
			item["batch_no"] = self.flock_doc.batch_no
		se.append("items", item)
		return _submit(se)

	def make_egg_receipt(self):
		se = self._new_entry("Material Receipt")
		for row in self.egg_details:
			if not (row.item and cint(row.qty)):
				continue
			rate = flt(frappe.db.get_value("Item", row.item, "valuation_rate")) or 4.0
			se.append("items", {
				"item_code": row.item,
				"qty": cint(row.qty),
				"t_warehouse": row.warehouse or self.cfg.egg_warehouse,
				"basic_rate": rate,
				"cost_center": self.flock_doc.cost_center,
			})
		if not se.items:
			return None
		return _submit(se)

	def reverse_stock(self):
		for field in ("feed_stock_entry", "mortality_stock_entry", "egg_stock_entry"):
			name = self.get(field)
			if not name or not frappe.db.exists("Stock Entry", name):
				continue
			se = frappe.get_doc("Stock Entry", name)
			if se.docstatus == 1:
				se.flags.ignore_permissions = True
				se.cancel()


def _submit(se):
	se.flags.ignore_permissions = True
	se.insert()
	se.submit()
	return se.name


def active_withdrawal_messages(flock, on_date):
	from poultry.poultry_utils import active_withdrawals

	return [
		_("Flock is under withdrawal for {0} until {1} and cannot be sold.").format(
			w.medication, w.withdrawal_clear_date)
		for w in active_withdrawals(flock, on_date)
	]
