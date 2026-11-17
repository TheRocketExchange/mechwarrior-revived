"""Build the themed First Contact pack from the existing rosters, dials and prices."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "units"))
import generate_cards as cards
from force_org import validate_force

OUT = ROOT / "playtest"
BASE = "https://therocketexchange.github.io/mechwarrior-revived/"
THEME = json.loads((OUT / "dead-air.json").read_text(encoding="utf-8"))
SCENARIO = json.loads((ROOT / "scenarios/first-contact.json").read_text(encoding="utf-8"))
CATALOG = cards.CATALOG
INDEX = {u["id"]: u for u in CATALOG["units"]}
PILOTS = {p["role"]: p for p in json.loads((ROOT / "pilots/cards.json").read_text())["cards"]}
FORMULA = CATALOG["points_formula"]["version"]
INK, MUTED, TEAL, RUST = [colors.HexColor(c) for c in ("#263330", "#5a655e", "#255c68", "#9b4b30")]
PALE, LINE = colors.HexColor("#f0f2ed"), colors.HexColor("#c6cec5")


def snapshot():
    """A table-test pair identifies its actual rules, rosters and costs, not a date."""
    digest = hashlib.sha256()
    paths = list((ROOT / "rules").glob("*.md")) + [ROOT / "pilots/cards.json", ROOT / "scenarios/00-first-contact.md", ROOT / "scenarios/first-contact.json", OUT / "dead-air.json"]
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_text(encoding="utf-8").replace("\r\n", "\n").encode())
    ids = sorted({uid for force in SCENARIO["forces"] for group in force["groups"] for uid in group["members"]})
    digest.update(json.dumps([INDEX[uid] for uid in ids], sort_keys=True, ensure_ascii=False).encode())
    return digest.hexdigest()[:10]


SNAPSHOT = snapshot()
RESULTS = {f["id"]: validate_force(f, INDEX) for f in SCENARIO["forces"]}


def para(c, value, x, top, width=540, size=10, leading=14, color=INK):
    style = ParagraphStyle("body", fontName="Helvetica", fontSize=size, leading=leading, textColor=color)
    p = Paragraph(value, style)
    _, height = p.wrap(width, 720)
    assert top - height >= 38, ("Paragraph outside page", value[:70], top, height)
    p.drawOn(c, x, top-height)
    return top-height


def label(c, value, x, y, size=10, color=TEAL):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, cards.safe(value))


def page(c, title, subtitle):
    c.setFillColor(TEAL)
    c.rect(36, 746, 32, 5, fill=1, stroke=0)
    label(c, "MECHWARRIOR REVIVED / DEAD AIR", 78, 745, 9)
    label(c, title, 36, 711, 24, INK)
    para(c, subtitle, 36, 698, size=10, color=MUTED)
    c.setStrokeColor(LINE)
    c.line(36, 34, 576, 34)
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawString(36, 23, f"Pack {THEME['edition']} / Rules 0.3 / Points {FORMULA} / Snapshot {SNAPSHOT}")


def table(c, rows, top, widths, heights=None, font=9):
    style = ParagraphStyle("cell", fontName="Helvetica", fontSize=font, leading=font+3, textColor=INK)
    data = [[Paragraph(str(cell), style) for cell in row] for row in rows]
    t = Table(data, colWidths=widths, rowHeights=heights)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("LINEBELOW", (0, 0), (-1, -1), .35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    _, height = t.wrap(540, 720)
    assert top-height >= 38, ("Table outside page", top, height)
    t.drawOn(c, 36, top-height)
    return top-height


def note(c, title, body, top, color=TEAL):
    label(c, title, 36, top, 11, color)
    return para(c, body, 36, top-8, size=9.5, leading=13)-17


def mission_page(c):
    page(c, "DEAD AIR", THEME["subtitle"])
    label(c, THEME["dispatch"], 36, 664, 9, RUST)
    y = para(c, escape(THEME["briefing"]), 36, 647, size=12, leading=17)-23
    for fid in ("S1", "S2"):
        f = THEME["forces"][fid]
        y = note(c, f["name"], escape(f["briefing"]), y, colors.HexColor(f["color"]))
    y = note(c, "Mission", "Play <b>First Contact</b>: 48 x 48 inches, four rounds, one relay at (24, 24). At the end of rounds 2, 3 and 4, score 1 if a friendly base center is within 3 inches and no enemy center is. Both sides inside means no score. Shutdown 'Mechs and passengers do not count; Spent units do.", y)
    y = para(c, "Higher score after round 4 wins; equal scores are a draw. Kills do not score or break ties. There are only 3 points available between both players. A wipeout does not end the game; if neither army has units left, end early with scores so far.", 36, y+4, size=9.5, leading=13)-19
    y = note(c, "Before you deploy", "Bring 14 models or clearly labeled stand-ins, tape measures, terrain, an objective marker, activation/readiness markers, and three D6 per player (two white and one other color). Set combat and heat dials to Start; vehicles and squads begin Ready. Both forces are mixed-faction contract patrols. Callsigns and this story are original fiction; the model factions and rules are unchanged.", y)
    y = note(c, "Two games, one rules snapshot", "Keep this PDF for both games. First play either patrol from either edge. For the return game, keep your force, swap north/south, and reset all dials and markers. Save suggested rule or points changes until both games are finished. The matchup has not yet been tested on the table.", y)
    para(c, '<b>Print:</b> Letter, 100%, single-sided. Pages 1-6 briefing and references; 7-10 Watch cards; 11-14 Blackwire cards; 15 pilot cards; 16 results (print twice). Cards include a separate full dial and photo for every base.<br/><b>Full rules:</b> <link href="'+BASE+'rules.html" color="#255c68">Core rules</link> / <link href="'+BASE+'equipment.html" color="#255c68">Equipment</link> / <link href="'+BASE+'first-contact.html" color="#255c68">First Contact diagrams</link>. Keep these open; the field sheets are quick references.', 36, y+3, size=9, leading=12)
    c.showPage()


def map_page(c):
    page(c, "Kestrel Relay", "Setup guide / 48 x 48 inches / North is up / Not a table-sized play mat")
    x0, y0, scale = 117, 282, 7.875
    width = 48*scale
    c.setFillColor(colors.HexColor("#fafaf6")); c.rect(x0, y0, width, width, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#e1edf0")); c.rect(x0, y0, width, 8*scale, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#f2e6df")); c.rect(x0, y0+40*scale, width, 8*scale, fill=1, stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(.5)
    for n in range(0, 49, 6):
        c.line(x0+n*scale, y0, x0+n*scale, y0+width)
        c.line(x0, y0+n*scale, x0+width, y0+n*scale)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawCentredString(x0+n*scale, y0-13, str(n))
        c.drawRightString(x0-9, y0+n*scale-3, str(n))
    palette = {"woods": "#dce7cd", "rubble": "#ede2c9", "blocking": "#ccd3d3"}
    for t in SCENARIO["terrain"]:
        x, y, w, h = x0+t["x"]*scale, y0+t["y"]*scale, t["width"]*scale, t["depth"]*scale
        c.setFillColor(colors.HexColor(palette[t["kind"]])); c.setStrokeColor(MUTED)
        c.rect(x, y, w, h, fill=1, stroke=1)
        if t["kind"] == "blocking":
            c.line(x, y, x+w, y+h); c.line(x+w, y, x, y+h)
        elif t["kind"] == "woods":
            for dx in (9, w-10):
                p=c.beginPath(); p.moveTo(x+dx-4, y+9); p.lineTo(x+dx, y+17); p.lineTo(x+dx+4, y+9); p.close(); c.drawPath(p)
        else:
            c.setDash(2, 3); c.line(x+5, y+8, x+w-5, y+8); c.setDash()
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 12); c.drawCentredString(x+w/2, y+h/2-4, t["id"])
    c.setDash(4, 3); c.setStrokeColor(TEAL)
    for y in (8, 40): c.line(x0, y0+y*scale, x0+width, y0+y*scale)
    obj=SCENARIO["objective"]
    cx, cy = x0+obj["x"]*scale, y0+obj["y"]*scale
    c.setStrokeColor(RUST); c.circle(cx, cy, obj["radius"]*scale); c.setDash()
    c.setFillColor(RUST); c.circle(cx, cy, 3, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9); c.drawCentredString(cx, cy+34, "RELAY (24, 24)")
    c.setFont("Helvetica", 8); c.drawCentredString(cx, cy-37, "3-inch control radius")
    for value,y in (("NORTH / y 40-48",y0+44*scale),("SOUTH / y 0-8",y0+4*scale)):
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 10); c.drawCentredString(cx,y-3,value)
    rows=[["Feature", "Footprint in inches"]]
    rows += [[f"{t['id']} / {THEME['terrain_names'][t['id']]}", f"x {t['x']}-{t['x']+t['width']}, y {t['y']}-{t['y']+t['depth']}"] for t in SCENARIO["terrain"]]
    y=table(c, rows, 249, [315,225], font=8)
    para(c, "W = woods; R = rubble; B = blocking. Each grid square is 6 inches. The southwest corner is (0, 0). Everything outside these footprints is open. Use a small marker for the relay; it adds no cover or obstacle.<br/><b>Deploy:</b> Roll D6 each, reroll ties. Winner chooses an edge; the other player deploys a group first. Alternate groups, whole bases inside the zones. Keep C1's centers in a 4-inch chain. Infiltrate follows its normal rule if present; neither patrol has it.", 36, y-10, size=8.5, leading=11)
    c.showPage()


def roster_page(c):
    page(c, "The patrols", "600-point Skirmish / 7 models and 5 activation groups each / Mixed factions")
    y=661
    for force in SCENARIO["forces"]:
        fid=force["id"]; theme=THEME["forces"][fid]
        label(c, f"{theme['name']} / {RESULTS[fid]['total']} points", 36, y, 16, colors.HexColor(theme["color"]))
        rows=[["ID / Callsign", "Model / Catalog ID / Faction", "Bases", "Points", "Pilot"]]
        for g in force["groups"]:
            u=INDEX[g["members"][0]]; t=theme["groups"][g["id"]]
            rows.append([f"<b>{g['id']}</b> / {t['callsign']}", f"<b>{escape(u['name'])}</b> / {u['id']}<br/>{u['rank']} / {escape(u['faction'])}",len(g["members"]),sum(INDEX[uid]["cost"]["points"] for uid in g["members"]),g.get("pilot","-")])
        y=table(c,rows,y-13,[122,230,40,45,103],font=8.5)-31
    y=note(c, "Read the labels", "<b>Catalog ID</b> identifies the exact figure and dial. <b>Roster ID</b> identifies its place in this patrol. The three infantry bases are C1a, C1b and C1c: separate dials, one C1 activation. Callsigns and pilot names are flavor only; the printed pilot role supplies the ability.",y)
    para(c,"Points shown for C1 cover all three bases. Neither vehicle is a carrier, including Blackwire's APC. All infantry start on foot; there are no Rocket substitutes. Use clearly labeled stand-ins with these exact cards if you lack a model. Keep both rosters fixed for the first two games.",36,y+3,size=9.5,leading=13)
    c.showPage()


def round_page(c):
    page(c,"Field reference","Use the current dial / Read new values after damage / Full rules take precedence")
    y=para(c,"<b>Each round:</b> Clear only activation markers. Roll D6 each, reroll ties; winner chooses who acts first. Alternate one group at a time. Pass only if you have fewer unactivated groups, or none. Each group acts once. Keep heat and readiness between rounds; there is no round-end cooling.",36,664,size=9.5,leading=13)-12
    rows=[["Order", "Movement and attack", "'Mech heat"]]
    rows += [list(row) for row in [
        ("Fire","Stay still; ranged or close attack. May pivot for close.","+1"),
        ("Advance","Half speed, rounded up; one ranged attack.","+2"),
        ("Move","Full speed; no attack. Non-'Mechs recover.","+1"),
        ("Rush","Twice speed; no attack. Forbidden while Spent.","+1"),
        ("Assault","Infantry/'Mech: half speed; close attack.","+1"),
        ("Disengage","Take 1 unavoidable damage; half speed; no attack.","+1"),
        ("Hold / Vent","Stay still. Hold cools 1; Vent cools vent rating (min. 1).","Cool"),
        ("Repair / Bypass","Need the matching Attack color; see next page.","+1"),
        ("Death from Above","Jump Jets 'Mech; special close attack. See page 6.","+2 total"),
    ]]
    y=table(c,rows,y,[95,372,73],font=8)-15
    y=note(c,"Vehicles and infantry","Fire, Advance, Assault or Bypass: <b>Ready - Committed - Spent.</b> On the second combat order, each surviving base takes 1 unavoidable damage after its own action, even if it misses or skips its attack. Spent must recover next activation. Move or Hold clears readiness; engaged bases Hold or Disengage. Rush and Repair leave readiness unchanged and are forbidden while Spent. C1 chooses one order; resolve its bases separately, ending in a 4-inch chain. Split squads must regroup without attacking.",y)
    y=note(c,"Attacks","Check arc, sight and range. <b>Three dice + Attack + modifiers must reach Defense.</b> White 6/6 always hits, +1 damage. White 1/1 always misses and deals 1 unavoidable damage to the attacker. Rear: +2 Attack; shutdown target: -2 Defense. Equipment gives at most +1 Attack / +1 Defense. Fire can pivot for close combat while keeping the center and contacts; ranged Fire cannot turn. Vehicles need special equipment to fight close.",y)
    y=note(c,"Heat","Apply printed heat modifiers to speed and damage. Add action heat, +1 for an Energy shot and +1 for Jump. Pulse adds another +1 if a second shot is rolled. After each heat gain, roll one stress die if a non-green/white warning is showing and not shutdown; on 1, take 1 damage. Stop at shutdown: only Vent, no objective control. Engineer improves Vent by 1. Stop cooling at Start.",y)
    para(c,"<b>Terrain:</b> Woods/rubble cost 2 inches per inch traveled. Ranged cover: +3 infantry, +2 battle armor, +1 vehicles/'Mechs; no close bonus. Blocking terrain stops movement and direct sight. Keep the relay's control area open. Use the rules for terrain sight and friendly contact when checking shots.",36,y+3,size=9.5,leading=13)
    c.showPage()


def equipment_pages(c):
    page(c,"Equipment / Movement and support","Only abilities found on these patrols' full dials / Color must be showing now")
    y=para(c,"Read the background color in its own category. A colored Attack number is different from colored weapon damage. Abilities are optional except Salvage; passive protection still works during Salvage or shutdown. Shutdown blocks active abilities. Read the next attack from the new dial.",36,664,size=9.5,leading=13)-19
    notes=[
        ("Red Speed / Evade","+1 ranged defense. Disengage without damage. Equipment defense bonuses do not add above +1; terrain cover is separate."),
        ("Blue Speed / Jump Jets","May ignore bases and terrain along a Jump route, but must land with the whole base in legal space. No Rush, no landing in fieldworks for a 'Mech or vehicle. Use the action's normal movement allowance. A jumping 'Mech gains 1 extra heat; DFA already includes it. Jump Jets also waive Disengage damage when walking. Grapple overrides free Disengage if encountered in other games."),
        ("Blue Attack / Improved Targeting","+1 Attack for ranged or close attacks, including Bypass. Total equipment attack bonus cannot exceed +1."),
        ("Black Attack / Salvage","Only Move, Hold, Vent or Disengage; no attacks or active support. May still contest unless shutdown. A salvaged squad member skips an illegal shared order and stays still, but still takes pushing damage. Passive protection remains."),
        ("Green Attack / Repair","Stay still in friendly base contact; neither unit may touch an enemy. Restore 1 combat click, stopping at Start or a black repair mark. A mark already showing prevents repair. No self-repair, passengers, destroyed units or heat repair. Infantry repair only their own type; other core types repair battle armor, vehicles or 'Mechs. No roll. Non-'Mechs keep readiness and cannot Repair while Spent; a 'Mech gains 1 heat."),
        ("Red Attack / Bypass","Need positive printed Attack, but no damage value. Choose an empty enemy vehicle/'Mech in Salvage, or a shutdown 'Mech; it cannot touch another unit friendly to its owner. Move up to half speed into front-arc contact, or pivot in contact. Roll a normal close attack with rear, shutdown and defense modifiers. A hit captures instead of damaging; critical hits add nothing, critical misses still hurt the attacker. This is a combat order for readiness, or +1 'Mech heat, plus Jump if used."),
        ("After a capture","Keep the target's dial, heat, readiness and pilot; mark it already activated this round. From next round it is a separate group for its new controller. Existing contacts remain until Disengage. It can contest for its new owner. Starting roster limits do not change; First Contact has no casualty points."),
        ("Green Defense / Decoy; Gray Defense / Heavy Armor","Decoy gives +1 ranged defense in or out of cover. Heavy Armor reduces ranged and close damage by 1. Armor never reduces unavoidable damage. Ordinary Piercing ignores 1 armor; Armor Piercing equipment ignores all."),
    ]
    for title,body in notes: y=note(c,title,body,y)
    c.showPage()
    page(c,"Equipment / Weapons and close combat","Damage colors follow the printed weapon type, even during a close attack")
    y=664
    notes=[
        ("Ballistic and Energy","Ballistic shots gain +1 damage against uncovered infantry. Moving or turning gives -1 Attack recoil; Gunner waives it during Advance within half-speed movement cost. Energy shots have Piercing, add 1 heat to a firing 'Mech, and deal at most 2 damage to infantry before armor. These weapon effects apply only to shooting. There are no Rockets in these lists."),
        ("Red Ballistic damage / Armor Piercing","Ranged attacks with this weapon ignore all armor. It does not add close Piercing when the same damage value is used in contact."),
        ("Gray Ballistic damage / Point Defense System","A touching friendly unit may use the donor's printed Defense if higher, then apply its own equipment and modifiers. Do not borrow the donor's armor or a Defense value it borrowed from someone else. Passengers cannot provide or receive this benefit."),
        ("Red Energy damage / Pulse","After a ranged hit, may shoot the same surviving legal target once more with the same weapon at -2 Attack. Read both new dials; the attacker must survive and still show Pulse. No second shot on an initial miss, and no chain. Pay action and ordinary Energy heat once, plus 1 extra heat if the second roll is made. Resolve critical-miss damage after each roll."),
        ("Green Melee damage / Full Strike","With Fire or Assault, may attack every enemy touching your front arc with this weapon. Roll once; compare against each target separately. Resolve targets in your chosen order using the values/equipment read before the roll. Pay critical-miss damage only once. No other extra-attack effect and no DFA."),
        ("Death from Above / Hatchetmen only in this pack","Start unengaged, with blue Speed, no Salvage, positive speed and printed Attack, and positive primary damage after heat. Declare the target first: an enemy vehicle or 'Mech. Jump some distance, up to full current speed, into legal front-arc contact beside it, touching no other enemy. No fieldworks landing. One close attack: target gets +2 Defense; your primary damage gets +2, outside the equipment/pilot cap. Apply normal rear, shutdown, critical, close and armor rules; no ranged effects or Full Strike."),
        ("Pay for the landing","After resolving the target's effects, take 1 unavoidable damage on a hit (even zero damage), or 2 on a miss or skipped attack after jumping. Critical-miss damage is additional. If still alive, gain 2 heat total, including Jump. No second attack, displacement or target pivot."),
        ("Infantry and damage limits","Against vehicles/'Mechs, infantry deal at most 1 before armor. An exposed close assault raises this to 2 with Piercing: rear contact, a shutdown target, or an attacker in woods/rubble/fieldworks. Flat equipment and pilot damage bonuses together cap at +1. Critical and DFA bonuses are separate. Apply damage limits, then armor after Piercing. Three bullet holes destroy a model."),
    ]
    for title,body in notes: y=note(c,title,body,y)
    c.showPage()


def unit_pages():
    pdf=cards.PDF()
    for force in SCENARIO["forces"]:
        theme=THEME["forces"][force["id"]]
        models=[]
        for g in force["groups"]:
            for n,uid in enumerate(g["members"]):
                squad=g["id"] if len(g["members"])>1 else ""
                models.append((INDEX[uid],dict(theme["groups"][g["id"]],force_name=theme["name"],roster_id=g["id"]+(chr(97+n) if squad else ""),squad=squad,pilot=g.get("pilot",""))))
        for offset in range(0,len(models),2):
            commands,images=[],{}
            for (unit,assignment),(x,y) in zip(models[offset:offset+2],[(36,405),(36,27)]):
                cards.card(pdf,commands,images,unit,x,y,assignment)
            cards.text(commands,36,778,f"DEAD AIR / {theme['name'].upper()}",9,True,cards.RED)
            cards.text(commands,36,13,f"Print 100% / 7.5 x 5 in cards / Points {FORMULA} / Snapshot {SNAPSHOT}",7,color=cards.MUTED)
            if offset==6:
                cards.text(commands,48,359,"C1 / ONE SQUAD, THREE SEPARATE DIALS",12,True,cards.RED)
                for i,line in enumerate(["C1a, C1b and C1c activate together using one order.","Resolve each base separately, with its own target, dice and current dial.","Keep neighboring base centers within 4 inches in a single chain.","Track one readiness state for C1. A push damages each surviving base.","Use each card's Roster ID to match it to the labeled miniature."]):
                    cards.text(commands,48,333-i*20,line,10)
            pdf.page(commands,images)
    # Reuse the existing, fully audited card renderer; keep its intermediate PDF in memory.
    class Buffer:
        def write_bytes(self,value): self.data=value
    buffer=Buffer();pdf.save(buffer)
    return PdfReader(io.BytesIO(buffer.data))


def pilot_page(c):
    page(c,"The pilots","Cut on borders / One card for each assigned pilot / Names add no rules or cost")
    for col,force in enumerate(SCENARIO["forces"]):
        theme=THEME["forces"][force["id"]]; accent=colors.HexColor(theme["color"])
        for row,g in enumerate([g for g in force["groups"] if "pilot" in g]):
            t=theme["groups"][g["id"]]; p=PILOTS[g["pilot"]]
            x,y,w,h=36+col*276,480-row*204,264,190
            c.setStrokeColor(LINE);c.rect(x,y,w,h)
            c.setFillColor(accent);c.rect(x,y+h-30,w,30,fill=1,stroke=0)
            label(c,theme["name"].upper()+" / "+g["id"],x+12,y+h-19,9,colors.white)
            label(c,t["pilot_name"],x+12,y+141,15,INK)
            label(c,t["callsign"]+" / "+g["pilot"],x+12,y+124,10,accent)
            label(c,p["ability"],x+12,y+105,9,accent)
            bottom=para(c,escape(p["text"]),x+12,y+95,w-24,size=9.5,leading=12)
            assert bottom>=y+34,(g["pilot"],"pilot text too tall")
            para(c,escape(p["reminder"]),x+12,y+30,w-24,size=8,leading=10,color=MUTED)
    para(c,"Abilities affect only the assigned 'Mech. Engineer works during shutdown; other pilot abilities do not. If captured, a 'Mech keeps its pilot. Each patrol uses one Gunner, Brawler and Engineer.",36,58,size=7.5,leading=10)
    c.showPage()


def results_page(c):
    page(c,"After-action report","One sheet per game / Keep both reports / Write observations before proposing fixes")
    y=para(c,"Date: __________________  Game: 1 / Return  &nbsp;&nbsp; Total minutes: __________<br/>Watch player: ____________________  Edge: North / South<br/>Blackwire player: _________________  Edge: North / South",36,662,size=11,leading=18)-12
    rows=[["Round", "Minutes", "Watch score", "Blackwire score", "Relay: controlled / contested / empty"]]
    rows += [[str(n),"","No scoring" if n==1 else "","No scoring" if n==1 else "",""] for n in range(1,5)]
    rows += [["Total", "", "", "", "Winner / Draw:"]]
    y=table(c,rows,y,[46,58,85,95,256],heights=[28]+[20]*5,font=8.5)-17
    y=para(c,"<b>Orders:</b> Write the actual order each round (Fire, Advance, Move, Hold, etc.). Mark a push with P, a useful recovery move with *, and a destroyed group with X.",36,y,size=9,leading=12)-9
    y=table(c,[["Group", "Round 1", "Round 2", "Round 3", "Round 4"],*[ [name,"","","",""] for name in ("Watch V1","Watch C1","Blackwire V1","Blackwire C1")]],y,[140,100,100,100,100],heights=[22]*5,font=9)-20
    for prompt in [
        "A decision changed by heat, pushing, recovery or loss of equipment:",
        "Did infantry reach useful cover or the relay? What stopped or protected them?",
        "A unit / weapon / ability that felt too strong or weak (give its ID and what happened):",
        "A rule we reread or disputed, and the ruling we used:",
    ]:
        label(c,prompt,36,y,9,INK)
        for dy in (17,34): c.setStrokeColor(LINE);c.line(36,y-dy,576,y-dy)
        y-=55
    para(c,"Score only at the end of rounds 2-4: at most 3 points combined. Note setup time separately if useful. Keep the same models, pilots, rules and points for the return game; swap edges and reset all dials. Record any stand-ins or deviations on the back.",36,y+2,size=8,leading=11)
    c.showPage()


def write_web():
    lines=["# Dead Air", "", f"**{THEME['subtitle']}**", "", THEME["briefing"], "", "[Download the complete playtest pack](dead-air-playtest-pack.pdf) · 16 Letter pages · Print at 100%, single-sided", "", "## The two patrols", ""]
    for fid,label_ in (("S1","Patrol A"),("S2","Patrol B")):
        theme=THEME["forces"][fid]
        lines += [f"### {theme['name']}","",theme["briefing"],"",f"**{RESULTS[fid]['total']} points · 7 models · 5 activation groups.** Uses the existing {label_} roster, with callsigns and named pilots.","",f"[Load {label_} in the builder](../site/builder.html?sample={fid}) · [Download the themed list](dead-air-{fid.lower()}.json)",""]
        force=copy.deepcopy(next(f for f in SCENARIO["forces"] if f["id"]==fid))
        force.update(version=1,name=theme["name"],faction="",formula_version=FORMULA)
        (OUT/f"dead-air-{fid.lower()}.json").write_text(json.dumps(force,indent=2)+"\n",encoding="utf-8")
    lines += ["Both are mixed-faction contract patrols. Their actual model factions remain on the rosters and cards. The setting, callsigns and pilot names are original fan fiction; they add no rules or bonuses. Import a themed list in the builder to use its name, or load the matching starter patrol directly.","","## Inside the pack","", "| Pages | Contents |", "| --- | --- |", "| 1 | Mission briefing and how to run the two games |", "| 2 | Measured relay map, terrain key and deployment |", "| 3 | Both rosters, exact model IDs, factions and points |", "| 4–6 | Turn reference, equipment used by these patrols, and DFA |", "| 7–10 | Kestrel Watch: seven photo cards with full combat and heat dials |", "| 11–14 | Blackwire Recovery: seven photo cards with full combat and heat dials |", "| 15 | Six assigned pilot cards |", "| 16 | One-page results sheet; print two copies |","","## Set up and play","", "Use [First Contact](../scenarios/00-first-contact.md) exactly as written: a 48 × 48 inch table, four rounds, and a relay scored at the end of rounds 2, 3 and 4. Higher score wins; equal scores draw. Kills do not score. Either patrol can use either edge.","","[![First Contact setup map for the fight at Kestrel Relay.](../scenarios/diagrams/first-contact-map.svg)](../scenarios/diagrams/first-contact-map.svg)","","The printed pack gives the same terrain footprints local names: shelterbelts, ruined buildings and industrial blocks. The relay is a point marker, not a building. The map is a setup guide, not a table-sized play mat.","","Keep the [core rules](../rules/core-rules.md) and [equipment reference](../rules/equipment-reference.md) nearby. The PDF's field sheets are quick references. Infantry start on foot; neither vehicle is a carrier. Use clearly labeled stand-ins with the exact cards if needed.","","## Play the return game","", "Keep your force, swap north and south, and reset all dials and markers. Use the same PDF for both games. Record the score, time, vehicle and squad orders, decisions changed by heat or pushing, and rules that needed rereading. Save proposed rule and points changes until both games are finished.","", f"Pack {THEME['edition']} · Rules 0.3 · Points {FORMULA} · Snapshot `{SNAPSHOT}`. The snapshot identifies the rules and roster data used to build this copy. No tabletop results have been recorded for this matchup.",""]
    (OUT/"dead-air.md").write_text("\n".join(lines),encoding="utf-8")


def main():
    assert SCENARIO["board"]=={"width":48,"depth":48} and SCENARIO["rounds"]==4
    assert SCENARIO["scoring_rounds"]==[2,3,4]
    assert all(r["groups"]==5 and r["carriers"]==0 for r in RESULTS.values())
    assert abs(RESULTS["S1"]["total"]-RESULTS["S2"]["total"])<=12
    memory=io.BytesIO();c=canvas.Canvas(memory,pagesize=(612,792),invariant=1)
    mission_page(c);map_page(c);roster_page(c);round_page(c);equipment_pages(c)
    pilot_page(c);results_page(c);c.save()
    text_pages=PdfReader(memory)
    assert len(text_pages.pages)==8
    writer=PdfWriter()
    for p in text_pages.pages[:6]:writer.add_page(p)
    for p in unit_pages().pages:writer.add_page(p)
    for p in text_pages.pages[6:]:writer.add_page(p)
    assert len(writer.pages)==16
    for n,p in enumerate(writer.pages,1):
        overlay=io.BytesIO();stamp=canvas.Canvas(overlay,pagesize=(612,792),invariant=1)
        stamp.setFont("Helvetica",7);stamp.setFillColor(MUTED);stamp.drawRightString(575,8,f"DEAD AIR / {n} of 16");stamp.save()
        p.merge_page(PdfReader(overlay).pages[0])
    for title,index in [("Mission briefing",0),("Setup map",1),("The patrols",2),("Field reference",3),("Equipment",4),("Kestrel Watch cards",6),("Blackwire Recovery cards",10),("Pilot cards",14),("Results sheet",15)]:writer.add_outline_item(title=title,page_number=index)
    writer.add_metadata({"/Title":"Dead Air: The Fight for Kestrel Relay","/Author":"MechWarrior Revived","/Subject":f"Starter playtest pack / {FORMULA} / {SNAPSHOT}"})
    writer.write(OUT/"dead-air-playtest-pack.pdf")
    write_web()
    print(f"Dead Air: 16 pages, 14 full-dial unit cards, 6 pilot cards; snapshot {SNAPSHOT}.")


if __name__=="__main__":
    main()
