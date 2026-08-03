"""Withdrawal enforcement on outbound documents (§6.4).

A batch on a Delivery Note line resolves back to its flock; if that flock is
inside an active medication withdrawal window the document is blocked, naming
the drug and the date it clears.
"""

import frappe
from frappe import _
from frappe.utils import getdate

from poultry.poultry_utils import active_withdrawals


def block_sales_under_withdrawal(doc, method=None):
	posting = getdate(doc.get("posting_date") or frappe.utils.nowdate())
	blocked = {}

	for row in doc.get("items") or []:
		flock = resolve_flock(row)
		if not flock or flock in blocked:
			continue
		for w in active_withdrawals(flock, posting):
			blocked[flock] = w
			break

	if not blocked:
		return

	lines = [
		_("Flock {0}: {1}, clears {2}").format(flock, w.medication, w.withdrawal_clear_date)
		for flock, w in blocked.items()
	]
	frappe.throw(
		_("These birds or eggs are inside a medication withdrawal period and cannot be sold:")
		+ "<br>" + "<br>".join(lines),
		title=_("Withdrawal Period Active"),
	)


def resolve_flock(row):
	"""A flock's Batch is named after the flock (§3.3), so the batch on the line
	is the lookup key."""
	batch = row.get("batch_no")
	if batch and frappe.db.exists("Flock", batch):
		return batch
	return None
