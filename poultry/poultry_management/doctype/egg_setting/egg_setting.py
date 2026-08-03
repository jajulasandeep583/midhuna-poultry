import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate

# incubation: candle at 18, transfer at 18, hatch at 21
CANDLE_DAY, TRANSFER_DAY, HATCH_DAY = 18, 18, 21


class EggSetting(Document):
	def validate(self):
		d = getdate(self.set_date)
		self.candling_date = add_days(d, CANDLE_DAY)
		self.transfer_date = add_days(d, TRANSFER_DAY)
		self.hatch_date = add_days(d, HATCH_DAY)

		if self.source_flock and not self.breeder_age_weeks:
			age = cint(frappe.db.get_value("Flock", self.source_flock, "age_days"))
			if age:
				self.breeder_age_weeks = round(age / 7.0, 1)
		if not self.company and self.setter:
			self.company = frappe.db.get_value("Hatchery Machine", self.setter, "company")

		capacity = cint(frappe.db.get_value("Hatchery Machine", self.setter, "capacity_eggs"))
		if capacity and cint(self.eggs_set) > capacity:
			frappe.msgprint(
				_("{0} eggs into a setter rated for {1}.").format(cint(self.eggs_set), capacity),
				title=_("Above Setter Capacity"), indicator="orange")

		self.recompute()

	def recompute(self):
		"""Fertility comes from candling, hatch from the hatch entry - both are
		read back rather than typed here."""
		fertile = frappe.db.sql(
			"""select coalesce(sum(fertile_eggs), 0) from `tabCandling Entry`
			   where egg_setting = %s and docstatus = 1""", self.name)[0][0] if self.name else 0
		hatched = frappe.db.sql(
			"""select coalesce(sum(chicks_hatched), 0) from `tabHatch Entry`
			   where egg_setting = %s and docstatus = 1""", self.name)[0][0] if self.name else 0

		self.fertile_eggs = cint(fertile)
		self.chicks_hatched = cint(hatched)
		self.fertility_pct = (cint(fertile) / cint(self.eggs_set) * 100.0) if self.eggs_set else 0
		self.hatchability_set_pct = (
			cint(hatched) / cint(self.eggs_set) * 100.0) if self.eggs_set else 0
		self.hatchability_fertile_pct = (
			cint(hatched) / cint(fertile) * 100.0) if fertile else 0

		if hatched:
			self.status = "Hatched"
		elif fertile:
			self.status = "Candled"
		elif self.docstatus == 1:
			self.status = "Set"

	def on_submit(self):
		self.update_receipt()

	def on_cancel(self):
		self.update_receipt()

	def update_receipt(self):
		if self.egg_receipt:
			from poultry.poultry_management.doctype.hatching_egg_receipt.hatching_egg_receipt \
				import refresh_receipt

			refresh_receipt(self.egg_receipt)


def refresh(setting):
	doc = frappe.get_doc("Egg Setting", setting)
	doc.recompute()
	doc.flags.ignore_permissions = True
	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)
