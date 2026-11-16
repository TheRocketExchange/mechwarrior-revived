"""Draw printable SVG teaching diagrams and a measured starter map."""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "diagrams"
INK, OLIVE, BLUE, RED = "#30382e", "#65704f", "#216887", "#9b4032"


def text(x, y, value, size=20, anchor="start", fill=INK, weight="normal"):
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">{escape(str(value))}</text>'


def rect(x, y, w, h, fill, stroke="#bdc4b3", extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" {extra}/>'


def line(x1, y1, x2, y2, color=OLIVE, width=2, extra=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" {extra}/>'


def circle(x, y, radius, fill="none", stroke=OLIVE, extra=""):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'


def save(name, title, description, body, width, height):
    defs = '''<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#65704f"/></marker>
<pattern id="woods" patternUnits="userSpaceOnUse" width="18" height="18"><rect width="18" height="18" fill="#dfe8d2"/><path d="M9 3L14 13H4Z" fill="none" stroke="#a0b18d"/></pattern>
<pattern id="rubble" patternUnits="userSpaceOnUse" width="18" height="18"><rect width="18" height="18" fill="#eee4cf"/><path d="M3 9L7 5L10 11ZM13 14L16 10" fill="none" stroke="#b5a88e"/></pattern>
<pattern id="blocking" patternUnits="userSpaceOnUse" width="12" height="12"><rect width="12" height="12" fill="#d8dcd7"/><path d="M-3 3L3 -3M0 12L12 0M9 15L15 9" stroke="#a0aaa2"/></pattern>
</defs>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
{defs}<g font-family="Arial, Helvetica, sans-serif">{rect(0,0,width,height,'#faf9f4',stroke='none')}{''.join(body)}</g></svg>\n'''
    (OUT / name).write_text(svg, encoding="utf-8")


def map_diagram():
    data = json.loads((ROOT / "first-contact.json").read_text(encoding="utf-8"))
    scale, left, top = 11.5, 84, 104
    x = lambda value: left + value * scale
    y = lambda value: top + (48-value) * scale
    body = [text(36,42,"FIRST CONTACT",28,weight="bold"), text(36,72,"48 × 48 inches · each square = 6 inches",20)]
    body.append(rect(left,top,552,552,"#f5f3e9",OLIVE))
    for name, (low, high) in data["deployment"].items():
        body.append(rect(left,y(high),552,(high-low)*scale,"#dce9ee" if name=="south" else "#eee0d9",stroke="none",extra=f'data-zone="{name}"'))
    for value in range(0,49,6):
        body += [line(x(value),top,x(value),top+552,"#d0d4c8",1), line(left,y(value),left+552,y(value),"#d0d4c8",1),
                 text(x(value),top+580,value,18,"middle"), text(left-15,y(value)+6,value,18,"end")]
    body += [line(left,y(8),left+552,y(8),BLUE,2,extra='stroke-dasharray="8 5"'),
             line(left,y(40),left+552,y(40),RED,2,extra='stroke-dasharray="8 5"'),
             text(x(24),y(44)+7,"NORTH DEPLOYMENT · y 40–48",21,"middle",RED,"bold"),
             text(x(24),y(4)+7,"SOUTH DEPLOYMENT · y 0–8",21,"middle",BLUE,"bold")]
    for feature in data["terrain"]:
        px, py = x(feature["x"]), y(feature["y"]+feature["depth"])
        body.append(rect(px,py,feature["width"]*scale,feature["depth"]*scale,f"url(#{feature['kind']})",OLIVE,extra=f'data-terrain="{feature["id"]}"'))
        cx, cy = px+feature["width"]*scale/2, py+feature["depth"]*scale/2
        body += [rect(cx-21,cy-15,42,30,"#faf9f4",stroke="none"),text(cx,cy+7,feature["id"],22,"middle",weight="bold")]
    objective = data["objective"]
    cx, cy = x(objective["x"]), y(objective["y"])
    body += [circle(cx,cy,objective["radius"]*scale,stroke=RED,extra='stroke-width="2" stroke-dasharray="5 4" data-control-radius="3"'),
             circle(cx,cy,5,RED,RED), text(cx,cy-46,"RELAY (24, 24)",19,"middle",RED,"bold"),
             text(cx,cy+58,"3-inch radius",18,"middle",RED)]
    body += [text(360,714,"x → east   ·   y ↑ north",19,"middle"),
             text(84,752,"W = woods",20),text(275,752,"R = rubble",20),text(460,752,"B = blocking",20),
             text(360,788,"Keep whole bases inside deployment zones.",19,"middle")]
    save("first-contact-map.svg","First Contact battlefield map","North is up. Coordinates are inches from the southwest corner. The 600-point starter uses the measured terrain and zones listed in the scenario.",body,720,816)


def movement():
    body = [text(28,38,"MOVEMENT & SHOOTING",26,weight="bold"),text(28,66,"Speed 8 · no heat or equipment modifiers",20)]
    for action, distance, note, yy in [("Advance",4,"1 ranged attack",128),("Move",8,"No attack",225),("Rush",16,"No attack",322)]:
        end = 200 + distance*25
        body += [text(28,yy-5,action,25,weight="bold"),text(28,yy+23,note,18),
                 circle(200,yy,7,BLUE,BLUE),line(211,yy,end,yy,OLIVE,4,'marker-end="url(#arrow)"'),
                 text(end+12,yy+7,f'{distance}″',22)]
    body += [line(200,375,600,375,"#adb5a1",1)]
    for value in (0,4,8,12,16):
        body += [line(200+value*25,370,200+value*25,380,"#adb5a1",1),text(200+value*25,403,value,18,"middle")]
    body += [text(28,403,"Inches traveled",18)]
    save("movement-and-fire.svg","Movement choices at speed eight","Advance up to four inches and make one ranged attack. Move up to eight with no attack. Rush up to sixteen with no attack. Arrows share one distance scale.",body,700,430)


def objective_control():
    body = [text(28,38,"WHO CONTROLS THE RELAY?",26,weight="bold")]
    for cx, label, enemy_x in [(175,"CONTROLLED",290),(525,"CONTESTED",565)]:
        body += [text(cx,80,label,23,"middle",OLIVE if label=="CONTROLLED" else RED,"bold"),
                 circle(cx,180,82,"#f0f1e7",OLIVE,'stroke-dasharray="6 4" stroke-width="2"'),
                 circle(cx,180,4,INK,INK),line(cx,180,cx,98,OLIVE,1),text(cx+10,135,'3″',18),
                 circle(cx-40,180,14,BLUE,BLUE),text(cx-40,186,"A",18,"middle","white","bold"),
                 circle(enemy_x,180,14,RED,RED),text(enemy_x,186,"B",18,"middle","white","bold"),
                 text(cx,300,"A scores 1" if label=="CONTROLLED" else "Neither side scores",22,"middle",weight="bold")]
    body += [text(350,342,"A = your base · B = enemy base",20,"middle"),text(350,374,"Compare centers with the 3-inch ring at scoring time.",20,"middle")]
    save("objective-control.svg","Control and contest examples","Left: side A has a center inside the ring and side B is outside, so A scores. Right: both centers are inside, so the objective is contested. Base centers decide control.",body,700,400)


def readiness():
    body = [text(28,38,"PUSHING & RECOVERY",26,weight="bold")]
    for xx, action, before, after, note, detail in [(20,"1 · Fire","Ready","Committed","No pushing damage",""),(250,"2 · Fire","Committed","Spent","1 damage per base","after its action"),(480,"3 · Move / Hold","Spent","Ready","Recover; no attack","")]:
        body += [rect(xx,72,200,216,"#eeefe5"), text(xx+100,108,action,22,"middle",weight="bold"),
                 text(xx+100,151,before,21,"middle"),line(xx+100,164,xx+100,188,OLIVE,2,'marker-end="url(#arrow)"'),
                 text(xx+100,218,after,23,"middle",RED if after=="Spent" else OLIVE,"bold"),
                 text(xx+100,253,note,17,"middle"),text(xx+100,276,detail,17,"middle")]
    body += [text(350,330,"One vehicle or squad · one activation per step",20,"middle"),
             text(350,364,"Recover early from Committed to avoid pushing.",20,"middle")]
    save("pushing-and-recovery.svg","Three activation readiness example","First Fire changes Ready to Committed. A second Fire changes Committed to Spent and each surviving base pays one pushing damage after its action. Move or Hold recovers to Ready. Mechs use heat instead.",body,700,390)


def main():
    OUT.mkdir(exist_ok=True)
    map_diagram()
    movement()
    objective_control()
    readiness()
    print("Generated the measured First Contact map and three teaching diagrams.")


if __name__ == "__main__":
    main()
