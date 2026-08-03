import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class ChickDispatch(Document):
	def validate(self):
		hatch = frappe.get_doc("Hatch Entry", self.hatch_entry)
		self.company = hatch.company
		self.chicks_dispatched = cint(self.boxes) * cint(self.chicks_per_box) + cint(self.extras)

		if self.chicks_dispatched > cint(hatch.saleable_chicks):
			frappe.msgprint(
				_("Dispatching {0} chicks from a hatch of {1} saleable.").format(
					self.chicks_dispatched, cint(hatch.saleable_chicks)),
				title=_("More than hatched"), indicator="orange")

		if cint(self.chicks_dispatched):
			self.doa_pct = cint(self.doa_chicks) / cint(self.chicks_dispatched) * 100.0
		else:
			self.doa_pct = 0

		if self.destination_type == "Customer" and not self.customer:
			frappe.throw(_("Pick the customer."))
		if self.destination_type == "Own Farm" and not self.to_farm:
			frappe.throw(_("Pick the destination farm."))
