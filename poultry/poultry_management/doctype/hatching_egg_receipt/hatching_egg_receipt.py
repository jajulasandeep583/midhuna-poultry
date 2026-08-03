import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, getdate, nowdate


class HatchingEggReceipt(Document):
	"""Eggs arriving from a breeder farm, graded at the door.

	What is rejected here never reaches a setter, so settable % is the first
	number a hatchery manager looks at each morning.
	"""

	def validate(self):
		rejects = (cint(self.cracked_eggs) + cint(self.dirty_eggs)
		           + cint(self.small_eggs) + cint(self.misshapen_eggs))
		if rejects > cint(self.eggs_received):
			frappe.throw(_("Rejects exceed the eggs received."))
		self.settable_eggs = cint(self.eggs_received) - rejects
		self.settable_pct = (
			self.settable_eggs / cint(self.eggs_received) * 100.0
		) if self.eggs_received else 0

		if self.source_flock and not self.breeder_age_weeks:
			age = cint(frappe.db.get_value("Flock", self.source_flock, "age_days"))
			if age:
				self.breeder_age_weeks = round(age / 7.0, 1)
		if self.chick_type and not self.egg_type:
			cat = frappe.db.get_value("Chick Type", self.chick_type, "category")
			self.egg_type = {
				"Broiler": "Broiler Hatching Egg",
				"Layer": "Layer Hatching Egg",
				"Desi / Native": "Desi / Native Hatching Egg",
				"Breeder": "Breeder Hatching Egg",
			}.get(cat)

		self.recompute()

	def recompute(self):
		used = frappe.db.sql(
			"""select coalesce(sum(eggs_set), 0) from `tabEgg Setting`
			   where egg_receipt = %s and docstatus = 1""", self.name)[0][0] if self.name else 0
		self.eggs_set = cint(used)
		self.eggs_in_store = cint(self.settable_eggs) - cint(used)
		self.storage_days = max(0, date_diff(getdate(nowdate()), getdate(self.posting_date)))
		if self.storage_days > 7 and self.eggs_in_store > 0:
			frappe.msgprint(
				_("These eggs have been in store {0} days. Hatchability falls roughly a point "
				  "a day past the first week.").format(self.storage_days),
				title=_("Ageing Stock"), indicator="orange")


def refresh_receipt(name):
	if not name or not frappe.db.exists("Hatching Egg Receipt", name):
		return
	doc = frappe.get_doc("Hatching Egg Receipt", name)
	doc.recompute()
	doc.flags.ignore_permissions = True
	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)
