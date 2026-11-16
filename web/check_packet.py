"""Check offline HTML links, search destinations, roster costs, and PDF structure."""
import csv
import math
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, parse_qs

from lxml import html
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "units"))
from force_org import DEFAULT_SIZE, GAME_SIZES, unit_family, validate_force
SITE = ROOT / "site"
catalog = json.loads((ROOT / "units/catalog.json").read_text(encoding="utf-8"))
units = {u["id"]:u for u in catalog["units"]}
pages = {path.resolve():html.fromstring(path.read_text(encoding="utf-8")) for path in SITE.glob("*.html")}
errors = []


def check_link(source, link):
    parts = urlsplit(link)
    if parts.scheme or parts.netloc:
        return
    target = (source.parent / unquote(parts.path)).resolve() if parts.path else source
    if not target.exists():
        errors.append(f"{source.name}: missing {link}")
    elif target in pages and parts.fragment and not pages[target].xpath('//*[@id=$value]',value=unquote(parts.fragment)):
        errors.append(f"{source.name}: missing anchor {link}")
    if target.name == "unit.html" and "id" in parse_qs(parts.query):
        if parse_qs(parts.query)["id"][0] not in units:
            errors.append(f"{source.name}: unknown unit {link}")


for path, page in pages.items():
    assert len(page.xpath('//h1')) == 1, path
    ids = page.xpath('//*[@id]/@id')
    assert len(ids) == len(set(ids)), path
    for link in page.xpath('//@href|//@src'):
        check_link(path,link)
index = json.loads((SITE / "search-index.js").read_text(encoding="utf-8").split(" = ",1)[1].rstrip(";\n"))
for record in index:
    check_link(SITE / "index.html",record["url"])
# README links should open the published page, anchor, or download they name.
readme = (ROOT / "README.md").read_text(encoding="utf-8")
live_base = "https://therocketexchange.github.io/mechwarrior-revived/"
for suffix in re.findall(re.escape(live_base) + r'([^\s)<>]*)', readme):
    check_link(SITE / "index.html", suffix or "index.html")
published = json.loads((SITE / "catalog-data.js").read_text(encoding="utf-8").split(" = ", 1)[1].rstrip(";\n"))
assert len(published["units"]) == len(units)
assert published["force_organization"]["sizes"] == GAME_SIZES
assert published["force_organization"]["default_size"] == DEFAULT_SIZE
# Check the written force chart against the data used by both validators.
rules_page = pages[(SITE / "rules.html").resolve()]
sizes_table = rules_page.xpath('//*[@id="choose-the-battle-size"]/following::table[1]')[0]
assert [[cell.text_content().strip() for cell in row.xpath('./td')] for row in sizes_table.xpath('.//tbody/tr')] == [[size["name"], f"{size['points_limit']:,}", f"{size['board_width']} × {size['board_depth']} inches"] for size in GAME_SIZES.values()]
chart = rules_page.xpath('//*[@id="force-organization"]/following::table[1]')[0]
rows = [[cell.text_content().strip() for cell in row.xpath('./th|./td')] for row in chart.xpath('.//tr')]
assert rows[0][1:] == [size["name"] for size in GAME_SIZES.values()]
for column, size in enumerate(GAME_SIZES.values(), 1):
    limit = size["limits"]
    assert [row[column] for row in rows[1:]] == [f"{limit['mechs_min']}–{limit['mechs_max']}", f"0–{limit['vehicles_max']}", f"0–{limit['squads_max']}", str(limit['carriers_max']), str(limit['pilot_max'])]
for unit in published["units"]:
    assert unit["family"] == unit_family(units[unit["id"]]), unit["id"]
    assert "printed_points" not in unit, unit["id"]
    assert unit["cost"] == units[unit["id"]]["cost"], unit["id"]
    assert unit["rocket_options"] == units[unit["id"]]["rocket_options"], unit["id"]
with (SITE / "downloads/unit-catalog.csv").open(encoding="utf-8-sig", newline="") as stream:
    catalog_rows = list(csv.DictReader(stream))
assert len(catalog_rows) == len(units)
assert all(row["family"] == unit_family(units[row["id"]]) for row in catalog_rows)
assert all(int(row["points"]) == units[row["id"]]["cost"]["points"] and row["formula_version"] == catalog["points_formula"]["version"] for row in catalog_rows)
with (ROOT / "playtest/sample-forces.csv").open(encoding="utf-8",newline="") as stream:
    rows = list(csv.DictReader(stream))
totals = {}
for row in rows:
    unit = units[row["catalog_id"]]
    cost = unit["rocket_options"][row["rocket_slot"]] if row.get("rocket_slot") else unit["cost"]
    assert int(row["points_each"]) == cost["points"]
    assert row["formula_version"] == unit["cost"]["version"]
    totals[row["force"]] = totals.get(row["force"],0) + int(row["quantity"]) * int(row["points_each"])
rosters = json.loads((ROOT / "playtest/forces.json").read_text(encoding="utf-8"))
assert totals == {force["id"]: validate_force(force, units, rosters["limit"])["total"] for force in rosters["forces"]}
for path in (ROOT / "units/revived-unit-cards.pdf", ROOT / "pilots/revived-pilot-cards.pdf", ROOT / "rules/readiness-reference.pdf"):
    data=path.read_bytes()
    start=int(re.search(rb'startxref\s+(\d+)',data).group(1))
    assert data[start:start+4] == b'xref', path
    lines=data[start:].splitlines()
    count=int(lines[1].split()[1])
    for object_id,line in enumerate(lines[3:count+2],1):
        offset=int(line.split()[0])
        assert data.startswith(f'{object_id} 0 obj'.encode(),offset), (path,object_id)
    assert (SITE / "downloads" / path.name).read_bytes() == data
    reader = PdfReader(path)
    assert len(reader.pages) == (math.ceil(len(units) / 2) if path.name == "revived-unit-cards.pdf" else 1), path
    assert all(tuple(page.mediabox) == (0, 0, 612, 792) for page in reader.pages), path
    if path.name == "revived-unit-cards.pdf":
        # Audit the printed output against the source data, including every
        # dial value and color, instead of trusting the generator's page count.
        codes = {"white":"", "red":"R", "blue":"B", "black":"K", "gray":"Gy", "green":"Gn", "yellow":"Y", "purple":"P"}
        compact = lambda value: re.sub(r"\s+", "", value)
        def expected_cell(cell, heat=False):
            if cell.get("shutdown"):
                return "SD"
            if cell.get("dead"):
                return "X"
            value = cell.get("value")
            if value is None:
                return "-"
            return (f"{value:+d}" if heat and value else str(value)) + codes[cell.get("color", "white")]
        printed_ids = []
        for page in reader.pages:
            page_text = page.extract_text()
            assert "Formula " + catalog["points_formula"]["version"] in page_text
            blocks = page_text.split("Catalog ID: ")[1:]
            for block in blocks:
                unit_id = block.split()[0]
                unit = units[unit_id]
                printed_ids.append(unit_id)
                content = compact(block)
                assert re.search(r"\b" + str(unit["cost"]["points"]) + r"\s+POINTS", block), unit_id
                assert "RosterID:" in content and "Liveclicks" not in content, unit_id
                assert f"Clicks:{len(unit['track'])-unit['start']}(damagefromStarttoEnd)" in content, unit_id
                combat = content.split("COMBATDIAL",1)[1].split("HEATDIAL",1)[0]
                assert "Click" + "".join(str(i+1) for i in range(len(unit["track"]))) + "End" in combat, unit_id
                fields = [(w["slot"], w["slot"].title()+"dmg") for w in unit["weapons"]] + [(k,k.title()) for k in ("speed","attack","defense")]
                for key, label in fields:
                    expected = label + "".join(expected_cell(click.get(key,{})) for click in unit["track"]) + "X"
                    assert expected in combat, (unit_id, key)
                repair_count = sum(bool(click.get("markers",{}).get("repair")) for i,click in enumerate(unit["track"]) if i != unit["start"])
                assert "MarksStart" + "Stop" * repair_count + "End" in combat, unit_id
                if unit["heat"]:
                    heat = content.split("HEATDIAL",1)[1]
                    assert "ClickStart" + "".join(str(i) for i in range(1,len(unit["heat"]))) in heat, unit_id
                    for key in ("primary", "secondary", "speed"):
                        if any(key in click for click in unit["heat"]):
                            label = key.title() + ("dmg" if key != "speed" else "")
                            assert label + "".join(expected_cell(click.get(key,{}), True) for click in unit["heat"]) in heat, (unit_id,key)
        assert printed_ids == list(units), "Missing, duplicate, or reordered PDF cards"
    if path.name == "readiness-reference.pdf":
        reference_text = reader.pages[0].extract_text()
        assert all(word in reference_text for word in ("Ready", "Committed", "Spent", "Passengers", "Breakthrough"))
    if path.name == "revived-pilot-cards.pdf":
        role_limits = " / ".join(f"{size['name'].removesuffix(' Battle')} {size['limits']['pilot_max']}" for size in GAME_SIZES.values())
        assert role_limits in reader.pages[0].extract_text()
pilot_data=json.loads((ROOT / "pilots/cards.json").read_text(encoding="utf-8"))
pilot_rules=(ROOT / "pilots/pilot-cards.md").read_text(encoding="utf-8").replace('’',"'")
for card in pilot_data["cards"]:
    assert card["text"] in pilot_rules, card["role"]
assert not errors, "\n".join(errors)
print(f"Checked {len(pages)} HTML pages, {len(index)} search destinations, local and README links, unit families, PDF offsets, pilot text, and legal force totals: {totals}")
