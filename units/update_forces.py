"""Generate legal sample rosters using the catalog's shared points formula."""
from collections import Counter
import csv
import json
from pathlib import Path

from force_org import DEFAULT_SIZE, GAME_SIZES, unit_family, validate_force

ROOT = Path(__file__).resolve().parent.parent


def group_cost(group, index):
    return (index[group["members"][0]]["rocket_options"][group["rocket_slot"]]["points"]
            if group.get("rocket_slot") else sum(index[key]["cost"]["points"] for key in group["members"]))


def row(values):
    return "| " + " | ".join(map(str, values)) + " |"


def main():
    catalog = json.loads((ROOT / "units/catalog.json").read_text(encoding="utf-8"))
    roster = json.loads((ROOT / "playtest/forces.json").read_text(encoding="utf-8"))
    index = {unit["id"]: unit for unit in catalog["units"]}
    forces = roster["forces"]
    assert roster["limit"] == GAME_SIZES[DEFAULT_SIZE]["points_limit"]
    assert all(force.get("game_size", DEFAULT_SIZE) == DEFAULT_SIZE for force in forces)
    results = {force["id"]: validate_force(force, index) for force in forces}
    totals = [result["total"] for result in results.values()]
    if max(totals) - min(totals) > roster["limit"] * 0.02:
        raise ValueError("Sample forces must stay within 2% of the common limit of one another")
    with (ROOT / "playtest/sample-forces.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["force", "group", "catalog_id", "unit_name", "family", "edition", "rank", "category", "quantity", "points_each", "formula_version", "pilot", "carrier", "passengers", "rocket_slot"])
        for force in forces:
            for group in force["groups"]:
                for key, quantity in Counter(group["members"]).items():
                    unit = index[key]
                    cost = unit["rocket_options"][group["rocket_slot"]] if group.get("rocket_slot") else unit["cost"]
                    writer.writerow([force["id"], group["id"], key, unit["name"], unit_family(unit), unit["set"], unit["rank"], unit["category"], quantity, cost["points"], cost["version"], group.get("pilot", ""), bool(group.get("carrier")), group.get("passengers", ""), group.get("rocket_slot", "")])
    summary = [row([force["id"], f"**{results[force['id']]['total']:,}**"] +
                   [results[force["id"]][key] for key in ("mechs", "vehicles", "conventional", "battle_armor", "squads", "groups")]) for force in forces]
    sections = []
    for force in forces:
        lines = [f"## {force['id']}: {force['name']}", "", "| Group | Unit and catalog ID | Bases | Points | Pilot / transport |", "| --- | --- | ---: | ---: | --- |"]
        for group in force["groups"]:
            members = Counter(group["members"])
            names = "; ".join((f"{count} × " if len(members) > 1 else "") + f"[{index[key]['name']} · {key}](../site/unit.html?id={key})" for key, count in members.items())
            notes = [group["pilot"]] if group.get("pilot") else []
            if group.get("carrier"):
                notes.append("Carrier" + ("; starts with " + group["passengers"] if group.get("passengers") else ""))
            if group.get("rocket_slot"):
                notes.append(group["rocket_slot"].capitalize() + " as Rocket")
            lines.append(row([group["id"], names, len(group["members"]), group_cost(group, index), "; ".join(notes) or "—"]))
        lines += ["", f"**{results[force['id']]['total']:,} points.** Breakthrough escape target: **{results[force['id']]['escape']} points**."]
        sections.append("\n".join(lines))
    text = f"""# Sample forces

Version {roster['version']} · Standard · {roster['limit']:,}-point limit · Formula {catalog['points_formula']['version']}

Three starting armies: **H** (’Mech-heavy), **B** (balanced), and **I** (infantry-heavy). Try H against B first. Their totals are close; their balance still needs testing.

Each follows the Standard [force organization and rule of three](../rules/core-rules.md#11-build-your-force): at most 8 ’Mechs, 6 vehicles, and 9 infantry squads. No unit type is required; a force can have zero ’Mechs. No chassis appears more than three times; no infantry family appears in more than three squads. All squads have 2–3 bases. For 600, 1,800, or 2,400 points, select that [game size](../rules/core-rules.md#choose-the-battle-size) in the [force builder](../site/builder.html) and build to its chart.

| Army | Points | ’Mechs | Vehicles | Infantry bases | Battle armor bases | Squads | Activation groups |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(summary)}

Use the exact catalog IDs in the rosters below. Each link shows the figure, rank, dial, and unit family. Every base costs the points given by the [shared formula](../rules/points.md); the points column below totals the whole group. Pilots are included, and carriers have no extra charge.

[Download the rosters and costs](sample-forces.csv).

## Before deployment

Use the group IDs below: M for ’Mechs, V for vehicles, C for infantry squads, and A for battle armor squads. Label individual squad members C1a, C1b, C1c, and so on. Each group takes one activation.

V1 starts with C1 aboard; V2 starts with A1. All other squads start on foot. Passengers still count as separate groups and are already paid for in the roster. Keep squad membership, pilots, and transport assignments for the return game.

{chr(10).join(chr(10) + section + chr(10) for section in sections)}

## What to try

- **H:** Use the eight ’Mechs to pressure several sites; protect the three infantry squads.
- **B:** Use vehicle fire and the two carried squads to take positions.
- **I:** Test whether nine infantry squads can hold ground with fewer ’Mechs, and whether the extra groups slow the game.

For example, H’s three Mongoose figures fill that chassis allowance. I’s nine Standard Foot bases form three squads, filling the Standard Foot allowance. It can also take three Hoverbike squads because they are a different infantry family.

You can substitute figures from your collection. Keep the intended army roles, check every force limit, and record each replacement’s catalog ID, points, pilot, weapons, and transport assignment. Recalculate totals and keep the armies within 2% under the same limit.

For a Rocket test, choose a substitute on one eligible ’Mech’s datasheet and use its updated cost. Recheck the army limit and Breakthrough target. Keep the same roster for the return game.
"""
    (ROOT / "playtest/sample-forces.md").write_text(text, encoding="utf-8")
    print("Sample forces:", "; ".join(f"{key} {result['total']} points, {result['groups']} groups, escape {result['escape']}" for key, result in results.items()))


if __name__ == "__main__":
    main()
