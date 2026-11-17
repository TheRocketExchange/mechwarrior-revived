"""Check the deliverable PDF and builder imports against the live roster data."""
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "units"))
from force_org import validate_force


def main():
    catalog=json.loads((ROOT/"units/catalog.json").read_text(encoding="utf-8"))
    units={u["id"]:u for u in catalog["units"]}
    scenario=json.loads((ROOT/"scenarios/first-contact.json").read_text(encoding="utf-8"))
    theme=json.loads((ROOT/"playtest/dead-air.json").read_text(encoding="utf-8"))
    pdf=PdfReader(ROOT/"playtest/dead-air-playtest-pack.pdf")
    assert len(pdf.pages)==16
    assert all(tuple(p.mediabox)==(0,0,612,792) for p in pdf.pages)
    for n,p in enumerate(pdf.pages,1):assert f"{n} of 16" in p.extract_text()
    all_text="\n".join(p.extract_text() for p in pdf.pages)
    assert catalog["points_formula"]["version"] in all_text
    assert "After-action report" in pdf.pages[15].extract_text()
    assert "Kestrel Relay" in pdf.pages[1].extract_text()
    assert len(re.findall(r"Snapshot [0-9a-f]{10}",all_text))==16
    compact=lambda s:re.sub(r"\s+","",s).replace("\u2019","'")
    codes={"white":"","red":"R","blue":"B","green":"Gn","gray":"Gy","black":"K","purple":"P","yellow":"Y"}
    def cell(value,heat=False):
        if value.get("shutdown"):return "SD"
        if value.get("dead"):return "X"
        v=value.get("value")
        if v is None:return "-"
        return (f"{v:+d}" if heat and v else str(v))+codes[value.get("color","white")]
    for army,force in enumerate(scenario["forces"]):
        fid=force["id"]; t=theme["forces"][fid]
        imported=json.loads((ROOT/f"playtest/dead-air-{fid.lower()}.json").read_text(encoding="utf-8"))
        assert imported["groups"]==force["groups"] and imported["faction"]=="" and imported["name"]==t["name"]
        result=validate_force(imported,units)
        assert f"{result['total']} points" in pdf.pages[2].extract_text()
        expected=[]
        for group in force["groups"]:
            for i,uid in enumerate(group["members"]):
                expected.append((uid,group,group["id"]+(chr(97+i) if len(group["members"])>1 else "")))
        actual=[]
        for p in pdf.pages[6+army*4:10+army*4]:
            blocks=p.extract_text().split("Catalog ID: ")[1:]
            assert len(re.findall(rb"\bDo\b",p.get_contents().get_data()))==len(blocks),"One real photo per card"
            actual.extend(blocks)
        assert len(actual)==len(expected)==7
        for block,(uid,g,roster_id) in zip(actual,expected):
            u=units[uid]; s=compact(block)
            assert block.split()[0]==uid
            for value in [t["name"],"Faction: "+u["faction"],"Roster ID: "+roster_id,t["groups"][g["id"]]["callsign"]]:assert compact(value) in s,(uid,value)
            assert re.search(r"\b"+str(u["cost"]["points"])+r"\s+POINTS",block),uid
            if g.get("pilot"):
                assert compact("Pilot: "+t["groups"][g["id"]]["pilot_name"]+" / "+g["pilot"]) in s
            elif len(g["members"])>1:assert "Squad:C1Assignedcarrier:None" in s
            else:assert "Carrier:NoAssignedsquad:None" in s
            combat=s.split("COMBATDIAL",1)[1].split("HEATDIAL",1)[0]
            for key,label in [(w["slot"],w["slot"].title()+"dmg") for w in u["weapons"]]+[("speed","Speed"),("attack","Attack"),("defense","Defense")]:
                assert label+"".join(cell(click.get(key,{})) for click in u["track"])+"X" in combat,(uid,key)
            if u["heat"]:
                heat=s.split("HEATDIAL",1)[1]
                for key,label in [("primary","Primarydmg"),("secondary","Secondarydmg"),("speed","Speed")]:
                    if any(key in click for click in u["heat"]):assert label+"".join(cell(click.get(key,{}),True) for click in u["heat"]) in heat,(uid,key)
        pilots=pdf.pages[14].extract_text()
        for g in force["groups"]:
            if g.get("pilot"):assert t["groups"][g["id"]]["pilot_name"] in pilots
    printed_pilots=compact(pdf.pages[14].extract_text())
    for p in json.loads((ROOT/"pilots/cards.json").read_text())["cards"]:
        if p["role"]!="Skirmisher":assert printed_pilots.count(compact(p["text"]))==2
    for filename in ("dead-air-playtest-pack.pdf","dead-air-s1.json","dead-air-s2.json"):
        assert (ROOT/"playtest"/filename).read_bytes()==(ROOT/"site/downloads"/filename).read_bytes()
    print("Dead Air: 16 pages; 14 photos, full dials and assignments; 6 pilot cards; 2 legal roster imports; published copies verified.")


if __name__=="__main__":main()
