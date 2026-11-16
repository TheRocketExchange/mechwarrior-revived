"""Check offline HTML links, search destinations, roster costs, and PDF structure."""
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, parse_qs

from lxml import html
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "units"))
from force_org import unit_family, validate_force
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
for unit in published["units"]:
    assert unit["family"] == unit_family(units[unit["id"]]), unit["id"]
    assert "printed_points" not in unit, unit["id"]
with (SITE / "downloads/unit-catalog.csv").open(encoding="utf-8-sig", newline="") as stream:
    catalog_rows = list(csv.DictReader(stream))
assert len(catalog_rows) == len(units)
assert all(row["family"] == unit_family(units[row["id"]]) for row in catalog_rows)
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
    assert len(reader.pages) == (413 if path.name == "revived-unit-cards.pdf" else 1), path
    assert all(tuple(page.mediabox) == (0, 0, 612, 792) for page in reader.pages), path
    if path.name == "readiness-reference.pdf":
        reference_text = reader.pages[0].extract_text()
        assert all(word in reference_text for word in ("Ready", "Committed", "Spent", "Passengers", "Breakthrough"))
pilot_data=json.loads((ROOT / "pilots/cards.json").read_text(encoding="utf-8"))
pilot_rules=(ROOT / "pilots/pilot-cards.md").read_text(encoding="utf-8").replace('’',"'")
for card in pilot_data["cards"]:
    assert card["text"] in pilot_rules, card["role"]
assert not errors, "\n".join(errors)
print(f"Checked {len(pages)} HTML pages, {len(index)} search destinations, local and README links, unit families, PDF offsets, pilot text, and legal force totals: {totals}")
