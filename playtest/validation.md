# Checks so far

Version 0.3 · November 16, 2026

The checks below cover written rules, arithmetic, and generated files. **No tabletop games have been recorded.** Balance, play time, and fit with a wider collection still need testing.

## Completed checks

| Check | Result |
| --- | --- |
| Packet contents | Core rules, references, First Contact starter, three full missions, two starter patrols, three Standard sample armies, pilots, game log, playtest plan, and point-adjustment table are present |
| Starter scenario | Four rounds with one relay; scoring in rounds 2–4 gives three available points. Patrols A/B cost 594/590 points, each with seven models in five groups. Both pass Skirmish limits. Symmetric terrain, clear control area, source coordinates, and measured map geometry are checked |
| Teaching diagrams | Four local SVGs cover setup, movement and shooting, objective control, and pushing/recovery. They include accessible titles and descriptions. The map loads offline, fits mobile, and opens at full size for printing; each diagram was visually inspected |
| Earlier material | Compared Age of Destruction and the downloaded scenario handbook; source notes identify both |
| Army totals | H: 1,192 points / 15 groups. B: 1,192 / 17. I: 1,196 / 19. The totals differ by 4 points. Each has two carriers and follows the force chart |
| Force organization | All three rosters pass automated checks for unit-type caps, 2–3-base squads, repeated families, Unique IDs, pilots, carriers, passenger assignments, Rocket substitutions, and points. Mixed squads count toward every family they contain |
| Game sizes | 600-point Skirmish, 1,200-point Standard, 1,800-point Large Battle, and 2,400-point Grand Battle share one definition across Python and the browser. All four allow zero ’Mechs, vehicle-only forces, infantry-only forces, and mixed forces. Legal catalog rosters also reach each ’Mech cap. Budget boundaries, unit caps, pilots, carriers, and the unchanged rule of three are checked. The rules chart matches the published data |
| Breakthrough targets | 30% rounded up: H 358, B 358, I 359 |
| Catalog coverage | All 1,649 miniature entries in the source index parsed; all 1,649 local photos decoded successfully. Includes five DropShip turret sections |
| Unit types | 751 ’Mechs including quads and colossi, 519 vehicles, 213 battle armor, 161 conventional infantry, and five turrets. 114 entries are marked outside the core rules |
| Points | Every cost and Rocket substitute reproduces from formula 0.3-alpha-5. Each complete click is priced separately, with weights from 1.5 to 0.5. Eligible Jump clicks include a DFA allowance after landing risk and heat. Infantry Toughness includes stronger woods and fieldworks protection. Faction, name, and rarity do not affect pricing |
| Automated tests | Forty-seven tests cover starter patrols and map geometry, all catalog prices and Rocket alternatives, full dials, stat increases, criticals, weapons, heat, source parsing, photos, readiness, infantry terrain defense, DFA, and legal and illegal rosters at all four sizes. Dial checks cover early strength, degradation order, defense on the same click as firepower, weight normalization, weak tail clicks, and later improvements. Short schedules were also exhaustively enumerated to check the readiness optimizer independently |
| Restored equipment | Named colors match the original stat and weapon categories, including purple. Tests cover Salvage, armor grades, Piercing, Agility, Pulse, Rapid Strike, Flamers, Streak and ECM, starting-only Infiltrate value, and positive costs for useful equipment. Datasheets display ability names and every master-PDF card includes its faction |
| Factions | All 22 catalog factions are available. Mixed remains the default for older lists. Every base is checked in single-faction armies; Mercenary is not a wildcard. Model tests cover JSON round trips and invalid factions. Browser tests cover filtering, changing faction without deleting models, mismatch messages, reload, mobile layout, and faction labels on generated cards |
| Unit PDF | 1,649 photo cards on 825 US Letter pages, two 7.5 × 5 inch cards per page. Every combat and heat value, color code, repair-mark count, and catalog ID checked against the extracted PDF. Sampled infantry, ’Mech, turret, longest-dial, and long-name cards independently rendered and visually checked |
| Seize and Hold score | 5 scoring rounds × 3 sites = 15 available points |
| Critical dice | The two white dice decide critical results; the third does not. Check target legality before rolling |
| Cover example | For attack 8 against base defense 18, all 216 dice results give: open 62.50%, +2 cover 37.50%, +3 cover 25.93%, +4 cover 16.67%, including criticals. Fieldworks close defense and Salvage preventing attacks are checked. The terrain chart matches the pricing inputs |
| Close damage examples | Conventional infantry: 0 through Armor 1 from the open front, 2 in an exposed assault. Battle armor with damage 2: 3 in close combat |
| Close pivots and DFA | Fire may pivot for a close attack while keeping center and contacts fixed. DFA uses full speed with Jump, +2 target defense, +2 primary damage, 1/2 landing damage, and 2 total heat. Blue-speed catalog ’Mechs can Jump and use DFA; the original equipment card confirms the color. The formula checks legal profiles, all 216 rolls, armor, rear attacks, landing risk, heat, and current-click eligibility; tabletop balance is untested |
| Weapon examples | Damage-3 Ballistic / Energy / Rocket-direct / Rocket-indirect: 4/2/3/2 against open conventional infantry; 3/2/3/2 in cover; 2/3/2/1 against larger Armor-1 targets |
| Weapon limits | Energy criticals still obey the infantry damage limit. Energy Fire/Advance give 2/3 ’Mech heat. Rockets cannot Advance-fire |
| Moving fire | Advance is half speed, rounded up before equipment bonuses, and adds no attack penalty. Ballistic recoil is −1, removed by Gunner only within the half-speed movement cost. Energy has no movement accuracy penalty |
| Readiness reference | One US Letter page generated from the Markdown source, with a six-group tracker. Independently rendered and visually checked |
| Pilot text | The four abilities in the rules match the card data |
| Pilot PDF | Generator produces four 2.5 × 3.5 inch cards on US Letter, with valid PDF offsets |
| Pilot layout | The PDF was independently rendered and visually checked; ability text, name fields, and reminders fit |
| Fieldworks objectives | Objectives sit on the edge. A 3-inch-diameter large base can stay outside and within control range |
| Handbook identity | Local file: 116 pages, v2.1, Mike “Rimoran” McCarrig, December 15, 2020. File hash is in the source notes |
| HTML | 27 offline pages and 1,790 search entries. Local links, anchors, IDs, headings, PDF offsets and page sizes, roster costs, unit-family data, game-size charts, SVG assets, and JavaScript syntax checked. README Pages links resolve to generated pages, anchors, or downloads |
| Browser | Isolated headless Chrome checks passed for catalog search, filters, photos, paging, dials, Rocket pricing, readiness, and missing units. Click-value curves and contribution tables match the catalog. Catalog, rules, readiness, unit cards, long dials, pricing details, and the force builder fit a 390-pixel viewport without page overflow |
| Datasheet printing | Both a 14-click ’Mech and the 23-click longest dial print on one Letter page with complete combat and heat tracks. Independently rendered and visually checked |
| Force builder | Fourteen model checks cover starter patrols, sample-list parity, family limits, mixed squads, forces with zero ’Mechs, size-specific budgets and caps, pilots, Unique figures, carriers, Rocket prices, import validation, and card assignments. Browser checks cover vehicle-only and infantry-only forces, zero ’Mechs at every size, switching sizes without losing models, loading Standard and starter samples, preserving size on reload and JSON export/import, rejected broken imports, generated cards, and recalculating an older saved list with a notice. Starter links respect a declined replacement; unknown sample links preserve the saved roster. Older lists without a size use Standard |
| Selected-model cards | An eight-model list produced exactly eight cards on four Letter pages, including the chosen Rocket cost, pilot names, squad labels, and assigned carrier. Every sheet also shows game size and points. Representative output independently rendered and visually checked. Draft lists can also print |
| Starter card sheets | Each patrol produced seven cards on four Letter pages, with Skirmish limits met and correct assignments |

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
| Speed 7 with blue speed equipment | Advance allowance 4; Jump ignores route terrain and adds 1 heat, without extra distance |
| Spent group in Breakthrough | May use Move to recover and exit while unengaged; the whole on-foot squad must cross together |
| First squad attack changes the target’s equipment | Finish that attack with the old values; the next attack uses the new dial |
| Heat reaches shutdown partway through a gain | Stop, discard extra heat, and skip the stress roll |
| Engineer Vents from shutdown | Extra cooling works. Restart when the symbols disappear; the activation is spent |
| Attack or damage reaches zero | Unit may still move, carry troops, and contest if otherwise allowed |
| Both players want to pass | Only the player with fewer groups left may pass |
| Damage changes a weapon’s color | Its E/B/R label stays fixed; equipment and numbers change normally |
| Indirect Rocket fire crosses a building | Allowed, but arc, range, cover, and friendly-contact rules still apply |
| Engaged ’Mech uses close Fire against an enemy behind it | May pivot before attacking, even at zero speed; center and existing contacts stay fixed. Ranged Fire cannot pivot |
| DFA hits with attack 8 plus dice 12 against defense 18 | Meets defense 20; primary damage 3 becomes 5, or 4 through Armor 1; attacker pays 1 landing damage then 2 total heat if alive |
| DFA misses or rolls white 1/1 | Miss costs 2 landing damage; a critical miss also deals its usual 1 first. Target stays in place and cannot pivot in response |
| DFA landing damage destroys its attacker | Finish the target’s damage and equipment heat first; remove the attacker and apply no further heat |
| DFA starts engaged, lacks current Jump, targets infantry, or has no legal landing | Not allowed; an ordinary close attack or legal movement must use its own action |
| Seize and Hold return game | Each army changes edge, whoever controls it |
| Hold the Station defender is wiped out | Attacker still needs both sites for two consecutive round ends |

## Still to check

Run the short exercises and eighteen-game plan, then a pair with other chassis from your collection. Check archive dials against the bases and record weapon labels or Rocket substitutes. The pricing model and force limits are starting estimates; automated checks do not establish game balance.

The PDFs have not been physically printed. Print one sheet at 100% to check card size and legibility on your printer.

Browser print settings vary. Use 100% scale and enable background graphics; the color letters also identify equipment in black-and-white prints.

Repeat the checks with `python units/test_catalog.py`, `node web/test_force_model.js`, then `python web/check_packet.py` after rebuilding. Optional browser checks use `web/preview_check.py --port 9234` with a separate Chrome debugging profile and `websocket-client`.
