# How v0.3 changes a battle

Version 0.3 · Worked examples, not playtest results.

Vehicles and infantry now have a reason to pause, and moving into firing range takes more commitment. Squads choose a common order while keeping their separate attacks. These changes bring back some of the original game’s pacing within Revived’s alternating activations.

## Push now or preserve the dial

Consider a vehicle with a target available throughout six activations. Ignore enemy damage and critical misses for this example.

| Schedule | Attacks | Recovery actions | Pushing damage |
| --- | ---: | ---: | ---: |
| v0.2: Fire six times | 6 | 0 | 0 |
| v0.3: Fire, Hold, Fire, Hold, Fire, Hold | 3 | 3 | 0 |
| v0.3: Fire, Fire, Hold, Fire, Fire, Hold | 4 | 2 | 2 |
| v0.3: Fire, Hold, Fire, Hold, Fire, Fire | 4 | 2 | 1 |

The last two patterns make the same number of attacks, but at different times and costs. Pushing early can remove a threat before it acts or help win an objective this round. Waiting preserves good dial values. Near the end of a game, future recovery matters less. These are illustrative schedules, not a claim that one is always best.

Move can replace Hold when unengaged. Recovery can therefore advance toward cover or an objective. Rush goes farther but leaves readiness unchanged. A Committed unit that Rushes is still Committed when it next fires.

Pushing uses the dial **before** taking its damage. A vehicle on its last live click can make that final attack, then be destroyed by its push. If a critical miss destroys it first, it does not pay a second damage or pass damage to an ally.

## The moving firing line gets shorter

For speed 8 and range 12 on open ground, with clear sight and no equipment bonus:

| Choice | Movement | Furthest shot from the starting center |
| --- | ---: | ---: |
| Fire | 0 inches | 12 inches |
| v0.2 Advance | 8 inches | 20 inches |
| v0.3 Advance | 4 inches | 16 inches |
| v0.3 Move | 8 inches | No shot |

This is a straight-line reach example, not a circular zone of guaranteed hits. Bases, arcs, terrain, and blockers still matter. Half-speed Advance gives an opponent more room to approach without immediately entering a moving shot. It also makes a firing position worth preparing with a Move or Rush.

There is no new accuracy penalty. Moving Ballistics still have -1 recoil; Energy still trades penetration for heat; Rockets still require Fire. ’Mechs gain 1 heat for Move or 2 for Advance, plus any Energy or Jump heat.

**Odd speed and equipment:** Speed 7 gives Advance 4. Blue speed raises that allowance to 6. Gunner still removes recoil only if movement costs 4 or less. Moving 2 inches through woods costs 4; moving 3 costs 6 and loses Gunner’s benefit. Blue speed does not increase Move.

## A squad commits together

A Committed three-base squad chooses Advance. The first base fires, the second has a blocked shot, and the third carries only Rockets. Each may move its own half-speed allowance. Only the first can shoot; all three surviving bases take 1 pushing damage after their own actions. The squad ends Spent.

With Fire instead, the Rocket base could shoot if it had a legal target. The other members would stay still and could choose different targets. No member adds to another member’s attack roll. The decision is now about coordinating positions and weapon needs, without building combined-fire bonuses.

On recovery, a member touching an enemy may Hold or Disengage while the others Move or Hold. A split squad must follow regroup movement and cannot use that activation to board or score an exit. A sole survivor keeps the squad’s readiness.

## Passengers and objectives

A Committed squad can board and later unload, but both leave it Committed. Hold aboard clears it while the carrier takes its own action. A Spent squad aboard must Hold before unloading on a later activation. Destruction of the carrier forces evacuation without clearing passenger readiness.

Spent units still contest objectives and count when checking whether a player can pass. In Breakthrough, Move lets an unengaged Spent group recover while exiting; an on-foot squad must leave together. A group cannot score an exit while regrouping.

## What the points model can tell us

The [calculator](../rules/points.md) compares attack and recovery choices over 24 actions, following pushing damage along the dial. It can recover early to save a strong click or spend a final click on one last attack. It prices every click alongside its own defense, speed, and equipment, with earlier clicks carrying more weight. A unit that loses strength quickly costs less than one that holds onto it. Later improvements are paid for on their own clicks rather than also raising the price of earlier weak ones.

This estimates sustained firepower. It does not know where objectives are, what an enemy will do, or whether three squad members can all get a shot. More affordable support units may also mean more bodies and activations at the same points limit. Test fixed armies first to isolate the rules, then rebuilt armies to see the effect of prices.

## Compare four cases

| Case | Readiness | Advance | Purpose |
| --- | --- | --- | --- |
| A: v0.2 baseline | None | Full speed | Previous rules |
| B: readiness only | v0.3 | Full speed | Isolate pauses and pushing |
| C: movement only | None | Half speed | Isolate moving shot reach |
| D: v0.3 core | v0.3 | Half speed | Test the combined change |

Keep the exact miniatures, pilots, squads, map, and deployment roles for the first comparison. Cases B and C are test variants, not alternate published core rules. Keep v0.2 squad action choices in A, B, and C; in D use the shared squad order. Record when that extra change matters, since D is not a pure two-variable comparison. If it seems important, repeat D once with separate squad orders to isolate coordination.

Use the same fixed roster costs and Breakthrough threshold across that first comparison; do not mix formula editions within a game. Then rebuild to the v0.3 points limit and repeat A/D with each edition’s own costs. Play return games with sides exchanged. Log attacks, recovery actions, pushing damage and losses, objective results, time, and each group’s action sequence. Full instructions and blank tables are in the [playtest plan](../playtest/protocol.md) and [game log](../playtest/playtest-log.md).

[The v0.2 release](https://github.com/TheRocketExchange/mechwarrior-revived/tree/v0.2) preserves the previous rules and costs. Equipment meanings, expanded original heat effects, and additional pilots are reserved for a later review.
