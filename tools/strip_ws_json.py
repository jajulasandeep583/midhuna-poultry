"""Strip runtime-built child rows out of the committed workspace json.

Frappe syncs a workspace json during install-app, BEFORE after_install runs.
If that json references Number Cards, Dashboard Charts or a Custom HTML Block
that after_install has not created yet, link validation fails and the whole
install aborts. Those rows are attached at runtime by setup/desk.py and
setup/navblock.py instead.
"""

import json
import os
import sys

STRIP = ("number_cards", "charts", "custom_blocks")


def run(base):
	changed = 0
	for root, _dirs, files in os.walk(base):
		for fname in files:
			if not fname.endswith(".json"):
				continue
			path = os.path.join(root, fname)
			try:
				doc = json.load(open(path, encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Workspace":
				continue
			touched = False
			for key in STRIP:
				if doc.get(key):
					doc[key] = []
					touched = True
			if touched:
				with open(path, "w", encoding="utf-8") as fh:
					json.dump(doc, fh, indent=1, sort_keys=True)
					fh.write("\n")
				changed += 1
				print("  stripped:", os.path.basename(path))
	print(f"workspace json cleaned: {changed}")


if __name__ == "__main__":
	run(sys.argv[1])
