"""Build an offline HTML rulebook from the canonical Markdown packet.

Run from any directory: python web/build.py
Requires markdown-it-py (see requirements.txt). The generated site needs no server.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from catalog import build_catalog
from builder import build_force_builder

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
WEB = ROOT / "web"
MD = MarkdownIt("commonmark", {"html": False}).enable("table")

# Source, output, display title, primary navigation, eyebrow.
PAGES = [
    ("README.md", "index.html", "MechWarrior Revived", "Home", "Rules for your clix collection"),
    ("rules/core-rules.md", "rules.html", "Core rules", "Rules", "Rules / 01"),
    ("rules/weapon-reference.md", "weapons.html", "Weapon reference", "Rules", "Rules / 02"),
    ("rules/equipment-reference.md", "equipment.html", "Equipment reference", "Rules", "Rules / 03"),
    ("rules/points.md", "points.html", "Points", "Rules", "Building armies"),
    ("rules/turn-reference.md", "turn.html", "Turn reference", "Game aids", "At the table / 01"),
    ("rules/readiness-reference.md", "readiness.html", "Readiness reference", "Game aids", "At the table / Readiness"),
    ("pilots/pilot-cards.md", "pilots.html", "Pilot cards", "Game aids", "At the table / 02"),
    ("playtest/sample-forces.md", "forces.html", "Sample forces", "Forces", "Build your force"),
    ("playtest/starter-forces.md", "starter-forces.html", "Starter patrols", "Forces", "First Contact / Two patrols"),
    ("playtest/dead-air.md", "dead-air.html", "Dead Air", "Scenarios", "The Fight for Kestrel Relay / Starter pack"),
    ("scenarios/00-first-contact.md", "first-contact.html", "First Contact", "Scenarios", "Start here / First battle"),
    ("scenarios/01-seize-and-hold.md", "seize-and-hold.html", "Seize and Hold", "Scenarios", "Mission / 01"),
    ("scenarios/02-breakthrough.md", "breakthrough.html", "Breakthrough", "Scenarios", "Mission / 02"),
    ("scenarios/03-hold-the-station.md", "hold-the-station.html", "Hold the Station", "Scenarios", "Mission / 03"),
    ("playtest/protocol.md", "playtest.html", "Playtest plan", "Development", "Testing / Plan"),
    ("playtest/playtest-log.md", "log.html", "Game log", "Development", "Testing / Record a game"),
    ("docs/design-brief.md", "design.html", "Design notes", "Development", "About the rules"),
    ("docs/combat-rhythm.md", "combat-rhythm.html", "How v0.3 changes a battle", "Development", "Development / Worked examples"),
    ("docs/comparison.md", "comparison.html", "Rules & handbook comparison", "Development", "Development / Community sources"),
    ("docs/sources.md", "sources.html", "Sources", "Development", "Background reading"),
    ("playtest/validation.md", "validation.html", "Checks so far", "Development", "Testing / Progress"),
]
SOURCE_URL = {(ROOT / p[0]).resolve(): p[1] for p in PAGES}
NAV = [("Rules", "rules.html"), ("Units", "units.html"), ("Forces", "builder.html"),
       ("Scenarios", "scenarios.html"), ("Game aids", "aids.html"),
       ("Development", "design.html")]
DOWNLOADS = ["rules/readiness-reference.pdf", "pilots/revived-pilot-cards.pdf", "pilots/revived-pilot-cards-preview.png",
             "playtest/sample-forces.csv", "playtest/adjustments.csv", "units/revived-unit-cards.pdf",
             "units/points-config.json", "units/points.py", "units/readiness.py",
             "playtest/dead-air-playtest-pack.pdf", "playtest/dead-air-s1.json", "playtest/dead-air-s2.json"]
SEARCH = []


def slug(value):
    return re.sub(r"[^\w]+", "-", value.lower()).strip("-")


def rewrite_link(href, source):
    if href == "C:/Users/wben7/Downloads/MWScenarioHandbookv21.pdf":
        return "https://www.warrenborn.com/Files/MWScenarioHandbookv21.pdf"
    # Turn Windows source paths into valid local-file links.
    if re.match(r"^[A-Za-z]:[/\\]", href):
        return Path(unquote(href)).as_uri()
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path:
        return href
    path = (source.parent / unquote(parts.path)).resolve()
    if path.parent == OUT.resolve():
        target = path.name
    elif path.parent == (ROOT / "scenarios/diagrams").resolve():
        target = "diagrams/" + path.name
    elif path in SOURCE_URL:
        target = SOURCE_URL[path]
    else:
        relative = path.relative_to(ROOT)
        target = "downloads/" + path.name
        if relative.as_posix() not in DOWNLOADS:
            target = "../" + relative.as_posix()
    return target + ("?" + parts.query if parts.query else "") + ("#" + parts.fragment if parts.fragment else "")


def render_document(source, output, title):
    tokens = MD.parse(source.read_text(encoding="utf-8"))
    # The template supplies the document title; keep every remaining source block.
    if tokens and tokens[0].type == "heading_open" and tokens[0].tag == "h1":
        tokens = tokens[3:]
    toc, ids = [], set()
    current = {"title": title, "page": title, "url": output, "text": ""}
    SEARCH.append(current)
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            text = tokens[i + 1].content
            anchor = slug(text)
            original, counter = anchor, 2
            while anchor in ids:
                anchor = f"{original}-{counter}"
                counter += 1
            ids.add(anchor)
            token.attrSet("id", anchor)
            toc.append((token.tag, text, anchor))
            current = {"title": text, "page": title, "url": output + "#" + anchor, "text": ""}
            SEARCH.append(current)
        if token.type == "inline":
            current["text"] += " " + token.content
        for child in token.children or []:
            if child.type == "link_open":
                child.attrSet("href", rewrite_link(child.attrGet("href"), source))
            elif child.type == "image":
                child.attrSet("src", rewrite_link(child.attrGet("src"), source))
    rendered = MD.renderer.render(tokens, MD.options, {})
    # Keyboard users can scroll wide tables without scrolling the whole page.
    rendered = rendered.replace("<table>", '<div class="table-scroll" tabindex="0" role="region" aria-label="Rules table"><table>')
    rendered = rendered.replace("</table>", "</table></div>")
    return rendered, toc


def nav_html(active):
    return "".join(f'<a href="{url}"' + (' aria-current="page"' if label == active else "")
                   + f'>{label}</a>' for label, url in NAV)


def contents_html(toc):
    if not toc:
        return '<p class="toc-note">Everything on this page is below.</p>'
    return '<ol class="contents">' + "".join(
        f'<li class="level-{level}"><a href="#{anchor}">{html.escape(label)}</a></li>'
        for level, label, anchor in toc) + "</ol>"


def resources_html(current):
    links = [("rules.html", "Core rules"), ("weapons.html", "Weapons"),
             ("equipment.html", "Equipment colors"), ("turn.html", "Turn reference"),
             ("readiness.html", "Readiness reference"),
             ("pilots.html", "Pilot cards"), ("units.html", "Unit cards"), ("builder.html", "Force builder"),
             ("points.html", "Points"), ("scenarios.html", "Scenarios")]
    return "".join(f'<a href="{url}"' + (' aria-current="page"' if url == current else "")
                   + f'>{label}<span aria-hidden="true">↗</span></a>' for url, label in links)


def write_page(filename, title, active, eyebrow, body, toc, tools="", next_page=None):
    template = (WEB / "shell.html").read_text(encoding="utf-8")
    next_html = ""
    if next_page:
        url, label = next_page
        next_html = f'<a class="next-page" href="{url}"><span>Continue reading<strong>{label}</strong></span><span aria-hidden="true">→</span></a>'
    replacements = {
        "TITLE": html.escape(title), "NAV": nav_html(active), "EYEBROW": html.escape(eyebrow),
        "BODY": body, "CONTENTS": contents_html(toc), "RESOURCES": resources_html(filename),
        "PAGE_TOOLS": tools, "NEXT": next_html,
    }
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    template = re.sub(r"(?m)^[ \t]+$", "", template)
    (OUT / filename).write_text(template, encoding="utf-8")


def resource_rows(items):
    return '<div class="resource-list">' + "".join(
        f'<a class="resource-row" href="{url}"><span class="resource-number">{num}</span>'
        f'<span><strong>{title}</strong><span class="resource-description">{desc}</span></span>'
        '<span class="resource-arrow" aria-hidden="true">↗</span></a>'
        for num, url, title, desc in items) + "</div>"


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "downloads").mkdir(exist_ok=True)
    for asset in ("site.css", "site.js", "diagrams.css"):
        shutil.copyfile(WEB / asset, OUT / asset)
    for path in DOWNLOADS:
        shutil.copyfile(ROOT / path, OUT / "downloads" / Path(path).name)
    (OUT / "diagrams").mkdir(exist_ok=True)
    for diagram in (ROOT / "scenarios/diagrams").glob("*.svg"):
        shutil.copyfile(diagram, OUT / "diagrams" / diagram.name)
    for source, filename, title, active, eyebrow in PAGES:
        body, toc = ("", []) if filename == "index.html" else render_document(ROOT / source, filename, title)
        tools, next_page = "", None
        if filename == "dead-air.html":
            body += '<link rel="stylesheet" href="diagrams.css">'
            tools = '<a class="small-button" href="downloads/dead-air-playtest-pack.pdf">Download playtest pack <span class="file-type">PDF</span></a>'
            next_page = ("first-contact.html", "First Contact rules and diagrams")
        elif filename == "first-contact.html":
            body += '<link rel="stylesheet" href="diagrams.css">'
            tools = '<a class="small-button" href="diagrams/first-contact-map.svg">Open setup map <span aria-hidden="true">↗</span></a>'
            next_page = ("starter-forces.html", "Choose a starter patrol")
        elif filename == "rules.html":
            tools = '<a class="small-button" href="turn.html">Quick reference <span aria-hidden="true">↗</span></a>'
            next_page = ("weapons.html", "Weapon types & tradeoffs")
        elif filename == "weapons.html":
            next_page = ("equipment.html", "Equipment colors")
        elif filename == "equipment.html":
            next_page = ("pilots.html", "Choose your pilots")
        elif filename == "pilots.html":
            tools = '<a class="small-button" href="downloads/revived-pilot-cards.pdf">Printable cards <span class="file-type">PDF</span></a>'
            next_page = ("first-contact.html", "Your first scenario")
            body += '<figure class="pilot-preview"><a href="downloads/revived-pilot-cards.pdf"><img src="downloads/revived-pilot-cards-preview.png" alt="Four printable Revived pilot cards: Gunner, Skirmisher, Brawler, and Engineer" loading="lazy" width="1224" height="1584"></a><figcaption>Four roles. Print the PDF at 100% on US Letter paper.</figcaption></figure>'
        elif filename == "index.html":
            body = '<p class="lead">A modernized take on MechWarrior: Dark Age.</p><p>Use your existing <strong>MW:DA clix figures and their combat dials</strong> with these fan-made rules. Command BattleMechs, armored vehicles, and infantry in the BattleTech universe, taking turns moving and fighting for ground.</p><p>New in v0.3: pushing and recovery, half-speed Advance, and one order per squad. <a href="combat-rhythm.html">See what changes on the table.</a></p>' + resource_rows([
                ("PACK", "dead-air.html", "Dead Air: The Fight for Kestrel Relay", "Two named patrols, photo cards, a map and a results sheet. Print and play."),
                ("START", "first-contact.html", "Play your first battle", "600 points · Two starter patrols · Setup map and teaching diagrams."),
                ("01", "rules.html", "Read the rules", "Learn how a battle unfolds, from movement and combat to victory."),
                ("02", "builder.html", "Build your force", "Choose models, check your list, and print cards for your army."),
                ("03", "units.html", "Find your units", "Photos, full dials, printable cards, and points."),
                ("04", "scenarios.html", "Choose your mission", "A starter battle and three full missions with deployment and scoring rules."),
                ("05", "aids.html", "Prepare the table", "Quick references and printable pilot cards."),
            ]) + '<div class="edition-note"><strong>Playtest edition</strong><p>The rules are ready to try. Balance at each size and the Standard game’s two-hour play target still need testing.</p></div>'
            SEARCH.append({"title": title, "page": title, "url": filename, "text": re.sub(r"<[^>]+>", " ", body)})
        write_page(filename, title, active, eyebrow, body, toc, tools, next_page)

    scenario_body = '<p class="lead">Choose a scenario.</p><p>Start with First Contact at 600 points. The other three missions support all four game sizes: use 48 × 48 inches for Skirmish or Standard, and the <a href="rules.html#set-up-a-larger-battlefield">72 × 48 setup</a> for Large or Grand Battles. Place terrain before choosing sides, then play again with roles or edges exchanged.</p>' + resource_rows([
        ("PACK", "dead-air.html", "Dead Air", "Themed First Contact pack · Two patrols · Assigned cards · Map · Results sheet"),
        ("START", "first-contact.html", "First Contact", "4 rounds · 600 points · One relay · Map, diagrams, and starter patrols"),
        ("01", "seize-and-hold.html", "Seize and Hold", "6 rounds · Three relay sites · Next step after First Contact"),
        ("02", "breakthrough.html", "Breakthrough", "8 rounds · Attacker versus defender · Escape through the north edge"),
        ("03", "hold-the-station.html", "Hold the Station", "6 rounds · Attacker versus defender · Capture both access sites"),
    ]) + '<p>Use the <a href="rules.html#10-objectives-and-victory">core rules</a> to check who controls each objective. The scenario tells you when to score and how to win.</p>'
    write_page("scenarios.html", "Scenarios", "Scenarios", "Mission selection", scenario_body, [])
    aids_body = '<p>References and printable cards for the table.</p>' + resource_rows([
        ("PACK", "dead-air.html", "Dead Air playtest pack", "Kestrel Watch versus Blackwire Recovery. Everything to prepare the starter matchup."),
        ("MAP", "first-contact.html#set-up-the-map", "Starter map & diagrams", "Measured 48 × 48 setup, movement, objective control, and pushing."),
        ("LIST", "builder.html", "Print cards or dials for your army", "Choose photo cards or compact dial sheets, with full tracks and assignments for every model."),
        ("01", "turn.html", "Turn reference", "Round sequence, actions, attacks, and heat."),
        ("NEW", "readiness.html", "Readiness reference", "Ready, Committed, Spent: recovery, pushing, and a roster tracker."),
        ("PDF", "downloads/readiness-reference.pdf", "Print the readiness sheet", "US Letter · One-page reference and reusable tracker"),
        ("02", "weapons.html", "Weapon reference", "Ballistic, Energy, and Rocket strengths and costs."),
        ("03", "equipment.html", "Equipment reference", "The new meanings of your printed combat colors."),
        ("04", "pilots.html", "Pilot cards", "Gunner, Skirmisher, Brawler, and Engineer."),
        ("PDF", "downloads/revived-pilot-cards.pdf", "Print the pilot cards", "US Letter · Four 2.5 × 3.5 inch cards · Print at 100%"),
        ("PDF", "downloads/revived-unit-cards.pdf", "Print the unit cards", "Complete combat and heat dials · Two photo cards per Letter page · Print at 100%"),
        ("CSV", "downloads/sample-forces.csv", "Sample force data", "Unit counts and costs for all three forces."),
        ("CSV", "downloads/adjustments.csv", "Points change log", "Record formula changes and test results."),
        ("LOG", "log.html", "Playtest log", "A printable record for your games and rules questions."),
    ])
    write_page("aids.html", "Game aids", "Game aids", "At the table", aids_body, [])
    for filename, title, body in [("scenarios.html", "Scenarios", scenario_body), ("aids.html", "Game aids", aids_body)]:
        SEARCH.append({"title": title, "page": title, "url": filename, "text": re.sub(r"<[^>]+>", " ", body)})
    extra_pages = build_catalog(OUT, write_page, SEARCH)
    extra_pages += build_force_builder(OUT, write_page, SEARCH)
    (OUT / "search-index.js").write_text("window.RULEBOOK_INDEX = " + json.dumps(SEARCH, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Built {len(PAGES) + 2 + extra_pages} pages and {len(SEARCH)} searchable sections in {OUT}")


if __name__ == "__main__":
    main()
