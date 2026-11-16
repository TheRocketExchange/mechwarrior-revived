"""Build sample rosters from catalog costs, never a second pricing table."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    catalog = json.loads((ROOT / "units/catalog.json").read_text(encoding="utf-8"))
    roster = json.loads((ROOT / "playtest/forces.json").read_text(encoding="utf-8"))
    index = {unit["id"]: unit for unit in catalog["units"]}
    units = [index[unit_id] for unit_id in roster["units"]]
    forces = roster["forces"]
    for force in forces:
        force["total"] = sum(count * unit["cost"]["points"] for count, unit in zip(force["counts"], units))
        force["groups"] = sum(force["counts"][:2]) + len(force["battle_armor_squads"]) + len(force["conventional_squads"])
        force["escape"] = math.ceil(force["total"] * 0.3)
        assert sum(force["battle_armor_squads"]) == force["counts"][2]
        assert sum(force["conventional_squads"]) == force["counts"][3]
        assert all(size in (2, 3) for size in force["battle_armor_squads"] + force["conventional_squads"])
        assert force["total"] <= roster["limit"], "Rebalance counts after changing the formula"
        assert 4 <= force["counts"][0] <= 8
    assert max(f["total"] for f in forces) - min(f["total"] for f in forces) <= roster["limit"] * 0.02
    with (ROOT / "playtest/sample-forces.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["force", "catalog_id", "unit_name", "edition", "rank", "category", "quantity", "revived_points_each", "printed_points_each", "formula_version", "squad_sizes", "carrier_count"])
        for force in forces:
            for i, unit in enumerate(units):
                squads = force["battle_armor_squads"] if i == 2 else force["conventional_squads"] if i == 3 else []
                writer.writerow([force["id"], unit["id"], unit["name"], unit["set"], unit["rank"], unit["category"], force["counts"][i], unit["cost"]["points"], unit["printed_points"], unit["cost"]["version"], "+".join(map(str,squads)), 2 if i == 1 else 0])
    def row(label, values):
        return "| " + label + " | " + " | ".join(map(str, values)) + " |"
    rows = []
    for i, unit in enumerate(units):
        rows.append(row(f"[{unit['name']} · {unit['id']}](../site/unit.html?id={unit['id']})", [f["counts"][i] for f in forces] + [unit["cost"]["points"], unit["printed_points"]]))
    rows.append(row("**Total Revived points**", [f"**{f['total']:,}**" for f in forces] + ["", ""]))
    rows.append(row("’Mechs / vehicles / infantry", [" / ".join(map(str, f["counts"][:2]+[sum(f["counts"][2:])])) for f in forces] + ["", ""]))
    rows.append(row("**Activation groups**", [f["groups"] for f in forces] + ["", ""]))
    squad_rows = [row(f["id"], [" + ".join(map(str,f["conventional_squads"])), " + ".join(map(str,f["battle_armor_squads"])), "V1: C1. V2: A1"]) for f in forces]
    targets = ", ".join(f"{f['id']}: {f['escape']}" for f in forces)
    text = f"""# Sample forces

Version {roster['version']} · {roster['limit']:,}-point limit · Formula {catalog['points_formula']['version']}

Three starting armies: **H** (’Mech-heavy), **B** (balanced), and **I** (infantry-heavy). Try H against B first. Their totals are close; their balance still needs testing.

Use the exact catalog IDs below. Each link shows the figure, rank, dial, and cost. Revived points come from the [shared formula](../rules/points.md); printed costs are a reference only.

| Unit | H | B | I | Revived points each | Original cost |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

[Download the counts and costs](sample-forces.csv). Pilots are included in ’Mech costs. Each army may designate two carriers without another charge.

## Before deployment

Number ’Mechs M1 onward and vehicles V1 onward. Make V1 and V2 the carriers. Number conventional squads C1 onward and battle armor squads A1 onward. The numbers below are bases in each squad.

| Army | Conventional squads | Battle armor squads | Starting passengers |
| --- | --- | --- | --- |
{chr(10).join(squad_rows)}

Give squad members IDs such as C1a, C1b, and C1c. Other squads start on foot. Passengers still count as activation groups.

Assign pilots in this order: **Gunner, Skirmisher, Brawler, Engineer**, then repeat. Keep assignments for the return game.

Use the weapon labels on each datasheet. For a Rocket test, choose a substitute on the first eligible ’Mech’s datasheet and record its alternate cost. Recalculate the army total and escape target; adjust counts if needed. Keep the same roster for the return game.

## What to try

- **H:** Pressure several sites with ’Mechs and commit the few infantry squads carefully.
- **B:** Use vehicle fire and the two carried squads to take positions.
- **I:** Test whether more infantry can hold ground with fewer ’Mechs, and whether {len(forces[2]['battle_armor_squads']) + len(forces[2]['conventional_squads'])} squads slow the game.

Repeated chassis help compare army composition. You do not need to buy these figures: substitute from your collection, keeping unit counts, infantry types, and squads as close as possible.

Record each replacement’s catalog ID, Revived points, pilot, weapons, and transport assignment. Recalculate totals and keep them within 2% under the same limit. If necessary, agree on a new limit and note the difference.

After the first tests, try a return-game pair with mixed light and heavy ’Mechs and different heat tracks.

For these exact armies, Breakthrough escape targets are **{targets} points**.
"""
    (ROOT / "playtest/sample-forces.md").write_text(text, encoding="utf-8")
    print("Sample forces:", "; ".join(f"{f['id']} {f['total']} points, {f['groups']} groups, escape {f['escape']}" for f in forces))


if __name__ == "__main__":
    main()
