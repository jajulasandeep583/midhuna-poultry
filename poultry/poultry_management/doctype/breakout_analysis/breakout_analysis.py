import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class BreakoutAnalysis(Document):
	"""Break out the residue and the hatch tells you what went wrong.

	Infertile points at the breeder flock. Early dead points at storage or
	handling. Late dead and pipped-not-hatched point at the machine. Without
	this a poor hatch is just a number nobody can act on.
	"""

	def validate(self):
		setting = frappe.get_doc("Egg Setting", self.egg_setting)
		self.company = setting.company

		total = (cint(self.infertile) + cint(self.early_dead) + cint(self.mid_dead)
		         + cint(self.late_dead) + cint(self.pipped_not_hatched)
		         + cint(self.contaminated) + cint(self.malpositioned))
		if total > cint(self.eggs_broken):
			frappe.throw(_("Classified {0} eggs but only {1} were broken out.").format(
				total, cint(self.eggs_broken)))

		base = cint(self.eggs_broken) or 1
		self.infertile_pct = cint(self.infertile) / base * 100.0
		self.early_dead_pct = cint(self.early_dead) / base * 100.0
		self.late_dead_pct = cint(self.late_dead) / base * 100.0
		self.contamination_pct = cint(self.contaminated) / base * 100.0
		self.likely_cause = self.read_it()

	def read_it(self):
		"""The standard reading a hatchery manager applies to a breakout."""
		base = cint(self.eggs_broken) or 1
		share = lambda n: cint(n) / base * 100.0  # noqa: E731

		if share(self.contaminated) > 2:
			return "Contamination / hygiene"
		if share(self.infertile) > 45:
			return "Breeder flock fertility"
		if share(self.early_dead) > 25:
			return "Egg storage / age"
		if share(self.pipped_not_hatched) > 15:
			return "Hatcher humidity"
		if share(self.late_dead) > 25:
			return "Setter temperature"
		if share(self.malpositioned) > 10:
			return "Turning"
		return "Inconclusive"
