# Checks so far

Version 0.2 · November 14, 2026

The checks below cover written rules, arithmetic, and generated files. **No tabletop games have been recorded.** Balance, play time, and fit with a wider collection still need testing.

## Completed checks

| Check | Result |
| --- | --- |
| Packet contents | Core rules, references, three scenarios, three sample armies, pilots, game log, playtest plan, and point-adjustment table are present |
| Earlier material | Compared Age of Destruction and the downloaded scenario handbook; source notes identify both |
| Army totals | H: 1,196 points / 15 groups. B: 1,188 / 15. I: 1,196 / 17. Each has two carriers and 4–8 ’Mechs |
| Breakthrough targets | 30% rounded up: H 359, B 357, I 359 |
| Catalog coverage | All 1,649 miniature entries in the source index parsed; all 1,649 local photos decoded successfully. Includes five DropShip turret sections |
| Unit types | 751 ’Mechs including quads and colossi, 519 vehicles, 213 battle armor, 161 conventional infantry, and five turrets. 114 entries are marked outside the core rules |
| Points | Every cost and Rocket substitute reproduces from formula 0.2-alpha-1. Original cost, faction, name, and rarity do not affect pricing |
| Pricing tests | Twelve automated tests cover full-dial costs, stat increases, criticals, infantry limits, weapon tradeoffs, heat, source parsing, and photo coverage |
| Unit PDF | 1,649 photo cards on 413 US Letter pages. All IDs extracted from the PDF; sampled pages independently rendered and visually checked |
| Seize and Hold score | 5 scoring rounds × 3 sites = 15 available points |
| Critical dice | The two white dice decide critical results; the third does not. Check target legality before rolling |
| Cover example | For stationary attack 8 against defense 18, all 216 dice results give: open 62.50%, +2 cover 37.50%, +3 cover 25.93%, including criticals |
| Close damage examples | Conventional infantry: 0 through Armor 1 from the open front, 2 in an exposed assault. Battle armor with damage 2: 3 in close combat |
| Weapon examples | Damage-3 Ballistic / Energy / Rocket-direct / Rocket-indirect: 4/2/3/2 against open conventional infantry; 3/2/3/2 in cover; 2/3/2/1 against larger Armor-1 targets |
| Weapon limits | Energy criticals still obey the infantry damage limit. Energy Fire/Advance give 2/3 ’Mech heat. Rockets cannot Advance-fire |
| Moving fire | Advance adds no attack penalty. Ballistic recoil is −1, removed by Gunner only within half speed, rounded up and counting terrain. Energy has no movement accuracy penalty |
| Pilot text | The four abilities in the rules match the card data |
| Pilot PDF | Generator produces four 2.5 × 3.5 inch cards on US Letter, with valid PDF offsets |
| Pilot layout | The PDF was independently rendered and visually checked; ability text, name fields, and reminders fit |
| Fieldworks objectives | Objectives sit on the edge. A 3-inch-diameter large base can stay outside and within control range |
| Handbook identity | Local file: 116 pages, v2.1, Mike “Rimoran” McCarrig, December 15, 2020. File hash is in the source notes |
| HTML | 21 offline pages and 1,738 search entries. Local links, anchors, IDs, headings, PDF offsets, roster costs, and JavaScript syntax checked |
| Browser | Chrome checks passed for photos, pagination, search, filters, sorting, combat dials, Rocket costs, and missing IDs. No JavaScript exceptions; desktop and phone layouts checked |
| Datasheet printing | A representative ’Mech datasheet, including its photo, weapons, and heat table, fits one Letter page in Chrome |

The hit percentages isolate cover; they do not predict how a whole battle will play.

## Sequence checks

| Situation | What happens |
| --- | --- |
| Squad boards, then carrier moves | Squad cannot act again that round |
| Carrier moves, then squad unloads | Unloading uses the squad’s activation; it cannot attack |
| Loaded carrier is destroyed before or after passengers act | Apply passenger damage, place survivors, and mark the squad activated. No extra activation |
| Squad cannot fully unload | Stay aboard. A destroyed carrier instead saves as many passengers as can fit |
| First squad attack changes the target’s equipment | Finish that attack with the old values; the next attack uses the new dial |
| Heat reaches shutdown partway through a gain | Stop, discard extra heat, and skip the stress roll |
| Engineer Vents from shutdown | Extra cooling works. Restart when the symbols disappear; the activation is spent |
| Attack or damage reaches zero | Unit may still move, carry troops, and contest if otherwise allowed |
| Both players want to pass | Only the player with fewer groups left may pass |
| Damage changes a weapon’s color | Its E/B/R label stays fixed; equipment and numbers change normally |
| Indirect Rocket fire crosses a building | Allowed, but arc, range, cover, and friendly-contact rules still apply |
| Seize and Hold return game | Each army changes edge, whoever controls it |
| Hold the Station defender is wiped out | Attacker still needs both sites for two consecutive round ends |

## Still to check

Run the short exercises and eighteen-game plan, then a pair with mixed chassis. Check archive dials against the bases and record weapon labels or Rocket substitutes. The pricing model is a starting estimate; automated checks do not establish game balance.

The PDFs have not been physically printed. Print one sheet at 100% to check card size and legibility on your printer.

Chrome failed when launched through the restricted session. Browser checks now pass with an isolated profile in the normal desktop session. Open the finished HTML through Windows normally.

Repeat the data checks with `python units/test_catalog.py`, then `python web/check_packet.py` after rebuilding. Optional browser checks use `web/preview_check.py` with a separate Chrome debugging profile and `websocket-client`.
