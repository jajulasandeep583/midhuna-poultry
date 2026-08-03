"""Give each poultry icon its own colour.

A presentation attribute on <symbol> beats the stroke frappe's .icon CSS
inherits from the host <svg>, and children inherit it from the symbol - so one
attribute per symbol colours the whole set everywhere it is used.
"""

import re
import sys

COLOURS = {
	# birds - amber family
	"poultry-hen": "#E8A33D",
	"poultry-chick": "#F0B429",
	"poultry-broiler": "#D97757",
	"poultry-layer": "#E8A33D",
	"poultry-rearing": "#EFB33D",
	"poultry-dna": "#B07BD1",
	# eggs - yellow
	"poultry-egg": "#F0B429",
	"poultry-egg-tray": "#E0A11B",
	"poultry-hatchery": "#E8A33D",
	# feed - brown
	"poultry-feed-bag": "#A9743F",
	"poultry-silo": "#A9743F",
	# buildings - slate blue
	"poultry-shed": "#5B8DEF",
	"poultry-farm": "#4178D4",
	"poultry-dispatch": "#5B8DEF",
	# health - teal
	"poultry-syringe": "#17B897",
	"poultry-pill": "#17B897",
	"poultry-virus": "#0E9F85",
	"poultry-schedule": "#12A594",
	"poultry-biosecurity": "#0E9F85",
	# danger - red
	"poultry-mortality": "#E24C4C",
	"poultry-alert": "#E2703A",
	"poultry-withdrawal": "#D9433F",
	# measurement - purple
	"poultry-scale": "#7C5CFC",
	"poultry-standard": "#7C5CFC",
	"poultry-target": "#6C4BE0",
	"poultry-trend-up": "#2CA58D",
	# records - slate
	"poultry-clipboard": "#4B6A88",
	"poultry-board": "#4B6A88",
	"poultry-guide": "#3E7BB6",
	"poultry-help": "#3E7BB6",
	"poultry-closure": "#4B6A88",
	# money and analytics - green
	"poultry-chart": "#2CA58D",
	"poultry-cost": "#1F9254",
	# environment
	"poultry-water": "#3BA7D9",
	"poultry-environment": "#F5793B",
	# people and misc
	"poultry-worker": "#6B7A8F",
	"poultry-search": "#6B7A8F",
	"poultry-settings": "#6B7A8F",
}


def run(path):
	src = open(path, encoding="utf-8").read()

	def repl(m):
		tag, sid = m.group(0), m.group(1)
		colour = COLOURS.get(sid)
		if not colour:
			return tag
		tag = re.sub(r'\s+stroke="[^"]*"', "", tag)
		return tag[:-1] + f' stroke="{colour}">'

	out = re.sub(r'<symbol[^>]*id="icon-([a-z0-9-]+)"[^>]*>', repl, src)
	missing = [i for i in re.findall(r'id="icon-([a-z0-9-]+)"', out) if i not in COLOURS]
	open(path, "w", encoding="utf-8").write(out)
	print(f"coloured {len(COLOURS)} symbols; uncoloured: {missing or 'none'}")


if __name__ == "__main__":
	run(sys.argv[1])
