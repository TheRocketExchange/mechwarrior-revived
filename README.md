# MechWarrior Revived

MechWarrior Revived is a tabletop wargame of combined-arms battles in the BattleTech universe. Command BattleMechs, armored vehicles, and infantry as you fight to seize ground, break through enemy lines, or hold a vital position.

Players take turns moving and fighting with one unit or squad at a time. A damaged combat dial changes what a unit can do. Heat and pushing force you to decide when another attack is worth the strain, and when to pull back or recover.

Play with your existing MechWarrior clix miniatures and their combat dials. These fan-made rules include scenarios, photo datasheets, and printable game aids.

**[Open the rulebook](https://therocketexchange.github.io/mechwarrior-revived/) · [Read the rules](https://therocketexchange.github.io/mechwarrior-revived/rules.html) · [Browse the units](https://therocketexchange.github.io/mechwarrior-revived/units.html)**

**Version 0.3 is ready for playtesting.** Balance at each size and the roughly two-hour target for Standard games still need testing. The [worked examples](https://therocketexchange.github.io/mechwarrior-revived/combat-rhythm.html) explain pushing, recovery, and moving fire. The [v0.2 tag](https://github.com/TheRocketExchange/mechwarrior-revived/tree/v0.2) preserves the previous edition.

## Your first game

1. Read [how the game works](https://therocketexchange.github.io/mechwarrior-revived/rules.html#1-how-the-game-works), then choose one of the [sample forces](https://therocketexchange.github.io/mechwarrior-revived/forces.html).
2. Start with [Seize and Hold](https://therocketexchange.github.io/mechwarrior-revived/seize-and-hold.html). Set out the terrain and objectives before deploying.
3. Keep the [turn reference](https://therocketexchange.github.io/mechwarrior-revived/turn.html), [readiness sheet](https://therocketexchange.github.io/mechwarrior-revived/readiness.html), [equipment sheet](https://therocketexchange.github.io/mechwarrior-revived/equipment.html), and [pilot cards](https://therocketexchange.github.io/mechwarrior-revived/pilots.html) nearby.
4. Record the game in the [playtest log](https://therocketexchange.github.io/mechwarrior-revived/log.html), then play again with sides reversed.

Use the rules in this packet. Original abilities, formations, pilots, gear, and expansion rules apply only where restated here.

## Build your own force

Once you know the basics, [choose a game size](https://therocketexchange.github.io/mechwarrior-revived/rules.html#choose-the-battle-size): **Skirmish (600), Standard (1,200), Large Battle (1,800), or Grand Battle (2,400 points per side)**. Each has a [force chart](https://therocketexchange.github.io/mechwarrior-revived/rules.html#force-organization) with ’Mech, vehicle, squad, pilot, and carrier limits. The rule of three applies at every size. Larger games use a 72 × 48 inch battlefield; the smaller two use 48 × 48.

Use the [force builder](https://therocketexchange.github.io/mechwarrior-revived/builder.html) to select a game size, choose models, arrange squads, and assign pilots and carriers. It adds up points, checks that size’s limits, and saves your list in your browser. Export a list to keep a backup or move it to another device. **Generate unit cards** creates a print sheet for just your models, with the game size, roster labels, and assignments filled in; use **Print / Save as PDF** to keep a copy.

The [unit catalog](https://therocketexchange.github.io/mechwarrior-revived/units.html) has 1,649 photo datasheets with full dials and costs from one [points formula](https://therocketexchange.github.io/mechwarrior-revived/points.html). Each datasheet identifies its unit family for the rule of three. [Download the unit cards](https://therocketexchange.github.io/mechwarrior-revived/downloads/revived-unit-cards.pdf), two per page with complete combat and heat dials, or the [catalog CSV](https://therocketexchange.github.io/mechwarrior-revived/downloads/unit-catalog.csv). The [card guide](https://therocketexchange.github.io/mechwarrior-revived/units.html#reading-a-unit-card) explains IDs, squad and carrier assignments, and clicks.

Points value every click as a complete profile. Early strength carries more weight, and units that keep their performance through damage cost more than those that fade quickly. Open a datasheet’s cost breakdown to see its curve and each click’s contribution. The [force builder](https://therocketexchange.github.io/mechwarrior-revived/builder.html) recalculates saved lists with current costs; review your total and regenerate cards after a formula update.

## Rules and game aids

| At the table | Background and testing |
| --- | --- |
| [Core rules](https://therocketexchange.github.io/mechwarrior-revived/rules.html) | [Design notes](https://therocketexchange.github.io/mechwarrior-revived/design.html) |
| [Weapons](https://therocketexchange.github.io/mechwarrior-revived/weapons.html) | [Earlier rules and handbook comparison](https://therocketexchange.github.io/mechwarrior-revived/comparison.html) |
| [Equipment](https://therocketexchange.github.io/mechwarrior-revived/equipment.html) | [Sources](https://therocketexchange.github.io/mechwarrior-revived/sources.html) |
| [Turn reference](https://therocketexchange.github.io/mechwarrior-revived/turn.html) | [Sample forces](https://therocketexchange.github.io/mechwarrior-revived/forces.html) |
| [Readiness reference](https://therocketexchange.github.io/mechwarrior-revived/readiness.html) | [Combat examples](https://therocketexchange.github.io/mechwarrior-revived/combat-rhythm.html) |
| [Pilot cards](https://therocketexchange.github.io/mechwarrior-revived/pilots.html) | [Playtest plan](https://therocketexchange.github.io/mechwarrior-revived/playtest.html) |
| [Seize and Hold](https://therocketexchange.github.io/mechwarrior-revived/seize-and-hold.html) | [Game log](https://therocketexchange.github.io/mechwarrior-revived/log.html) |
| [Breakthrough](https://therocketexchange.github.io/mechwarrior-revived/breakthrough.html) | [Points adjustments](https://therocketexchange.github.io/mechwarrior-revived/downloads/adjustments.csv) |
| [Hold the Station](https://therocketexchange.github.io/mechwarrior-revived/hold-the-station.html) | [Checks so far](https://therocketexchange.github.io/mechwarrior-revived/validation.html) |

All [game aids and downloads](https://therocketexchange.github.io/mechwarrior-revived/aids.html) are collected on the site. For offline play, download this repository and open [site/index.html](site/index.html). Search, printing, and card downloads also work locally. The navigation is inspired by [NetEA](https://www.net-armageddon.org/).

## GitHub Pages

The live rulebook is at **[therocketexchange.github.io/mechwarrior-revived](https://therocketexchange.github.io/mechwarrior-revived/)**.

The [Pages workflow](.github/workflows/pages.yml) rebuilds and checks the packet, then publishes `site/`. Pushes to `main` deploy automatically; pull requests run the build and checks without deploying. View deployments or run a manual build on the [Actions page](https://github.com/TheRocketExchange/mechwarrior-revived/actions/workflows/pages.yml).

Keep the cached records in `units/source/` and photos in `units/photos/` in the repository so builds work without fetching the archive. The generated site uses relative links. Temporary browser profiles and preview dependencies are excluded by `.gitignore`.

## Editing the packet

Run `python build.py` to rebuild costs, sample armies, card PDFs, the readiness PDF, and HTML from cached records. Install dependencies from [web requirements](web/requirements.txt) and [catalog requirements](units/requirements.txt).

Edit the rules in their Markdown source files, starting with [core-rules.md](rules/core-rules.md). Pricing lives in [points.py](units/points.py), with tuning weights in [points-config.json](units/points-config.json). Change the formula version when changing weights. Sample rosters live in [forces.json](playtest/forces.json); [update_forces.py](units/update_forces.py) checks their organization and generates the tables and CSV.

Run `python units/test_catalog.py`, `node web/test_force_model.js`, and `python web/check_packet.py` after rebuilding. The builder reads the same catalog costs and force limits as the roster generator; it never accepts saved prices from an imported list. To refresh the public archive cache, run `python units/import_catalog.py --fetch`. Routine builds need no network.

For pilot changes, edit both the [card data](pilots/cards.json) and [pilot rules](pilots/pilot-cards.md), then rebuild.
