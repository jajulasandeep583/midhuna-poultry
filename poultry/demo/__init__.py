"""Demo dataset. Never run this on a production site.

    bench --site <site> execute poultry.demo.install

Creates items, suppliers and customers, three farms with twelve sheds, nine
flocks at different stages, roughly a month of daily entries with real stock
movement, health records, one closed cycle and a few egg sales.
"""

import frappe


def install():
	from poultry.demo import masters, operations

	print("=== Poultry demo: masters ===")
	masters.install()
	print("=== Poultry demo: base ===")
	operations.run(step="base")
	print("=== Poultry demo: daily entries (this takes a while) ===")
	operations.run(step="entries")
	print("=== Poultry demo: health ===")
	operations.run(step="health")
	print("=== Poultry demo: closure and sales ===")
	operations.run(step="finish")
	frappe.db.commit()
	print("=== Poultry demo loaded. Run poultry.doctor.run to verify. ===")
