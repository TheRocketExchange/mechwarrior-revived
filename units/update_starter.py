"""Generate starter rosters from catalog costs; no separate price list."""
import json
from pathlib import Path
from force_org import GAME_SIZES, validate_force
from update_forces import group_cost, row

ROOT = Path(__file__).resolve().parent.parent


def main():
    scenario = json.loads((ROOT / "scenarios/first-contact.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "units/catalog.json").read_text(encoding="utf-8"))
    index = {u["id"]: u for u in catalog["units"]}
    totals = []
    sections = []
    for force in scenario["forces"]:
        result = validate_force(force, index)
        totals.append(result["total"])
        assert result["groups"] == 5 and sum(len(g["members"]) for g in force["groups"]) == 7
        assert result["carriers"] == 0
        label = "Patrol A" if force["id"] == "S1" else "Patrol B"
        lines = [f"## {label}", "", f"**{result['total']} points · 7 models · 5 activation groups.**", "",
                 f"[Load {label} in the builder](../site/builder.html?sample={force['id']}) to print its unit cards or change models.", "",
                 "| Roster ID | Model and catalog ID | Bases | Points | Pilot |",
                 "| --- | --- | ---: | ---: | --- |"]
        for group in force["groups"]:
            unit = index[group["members"][0]]
            lines.append(row([group["id"], f"[{unit['name']} · {unit['id']}](../site/unit.html?id={unit['id']}) · {unit['rank']}", len(group["members"]), group_cost(group, index), group.get("pilot", "—")]))
        sections.append("\n".join(lines))
    assert max(totals)-min(totals) <= GAME_SIZES["skirmish"]["points_limit"]*.02
    text = f"""# Starter patrols

For [First Contact](../scenarios/00-first-contact.md) · Skirmish, 600-point limit · Formula {catalog['points_formula']['version']}

Each patrol has three ’Mechs, one vehicle, and one three-base infantry squad. Each has five activation groups: M1, M2, M3, V1, and C1. Label the infantry C1a, C1b, and C1c; they keep separate dials but share an order.

Choose one patrol each. Both may deploy on either side. Their totals are close, but their matchup has not been tested on the table.

{chr(10).join(chr(10) + section + chr(10) for section in sections)}

Neither vehicle is designated as a carrier, including the APC in Patrol B. Infantry start on foot. These lists use no Rocket substitutes. Use normal equipment, pilots, heat, and readiness.

The catalog IDs specify the exact ranks and dials. If you lack a listed figure, use another legal 600-point Skirmish list, or agree to use clearly labeled stand-ins with these cards. Keep the armies within 12 points of each other when testing this matchup. Costs come from the shared formula and update on rebuild.

To print: load the patrol, choose **Generate unit cards**, then **Print / Save as PDF**. Existing saved models are replaced only after you accept the builder’s prompt; export your list first to keep it.
"""
    (ROOT / "playtest/starter-forces.md").write_text(text, encoding="utf-8")
    print(f"Starter patrols: {totals[0]} and {totals[1]} points; five groups each.")


if __name__ == "__main__":
    main()
