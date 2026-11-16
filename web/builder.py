"""Publish the browser-local force builder and selected-model print sheets."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build_force_builder(output, write_page, search):
    for name in ("force-model.js", "builder.js", "builder.css", "force-cards.js", "force-cards.css"):
        shutil.copyfile(ROOT / "web" / name, output / name)
    samples = json.loads((ROOT / "playtest/forces.json").read_text(encoding="utf-8"))
    (output / "builder-data.js").write_text("window.MW_SAMPLE_FORCES = " + json.dumps(samples, ensure_ascii=False) + ";\n", encoding="utf-8")
    assets = '<script src="catalog-data.js"></script><script src="force-model.js"></script>'
    body = (ROOT / "web/builder.html").read_text(encoding="utf-8")
    body += assets + '<script src="builder-data.js"></script><script src="builder.js" defer></script><link rel="stylesheet" href="builder.css">'
    write_page("builder.html", "Build a force", "Forces", "Your models / Your list", body, [])
    cards = '<p id="force-card-status" role="status">Preparing your unit cards…</p><div class="force-card-tools"><button id="print-force-cards" type="button">Print / Save as PDF</button><a href="builder.html">Back to the force builder</a></div><div id="force-card-output"></div><noscript><p>Enable JavaScript to generate the selected cards.</p></noscript>'
    cards += assets + '<script src="force-cards.js" defer></script><link rel="stylesheet" href="force-cards.css">'
    write_page("force-cards.html", "Your unit cards", "Forces", "Ready for the table", cards, [])
    search.extend([
        {"title": "Build a force", "page": "Force builder", "url": "builder.html", "text": "Build an army list. Choose models, infantry squads, pilots, carriers, and Rocket substitutes. Check points and the rule of three. Save and export your roster."},
        {"title": "Print cards for your models", "page": "Force builder", "url": "builder.html", "text": "Generate full-dial unit cards for just the models in your army. Print or save as PDF with roster IDs and assignments filled in."},
    ])
    return 2
