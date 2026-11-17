"""Publish the browser-local force builder and selected-model print sheets."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build_force_builder(output, write_page, search):
    for name in ("force-model.js", "builder.js", "builder.css", "force-cards.js", "force-cards.css"):
        shutil.copyfile(ROOT / "web" / name, output / name)
    samples = json.loads((ROOT / "playtest/forces.json").read_text(encoding="utf-8"))
    starter = json.loads((ROOT / "scenarios/first-contact.json").read_text(encoding="utf-8"))
    samples["forces"].extend(starter["forces"])
    (output / "builder-data.js").write_text("window.MW_SAMPLE_FORCES = " + json.dumps(samples, ensure_ascii=False) + ";\n", encoding="utf-8")
    assets = '<script src="catalog-data.js"></script><script src="force-model.js"></script>'
    body = (ROOT / "web/builder.html").read_text(encoding="utf-8")
    body += assets + '<script src="builder-data.js"></script><script src="builder.js" defer></script><link rel="stylesheet" href="builder.css">'
    write_page("builder.html", "Army builder", "Forces", "", body,
               [("h2", "Your force", "force-summary-heading"), ("h2", "Roster", "force-roster-heading"),
                ("h2", "Add models", "force-picker-heading")])
    cards = '<p id="force-card-status" role="status">Preparing your army…</p><div class="force-card-tools"><label>Print format<select id="force-print-layout"><option value="cards">Unit cards</option><option value="dials">Dials only</option></select></label><button id="print-force-cards" type="button" disabled>Print / Save as PDF</button><a href="builder.html">Back to the force builder</a></div><div id="force-card-output"></div><noscript><p>Enable JavaScript to print your selected army, or use the <a href="downloads/revived-unit-cards.pdf">complete card PDF</a>.</p></noscript>'
    cards += assets + '<script src="force-cards.js" defer></script><link rel="stylesheet" href="force-cards.css">'
    write_page("force-cards.html", "Army cards", "Forces", "", cards, [])
    search.extend([
        {"title": "Army builder", "page": "Army builder", "url": "builder.html", "text": "Army lists for Skirmish 600, Standard 1200, Large Battle 1800, or Grand Battle 2400 points. Model filters by faction, type, and points. Squads, pilots, carriers, Rocket substitutes, force limits, saved lists, import and export."},
        {"title": "Army cards", "page": "Army builder", "url": "builder.html", "text": "Printable unit cards and compact dial sheets for a selected army. Full combat and heat dials, roster IDs, pilots, and carrier assignments. Print or save as PDF."},
    ])
    return 2
