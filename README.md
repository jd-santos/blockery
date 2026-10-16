# Blockery

Vicious Blockery is a lightly-modded private Minecraft server for friends and family. Mods mostly target building tools, smoother everyday play, and performance fixes. If you're looking to join, the [Getting Started guide](https://blockery.notion.site/Getting-Started-568ff72b8dd24ce580cb377cfa1ffeaa) has the server details and setup steps.

This repository records shared Minecraft versions, mod metadata, resource packs, and reviewed settings. Separate build recipes select content for player clients and survival/creative servers without duplicating complete packs. The player client pack remains optional. The shared versions are **Minecraft 1.21.10** and **Fabric Loader 0.19.5**. Coordinated upgrades and Modrinth publishing are still being set up.

## Distribution names

- **Blockery** is the umbrella project and shared source.
- **Blockery Client** is the default, lightweight player client (`blockery-client`).
- **Blockery Extras Client** is the separately available expanded client (`blockery-extras-client`).
- **Blockery Server Survival** and **Blockery Server Creative** are server outputs, not player client packs.

The client split has two draft recipes:

- **Blockery Client:** 13 mods plus Redstone Tweaks. Simple Voice Chat, AppleSkin, Shulker Box
  Tooltip, Status Effect Timer, Xaero's minimap/world map, and MiniHUD form the everyday
  experience. Lithium, FerriteCore, ImmediatelyFast, and the existing View Distance Fix
  entry live here, with Fabric API and MaLiLib. View Distance Fix is a server-focused
  fog fix, not a promised client FPS improvement.
- **Blockery Extras Client:** inherits Blockery Client and adds specialist tools and visuals, including JEI, Axiom,
  Litematica, Tweakeroo, Inventory Profiles Next, and Fresh Animations with EMF/ETF.
  It preserves the other previous client entries pending their final review, for a total
  of 44 mods and two resource packs.

Both client drafts omit configuration and personal instance settings. Defaults,
keybindings, permissions, and clean-client gameplay still need review before release.
Both server recipes retain the same 30 mod entries and 11 reviewed shared gameplay
configs; target-specific settings remain outside the pack. Survival's `2026.10.12`
candidate passed local checks and was submitted to Modrinth by the owner. Approval
is pending. Creative and both clients remain release-gated.

## Build a distribution

The small Python build layer uses `uv` and the [pinned Packwiz build](docs/tooling.md).
Profiles are repository recipes, not a native Packwiz feature.

```sh
uv run --script scripts/build_pack.py list
uv run --script scripts/build_pack.py plan blockery-client
uv run --script scripts/build_pack.py build blockery-client --version naming-preview --draft
uv run --script scripts/build_pack.py build blockery-extras-client --version naming-preview --draft
```

Outputs go to ignored `local/dist/`. Drafts have `-draft` in their version and filename
and are not for publication. Normal release builds are blocked while a recipe has
pending checks. See [tooling](docs/tooling.md#distribution-builder) for recipe editing,
validation limits, and tests.

## Try the pack in Prism Launcher

Build the named draft above using the [pinned Packwiz build](docs/tooling.md).
In Prism Launcher, choose **Add Instance → Import** and select either
`local/dist/blockery-client-naming-preview-draft.mrpack` or
`local/dist/blockery-extras-client-naming-preview-draft.mrpack`. Use a separate new instance
for each and Java 21. Do not overwrite an existing player instance.

Resource packs are included, not automatically enabled: select Redstone Tweaks in
Minecraft's resource-pack menu. Blockery Extras Client also includes Fresh Animations and its EMF/ETF
support mods; enable the resource pack separately if wanted. Existing personalized
MiniHUD/map settings are not copied. Check overlays and keybindings in the clean
instance before treating defaults as approved. The [client checks](docs/tooling.md#client-smoke-test)
cover both drafts.

Direct root `packwiz modrinth export` bypasses distribution selection and release
checks. It is not the supported way to build either named client pack.

## What's in here

- `pack.toml` and `index.toml` record the Minecraft and loader versions and the files Packwiz installs.
- `mods/`, `resourcepacks/`, and `config/` hold the shared pack definition. Packwiz records where to download each mod and resource pack; the downloads themselves are not committed here.
- `build/profiles.toml` defines explicit selections; `build/disabled-mods.toml` retains reversible exclusions. `scripts/build_pack.py` exports selected content without changing root pack files.
- `scripts/validate_pack.py` checks source integrity; `scripts/upgrade_pack.py` reports upgrade candidates and confirms exclusions. Version application is not implemented yet.
- `.github/workflows/validate.yml` runs checks and produces short-lived draft artifacts, not public releases or deployments.
- `tests/` covers recipe selection, inheritance, safety checks, build isolation, reports, exclusions, and archive audits.
- `deploy/targets/` is reserved for settings that differ between the [main and creative servers](deploy/README.md). No differences have been confirmed yet.
- `docs/` covers [Packwiz tooling](docs/tooling.md), [coordinated upgrades and manual rollback](docs/upgrades.md), and [syncing local client data](docs/local-sync.md).

## License

Original Blockery build scripts, pack definitions, documentation, and original configuration
contributions are licensed under **GPL-3.0-or-later**. You may redistribute and modify that
material under the GNU General Public License, version 3 or any later version. It is
provided without warranty; see [LICENSE](LICENSE) for the full terms.

This does not relicense third-party mods, libraries, resource packs, generated configuration
text, or other upstream material. They retain their own terms and notices. In particular,
Axiom retains its separate license and multiplayer/commercial-use requirements.

## Making changes

Make changes here first. After changing a config file or Packwiz metadata, run `packwiz refresh`, then review `packwiz list` and the Git diff. Keep worlds, player data, logs, backups, credentials, and private keys out of the repository. The [deployment notes](deploy/README.md) explain how shared settings and server-specific settings are meant to fit together.
