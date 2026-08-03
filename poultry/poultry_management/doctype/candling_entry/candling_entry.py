import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from poultry.poultry_management.doctype.egg_setting.egg_setting import refresh


class CandlingEntry(Document):
	def validate(self):
		setting = frappe.get_doc("Egg Setting", self.egg_setting)
		self.eggs_set = cint(setting.eggs_set)
		self.company = setting.company

		removed = cint(self.clear_eggs) + cint(self.dead_germ) + cint(self.contaminated)
		if removed > self.eggs_set:
			frappe.throw(_("{0} eggs removed but only {1} were set.").format(
				removed, self.eggs_set))
		self.fertile_eggs = self.eggs_set - removed
		self.fertility_pct = (
			self.fertile_eggs / self.eggs_set * 100.0) if self.eggs_set else 0

	def on_submit(self):
		refresh(self.egg_setting)

	def on_cancel(self):
		refresh(self.egg_setting)
