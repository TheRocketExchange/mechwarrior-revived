# Points

Version 0.2 · Formula 0.2-alpha-1

Build armies with the **Revived points** shown in the [unit catalog](../site/units.html). Pay per base, including every member of a squad. The old printed cost is shown only for reference.

Every unit uses the same formula. There are no hand-set prices, faction discounts, or rarity premiums. These are starting costs for playtesting, not established balance.

## The formula

**Points = 1.6 × Toughness × (1 + Mobility + 3 × Firepower + Support) + Pilot allowance**

Round the final result to the nearest whole point, with a minimum of 1. The calculation uses the full live combat dial from its starting mark onward, not just its best click.

| Part | What it measures |
| --- | --- |
| Toughness | How much incoming fire the damage track can withstand, using defense, armor, and cover |
| Mobility | Average speed, with small bonuses for Jump, easier terrain, hover movement, and safe disengagement |
| Firepower | Expected damage, using attack, weapons, range, arcs, equipment, infantry limits, and heat |
| Support | Repair and equipment that heats a target |
| Pilot allowance | 6 points already included in each ’Mech’s cost; no extra charge for choosing its Revived pilot |

Each datasheet has a “How the points are calculated” section with its ratings and total.

## How the ratings work

**Toughness** adds the value of every live click. Each is compared with a defense-18 target under an attack-8, damage-3 hit. The test mix is 80% ranged attacks, split equally among B/E/R, and 20% close attacks. Half arrive in the open and half in woods. Revived equipment and infantry cover apply.

**Mobility** adds 0.08 per inch of average speed. Jump adds 0.25 while shown; green speed adds 0.15; gray speed adds 0.10; red or blue speed adds 0.08. Hover adds 0.05. These are small allowances for terrain and movement choices, not extra inches during play.

**Firepower** checks all 216 dice results, including white-dice criticals. Its target mix is 40% armored vehicles, 20% unarmored ’Mechs, 10% open conventional infantry, 15% covered conventional infantry, and 15% battle armor. It weighs stationary fire at 65% and moving fire at 35%. Recoil, Energy heat, Rocket restrictions, damage limits, and Piercing all apply.

Range adds 0.025 per maximum-range inch and subtracts 0.025 per minimum-range inch. Wider arcs get a small bonus. Indirect access adds 15% of its expected damage. Close attacks use a 0.4 reach allowance, split between frontal and rear attacks. The best attack counts fully; a different second choice adds 15%, since it offers a choice rather than another attack.

For ’Mechs, a 24-action Fire/Vent or Advance/Vent calculation uses the actual heat track and vent rating. Heat damage modifiers and a small stress allowance reduce output. **Support** adds 0.35 for gray attack and 0.15 for yellow damage, averaged across the dial.

## Special cases

- A Rocket test substitute uses the alternate cost on its datasheet. Record that cost before deployment and keep it for the return game.
- Up to two carriers remain a shared army allowance. Designation adds no separate charge in this version.
- Aircraft, artillery-only units, DropShip turrets, and other excluded types still get catalog costs. Those estimates use the same model, but do not make them legal in a core game. Special flight, artillery, and DropShip rules are not priced here.
- Repair stops, exact base size, heat-related movement loss, mission layouts, and pilot combinations are not fully modeled. Test these before treating the costs as settled.

## Changing costs

The calculator is [units/points.py](../units/points.py); all tuning weights are in [points-config.json](../units/points-config.json). Change the formula version when changing weights, then rebuild the catalog, cards, and sample armies together. Keep one formula version for both games in a test pair.

Record reasons for changes in the [adjustment log](../playtest/adjustments.csv). Prefer a shared formula correction over a special price for one unit.
