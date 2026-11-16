# Points

Version 0.3 · Formula 0.3-alpha-2

Build armies with the **points** shown in the [unit catalog](../site/units.html). Pay per base, including every member of a squad.

Every unit uses the same formula. There are no hand-set prices, faction discounts, or rarity premiums. These are starting costs for playtesting, not established balance.

## Why the whole dial matters

A strong starting click costs more, but it does not tell the whole story. A unit that keeps fighting well after several hits costs more than one that quickly loses its best weapons, armor, or speed.

The formula prices **each click as a complete profile**, from Start to the last click before destruction. Its defense protects the weapons and movement on that same click. This avoids letting tough but weak late clicks inflate the value of powerful early weapons.

Earlier clicks count more because their strengths are available sooner. The weight falls evenly from **1.5 at Start to 0.5 at the last click**. For a six-click dial, the weights are 1.5, 1.3, 1.1, 0.9, 0.7, and 0.5. No click is ignored, and the weights average 1. A one-click dial uses 1.

Here are three otherwise identical six-click vehicles. All have speed 6, attack 8, defense 18, and a single Ballistic weapon with a 0–12-inch range and a 180° arc. They have no colored equipment. Only the damage values change:

| Damage from Start to the last click | Pattern | Points |
| --- | --- | ---: |
| 3, 3, 3, 3, 3, 3 | Holds its strength | 59 |
| 3, 3, 2, 2, 1, 1 | Gradual decline | 45 |
| 3, 1, 1, 1, 1, 1 | Sharp early drop | 36 |

Order also matters. A damage track of **3, 3, 1, 1, 1, 1** costs **41 points**; **3, 1, 1, 1, 1, 3** costs **38**. They have the same starting damage and average, but the first keeps its strength through the next hit. These are pricing examples, not additional catalog units.

## The formula

**Each click contributes: 1.6 × Click weight × Toughness × (1 + Mobility + 3 × Firepower + Support)**

Add every click’s contribution, then add the pilot allowance. Round once to the nearest whole point, with a minimum of 1. All ratings below are calculated on that click.

| Part | What it measures |
| --- | --- |
| Toughness | Resistance to incoming damage, using that click’s defense, armor, and cover |
| Mobility | Speed, with small bonuses for Jump, easier terrain, hover movement, and safe disengagement |
| Firepower | Expected damage, using attack, weapons, range, arcs, equipment, infantry limits, heat, and readiness |
| Support | Repair and equipment that heats a target |
| Pilot allowance | 6 points already included in each ’Mech’s cost; no extra charge for choosing its Revived pilot |

Each datasheet has a “How the points are calculated” section with a profile-value chart, each click’s contribution, and the total. Profile value is a pricing estimate, not another stat used during play. Choosing a later click on the datasheet does not change the model’s purchase cost.

## How the ratings work

**Toughness** compares a click with a defense-18 target under an attack-8, damage-3 hit. The test mix is 80% ranged attacks, split equally among B/E/R, and 20% close attacks. Half arrive in the open and half in woods. Revived equipment and infantry cover apply.

**Mobility** adds 0.08 per inch of speed. Jump adds 0.25 while shown; green speed adds 0.15; gray speed adds 0.10; red or blue speed adds 0.08. Hover adds 0.05. These are small allowances for terrain and movement choices, not extra inches during play.

**Firepower** checks all 216 dice results, including white-dice criticals. Its target mix is 40% armored vehicles, 20% unarmored ’Mechs, 10% open conventional infantry, 15% covered conventional infantry, and 15% battle armor. It weighs stationary fire at 65% and moving fire at 35%. Recoil, Energy heat, Rocket restrictions, damage limits, and Piercing all apply.

Range adds 0.025 per maximum-range inch and subtracts 0.025 per minimum-range inch. For moving fire, add the half-speed Advance allowance, rounded up, plus 2 inches for blue speed equipment. This estimates how far a unit can reach with a shot; full speed still sets its separate Mobility rating. Wider arcs get a small bonus. Indirect access adds 15% of its expected damage. Close attacks use a 0.4 reach allowance, split between frontal and rear attacks. The best attack counts fully; a different second choice adds 15%, since it offers a choice rather than another attack.

For ’Mechs, a 24-action Fire/Vent or Advance/Vent calculation uses the actual heat track and vent rating. Heat damage modifiers and a small stress allowance reduce output. **Support** adds 0.35 for gray attack and 0.15 for yellow damage while shown.

For **vehicles and infantry**, a separate 24-action calculation chooses between attacking and recovering. A first attack commits the unit. A second attacks at its current values, then pushes it one click down its actual combat dial. Spent units must recover, and destruction ends their output. The calculation can recover early when preserving a good click is worth more than another immediate attack. It starts Ready at each click in turn and uses the result per action to price that click.

Some dials improve after taking damage. To price a particular click, this readiness estimate caps later attacks at that click’s firepower. Later improvements still add value on their own clicks; they are not also charged to earlier, weaker ones. This is a pricing convention and does not limit attacks during play.

Datasheets show firepower before readiness, a **readiness multiplier**, and the firepower used in the price. These summary ratings are weighted by click weight and toughness, matching the contributions above. This estimates sustained output; the multiplier is not a fixed discount. ’Mechs use heat instead. Both models use 24 actions, but neither predicts a whole battle.

## Special cases

- A Rocket test substitute uses the alternate cost on its datasheet. Record that cost before deployment and keep it for the return game.
- Carriers use the allowance for the chosen [game size](core-rules.md#force-organization). Designation adds no separate charge in this version.
- Aircraft, artillery-only units, DropShip turrets, and other excluded types still get catalog costs. Those estimates use the same model, but do not make them legal in a core game. Special flight, artillery, and DropShip rules are not priced here.
- Repair stops, exact base size, heat-related movement loss, mission layouts, squad coordination, and pilot combinations are not fully modeled. The readiness model includes pushing damage but not critical-miss self-damage, enemy attacks, or repairs. Click weights express an early-strength preference, not measured survival odds. Test these before treating the costs as settled.

## Changing costs

The calculator is [units/points.py](../units/points.py), with shared transitions in [readiness.py](../units/readiness.py); all tuning weights are in [points-config.json](../units/points-config.json). Change the formula version when changing weights, then rebuild the catalog, cards, and sample armies together. Keep one formula version for both games in a test pair.

Record reasons for changes in the [adjustment log](../playtest/adjustments.csv). Prefer a shared formula correction over a special price for one unit.

The force builder always uses current catalog costs, including when it opens an older saved list. Review its total after an update and generate fresh cards. Keep an exported list and its cards if you need to finish a test pair under an older formula.
