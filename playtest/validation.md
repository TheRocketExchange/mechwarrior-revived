# Checks so far

Version 0.3 · November 16, 2026

The checks below cover written rules, arithmetic, and generated files. **No tabletop games have been recorded.** Balance, play time, and fit with a wider collection still need testing.

## Completed checks

| Check | Result |
| --- | --- |
| Packet contents | Core rules, references, three scenarios, three sample armies, pilots, game log, playtest plan, and point-adjustment table are present |
| Earlier material | Compared Age of Destruction and the downloaded scenario handbook; source notes identify both |
| Army totals | H: 1,178 points / 15 groups. B: 1,187 / 17. I: 1,171 / 19. The totals differ by 16 points. Each has two carriers and follows the force chart |
| Force organization | All three rosters pass automated checks for unit-type caps, 2–3-base squads, repeated families, Unique IDs, pilots, carriers, passenger assignments, Rocket substitutions, and points. Mixed squads count toward every family they contain |
| Breakthrough targets | 30% rounded up: H 354, B 357, I 352 |
| Catalog coverage | All 1,649 miniature entries in the source index parsed; all 1,649 local photos decoded successfully. Includes five DropShip turret sections |
| Unit types | 751 ’Mechs including quads and colossi, 519 vehicles, 213 battle armor, 161 conventional infantry, and five turrets. 114 entries are marked outside the core rules |
| Points | Every cost and Rocket substitute reproduces from formula 0.3-alpha-2. Each complete click is priced separately, with weights from 1.5 to 0.5. Faction, name, and rarity do not affect pricing |
| Automated tests | Thirty-one tests passed. They cover all catalog prices and Rocket alternatives, full dials, stat increases, criticals, weapons, heat, source parsing, photos, readiness, and legal and illegal rosters. New checks cover early strength, degradation order, defense on the same click as firepower, weight normalization, weak tail clicks, and later improvements. Short schedules were also exhaustively enumerated to check the readiness optimizer independently |
| Unit PDF | 1,649 photo cards on 825 US Letter pages, two 7.5 × 5 inch cards per page. Every combat and heat value, color code, repair-mark count, and catalog ID checked against the extracted PDF. Sampled infantry, ’Mech, turret, longest-dial, and long-name cards independently rendered and visually checked |
| Seize and Hold score | 5 scoring rounds × 3 sites = 15 available points |
| Critical dice | The two white dice decide critical results; the third does not. Check target legality before rolling |
| Cover example | For stationary attack 8 against defense 18, all 216 dice results give: open 62.50%, +2 cover 37.50%, +3 cover 25.93%, including criticals |
| Close damage examples | Conventional infantry: 0 through Armor 1 from the open front, 2 in an exposed assault. Battle armor with damage 2: 3 in close combat |
| Weapon examples | Damage-3 Ballistic / Energy / Rocket-direct / Rocket-indirect: 4/2/3/2 against open conventional infantry; 3/2/3/2 in cover; 2/3/2/1 against larger Armor-1 targets |
| Weapon limits | Energy criticals still obey the infantry damage limit. Energy Fire/Advance give 2/3 ’Mech heat. Rockets cannot Advance-fire |
| Moving fire | Advance is half speed, rounded up before equipment bonuses, and adds no attack penalty. Ballistic recoil is −1, removed by Gunner only within the half-speed movement cost. Energy has no movement accuracy penalty |
| Readiness reference | One US Letter page generated from the Markdown source, with a six-group tracker. Independently rendered and visually checked |
| Pilot text | The four abilities in the rules match the card data |
| Pilot PDF | Generator produces four 2.5 × 3.5 inch cards on US Letter, with valid PDF offsets |
| Pilot layout | The PDF was independently rendered and visually checked; ability text, name fields, and reminders fit |
| Fieldworks objectives | Objectives sit on the edge. A 3-inch-diameter large base can stay outside and within control range |
| Handbook identity | Local file: 116 pages, v2.1, Mike “Rimoran” McCarrig, December 15, 2020. File hash is in the source notes |
| HTML | 25 offline pages and 1,767 search entries. Local links, anchors, IDs, headings, PDF offsets and page sizes, roster costs, unit-family data, and JavaScript syntax checked. README Pages links resolve to generated pages, anchors, or downloads |
| Browser | Isolated headless Chrome checks passed for catalog search, filters, photos, paging, dials, Rocket pricing, readiness, and missing units. Click-value curves and contribution tables match the catalog. Catalog, rules, readiness, unit cards, long dials, pricing details, and the force builder fit a 390-pixel viewport without page overflow |
| Datasheet printing | Both a 14-click ’Mech and the 23-click longest dial print on one Letter page with complete combat and heat tracks. Independently rendered and visually checked |
| Force builder | Eight model checks cover sample-list parity, family limits, mixed squads, unit caps, pilots, Unique figures, carriers, Rocket prices, import validation, and card assignments. Browser checks cover editing, reload persistence, JSON export/import, rejected broken imports, generated cards, and recalculating an older saved list with a notice |
| Selected-model cards | An eight-model list produced exactly eight cards on four Letter pages, including the chosen Rocket cost, pilot names, squad labels, and assigned carrier. Representative output independently rendered and visually checked. Draft lists can also print |

The hit percentages isolate cover; they do not predict how a whole battle will play.

## Sequence checks

| Situation | What happens |
| --- | --- |
| Squad boards, then carrier moves | Squad cannot act again that round |
| Carrier moves, then squad unloads | Unloading uses the squad’s activation; it cannot attack |
| Loaded carrier is destroyed before or after passengers act | Apply passenger damage, place survivors, and mark the squad activated. No extra activation |
| Squad cannot fully unload | Stay aboard. A destroyed carrier instead saves as many passengers as can fit |
| Fire, Fire, Move by a vehicle | Ready → Committed → Spent, paying 1 after the second action; Move clears readiness without repairing damage |
| Fire, Hold, Fire | Recover early; no pushing damage |
| A pushing attack is skipped or has no legal target | State still becomes Spent; each surviving base pays its own pushing damage |
| Critical miss while pushing | Pay the miss first, then push if alive. Stop at destruction; never transfer a casualty’s cost |
| Squad has different legal shots | One shared order; each base resolves its own legal parts, target, and roll. All surviving members pay a push |
| Spent squad has an engaged member | That member Holds or Disengages at normal cost; others Move or Hold and maintain the chain |
| Spent squad is split | Regroup, clear readiness when the activation ends, and regroup again next time if still split. No boarding or exit during regroup |
| Passengers Hold, unload, or evacuate | Only Hold clears their readiness; their carrier tracks its own state |
| Speed 7 with blue speed equipment | Advance allowance 6; Gunner still limits movement cost to 4, including terrain |
| Spent group in Breakthrough | May use Move to recover and exit while unengaged; the whole on-foot squad must cross together |
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

Run the short exercises and eighteen-game plan, then a pair with other chassis from your collection. Check archive dials against the bases and record weapon labels or Rocket substitutes. The pricing model and force limits are starting estimates; automated checks do not establish game balance.

The PDFs have not been physically printed. Print one sheet at 100% to check card size and legibility on your printer.

Browser print settings vary. Use 100% scale and enable background graphics; the color letters also identify equipment in black-and-white prints.

Repeat the checks with `python units/test_catalog.py`, `node web/test_force_model.js`, then `python web/check_packet.py` after rebuilding. Optional browser checks use `web/preview_check.py --port 9234` with a separate Chrome debugging profile and `websocket-client`.
