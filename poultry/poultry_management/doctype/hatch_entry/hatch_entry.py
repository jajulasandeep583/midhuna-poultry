import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from poultry.poultry_management.doctype.egg_setting.egg_setting import refresh


class HatchEntry(Document):
	def validate(self):
		setting = frappe.get_doc("Egg Setting", self.egg_setting)
		self.eggs_set = cint(setting.eggs_set)
		self.fertile_eggs = cint(setting.fertile_eggs)
		self.company = setting.company

		if cint(self.chicks_hatched) > self.eggs_set:
			frappe.throw(_("More chicks than eggs set."))
		if not cint(self.saleable_chicks):
			self.saleable_chicks = cint(self.chicks_hatched) - cint(self.cripples)

		self.dead_in_shell = max(0, self.fertile_eggs - cint(self.chicks_hatched))
		self.hatchability_set_pct = (
			cint(self.chicks_hatched) / self.eggs_set * 100.0) if self.eggs_set else 0
		self.hatchability_fertile_pct = (
			cint(self.chicks_hatched) / self.fertile_eggs * 100.0) if self.fertile_eggs else 0

		# a good chick weighs 67-70% of the egg it came from
		egg_wt = 0
		if self.egg_setting:
			receipt = frappe.db.get_value("Egg Setting", self.egg_setting, "egg_receipt")
			if receipt:
				egg_wt = flt(frappe.db.get_value(
					"Hatching Egg Receipt", receipt, "avg_egg_weight_g"))
		self.chick_yield_pct = (
			flt(self.avg_chick_weight_g) / egg_wt * 100.0) if egg_wt else 0
		if not cint(self.grade_a_chicks) and cint(self.saleable_chicks):
			self.grade_a_chicks = int(cint(self.saleable_chicks) * 0.94)
			self.grade_b_chicks = cint(self.saleable_chicks) - self.grade_a_chicks

		self.saleable_pct = (
			cint(self.saleable_chicks) / cint(self.chicks_hatched) * 100.0
		) if cint(self.chicks_hatched) else 0

	def on_submit(self):
		refresh(self.egg_setting)
		if self.chick_item and self.warehouse and cint(self.saleable_chicks):
			self.receive_chicks()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("Stock Entry", "Stock Ledger Entry", "GL Entry")
		if self.stock_entry and frappe.db.exists("Stock Entry", self.stock_entry):
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.flags.ignore_permissions = True
				se.cancel()
		refresh(self.egg_setting)

	def receive_chicks(self):
		"""Day-old chicks become stock the moment they are counted, so they can
		be placed on a flock or sold without a parallel record."""
		rate = flt(frappe.db.get_value("Item", self.chick_item, "valuation_rate")) or 30.0
		se = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": self.company,
			"posting_date": self.posting_date,
			"set_posting_time": 1,
			"remarks": f"Hatch Entry {self.name}",
			"items": [{
				"item_code": self.chick_item,
				"qty": cint(self.saleable_chicks),
				"t_warehouse": self.warehouse,
				"basic_rate": rate,
			}],
		})
		se.flags.ignore_permissions = True
		se.insert()
		se.submit()
		self.db_set("stock_entry", se.name, update_modified=False)
