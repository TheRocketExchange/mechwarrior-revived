# MechWarrior Revived

Tabletop rules for your MechWarrior clix collection: 4–8 ’Mechs per side, plus vehicles and infantry. Players alternate activations, and each scenario sets the objective.

**Version 0.3 is ready for playtesting.** Balance and the roughly two-hour play target still need testing.

New in this edition: pushing and recovery for vehicles and squads, half-speed Advance, and one order per squad. See the [worked examples](docs/combat-rhythm.md) and [readiness reference](rules/readiness-reference.md). The [v0.2 tag](https://github.com/TheRocketExchange/mechwarrior-revived/tree/v0.2) preserves the previous rules and prices.

## Start playing

Open the [HTML rulebook](site/rules.html) or browse the [rules hub](site/index.html). Both work offline, with search, print styles, and card downloads. The navigation is inspired by [NetEA](https://www.net-armageddon.org/).

The [unit catalog](site/units.html) has 1,649 source-linked photo datasheets, full dials, and costs from one [points formula](rules/points.md). [Printable unit cards](units/revived-unit-cards.pdf) cover the whole catalog, four per page. Original printed costs are reference only.

1. Read the [core rules](rules/core-rules.md) and choose a [sample force](playtest/sample-forces.md).
2. Start with [Seize and Hold](scenarios/01-seize-and-hold.md). Place terrain before choosing sides.
3. Keep the [turn reference](rules/turn-reference.md), [equipment sheet](rules/equipment-reference.md), and [pilot cards](pilots/pilot-cards.md) nearby.
4. Record the game in the [playtest log](playtest/playtest-log.md), then play again with sides reversed.

Use the rules in this packet. Original abilities, formations, pilots, gear, and expansion rules apply only where restated here.

## In the packet

| Rules and game aids | Background and testing |
| --- | --- |
| [Core rules](rules/core-rules.md) | [Design notes](docs/design-brief.md) |
| [Weapons](rules/weapon-reference.md) | [Earlier rules and handbook comparison](docs/comparison.md) |
| [Equipment](rules/equipment-reference.md) | [Sources](docs/sources.md) |
| [Turn reference](rules/turn-reference.md) | [Sample forces](playtest/sample-forces.md) |
| [Pilot cards](pilots/pilot-cards.md) | [Playtest plan](playtest/protocol.md) |
| [Seize and Hold](scenarios/01-seize-and-hold.md) | [Game log](playtest/playtest-log.md) |
| [Breakthrough](scenarios/02-breakthrough.md) | [Point adjustments](playtest/adjustments.csv) |
| [Hold the Station](scenarios/03-hold-the-station.md) | [Checks so far](playtest/validation.md) |

## GitHub Pages

The workflow in `.github/workflows/pages.yml` rebuilds and checks the packet, then publishes only `site/`. Pushes to the repository’s default branch deploy automatically. Pull requests run the same build and checks without deploying. You can also run it from the Actions tab.

When this folder is uploaded to a GitHub repository, open **Settings → Pages → Build and deployment**, and choose **GitHub Actions** as the source. Keep the cached records in `units/source/` and photos in `units/photos/` in the repository so builds work without fetching the archive. The workflow’s deployment shows the published URL.

The site uses relative links, so it works under a repository path such as `https://USERNAME.github.io/REPOSITORY/`. Temporary browser profiles and preview dependencies are excluded by `.gitignore`.

## Editing the packet

Run `python build.py` to rebuild costs, sample armies, both card PDFs, the readiness PDF, and the HTML from cached source records. Install dependencies from [web requirements](web/requirements.txt) and [catalog requirements](units/requirements.txt).

Edit rules in the Markdown files. Pricing lives in [points.py](units/points.py), with all tuning weights in [points-config.json](units/points-config.json). Change the formula version when changing weights. Sample force counts live in [forces.json](playtest/forces.json); their Markdown and CSV are generated. Adjust counts if a formula change puts a force over the limit.

Run `python units/test_catalog.py` to check data and pricing. To refresh the public archive cache, run `python units/import_catalog.py --fetch`, then rebuild. Routine builds need no network.

For pilot changes, edit both the [card data](pilots/cards.json) and [pilot rules](pilots/pilot-cards.md), then rebuild.

