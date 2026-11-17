"""Add the unit browser to the offline rulebook."""
import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "units"))
from force_org import DEFAULT_SIZE, GAME_SIZES, INFANTRY, PILOTS, unit_family


def build_catalog(output, write_page, search):
    source = ROOT / "units/catalog.json"
    if not source.exists():
        return 0
    catalog = json.loads(source.read_text(encoding="utf-8"))
    config = json.loads((ROOT / "units/points-config.json").read_text(encoding="utf-8"))
    if catalog.get("points_formula") != config:
        raise ValueError("Points configuration changed. Run python build.py to rebuild all costs.")
    if any("cost" not in unit for unit in catalog["units"]):
        raise ValueError("Run units/points.py before building the site")
    (output / "photos").mkdir(exist_ok=True)
    for unit in catalog["units"]:
        if unit["photo"]:
            shutil.copyfile(ROOT / "units" / unit["photo"], output / unit["photo"])
        search.append({"title": unit["name"] + " · " + unit["id"], "page": "Unit catalog",
                       "url": "unit.html?id=" + unit["id"],
                       "text": " ".join([unit_family(unit), unit["set"], unit["faction"], unit["rank"], unit["category"], str(unit["cost"]["points"]) + " points"])})
    # Source prices remain in the import archive; the site publishes one cost.
    published = dict(catalog, units=[dict({key: value for key, value in unit.items() if key != "printed_points"}, family=unit_family(unit))
                                     for unit in catalog["units"]])
    published["force_organization"] = {"default_size": DEFAULT_SIZE, "sizes": GAME_SIZES, "pilots": PILOTS, "infantry": sorted(INFANTRY)}
    published["equipment"] = json.loads((ROOT / "units/equipment.json").read_text(encoding="utf-8"))
    (output / "catalog-data.js").write_text("window.MW_CATALOG = " + json.dumps(published, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    for asset in ("catalog.js", "catalog.css"):
        shutil.copyfile(ROOT / "web" / asset, output / asset)
    with (output / "downloads/unit-catalog.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id", "name", "family", "set", "faction", "rank", "category", "points", "formula_version", "core_legal", "source", "photo_source"])
        for unit in catalog["units"]:
            writer.writerow([unit["id"], unit["name"], unit_family(unit), unit["set"], unit["faction"], unit["rank"], unit["category"], unit["cost"]["points"], unit["cost"]["version"], unit["core_legal"], unit["source_url"], unit["photo_source"]])
    assets = '<link rel="stylesheet" href="catalog.css"><script src="catalog-data.js"></script><script src="catalog.js" defer></script>'
    body = f'''<p>Browse {len(catalog['units']):,} unit entries from the original clix releases, including five DropShip turret sections. Each datasheet has a source photo, combat dial, and <a href="points.html">points cost</a>, plus a heat track for ’Mechs.</p>
<div class="catalog-tools"><a href="downloads/revived-unit-cards.pdf">Download all unit cards (PDF)</a><a href="downloads/unit-catalog.csv">Download the catalog (CSV)</a></div>
<p><a href="builder.html">Build your own force and print unit cards or compact dial sheets for just your models.</a></p>
<p>The PDF prints two cards per Letter page, with every combat-dial position, equipment color, and repair mark. ’Mech cards also include the full heat dial.</p>
<details class="card-guide" id="reading-a-unit-card"><summary>Reading a unit card</summary>
<ul><li><strong>Catalog ID</strong> identifies the exact release and variant, such as AOD108. Use it to find the same miniature in the catalog.</li>
<li><strong>Roster ID</strong> is your own label for one figure: M1 for a ’Mech, V1 for a vehicle, C1a for a conventional infantry base, or A1a for battle armor. It helps distinguish identical figures.</li>
<li><strong>Faction</strong> is the allegiance of this exact catalog figure. A single-faction force uses only figures with that faction; Mixed factions allows any combination.</li>
<li><strong>Squad</strong> records the infantry group, such as C1. <strong>Assigned carrier</strong> records its transport, such as V1. On a vehicle card, mark whether it is a carrier and record its assigned squad. These are roster notes, not proof that the squad is currently aboard; leave unused fields blank.</li>
<li><strong>Clicks</strong> is the damage needed to reach destruction from the starting position. It stays the same on the card; the current dial position tells you how much remains. Heat uses its own separate track.</li>
<li><strong>Full combat dial</strong> shows every position in order. Damage moves right one column per point; repairs move left, subject to repair stops. Start is the starting position, Stop is a repair mark, and End is destroyed. X marks a lost value. SD on the heat dial means shutdown. Color letters keep equipment and heat warnings readable in black-and-white prints.</li></ul></details>
<form class="unit-filters" id="unit-filters" role="search">
<label class="unit-search-label">Find a unit<input id="unit-query" type="search" placeholder="Name, collector ID, or variant…" autocomplete="off"></label>
<label>Set<select id="unit-set"><option value="">All sets</option></select></label>
<label>Type<select id="unit-category"><option value="">All types</option></select></label>
<label>Faction<select id="unit-faction"><option value="">All factions</option></select></label>
<label>Rules<select id="unit-status"><option value="">Full catalog</option><option value="core">Core rules only</option><option value="other">Other unit types</option></select></label>
<label>Sort<select id="unit-sort"><option value="id">Release / collector ID</option><option value="name">Name</option><option value="points">Points: low to high</option><option value="points-desc">Points: high to low</option></select></label>
<button type="reset" class="catalog-reset">Clear filters</button></form>
<p id="unit-count" class="catalog-count" role="status" aria-live="polite"></p>
<div id="unit-grid" class="unit-grid"></div>
<nav class="catalog-pagination" aria-label="Catalog pages"><button id="unit-prev" type="button">← Previous</button><span id="unit-page"></span><button id="unit-next" type="button">Next →</button></nav>
<noscript><p>The unit browser needs JavaScript. Use the PDF cards or CSV above to view the full catalog without it.</p></noscript>
<p class="catalog-credit">Photographs and original dial data: <a href="https://www.warrenborn.com/UnitSection.html">WarrenBorn’s MechWarrior archive</a>. Every datasheet links to its source. Figures outside the current rules are marked; their calculated costs are estimates for later rules.</p>'''
    write_page("units.html", "Unit catalog", "Units", "Figures & datasheets", body + assets, [])
    detail = '<p><a href="units.html">← All units</a></p><div id="unit-detail"><p>Loading the unit…</p></div><noscript><p>Open the <a href="downloads/revived-unit-cards.pdf">printable unit cards</a> to view units without JavaScript.</p></noscript>'
    write_page("unit.html", "Unit datasheet", "Units", "Figures & datasheets", detail + assets, [])
    return 2
