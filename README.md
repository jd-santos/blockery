# Blockery

Vicious Blockery is a lightly-modded private Minecraft server for friends and family. Mods mostly target building tools, smoother everyday play, and performance fixes. If you're looking to join, the [Getting Started guide](https://blockery.notion.site/Getting-Started-568ff72b8dd24ce580cb377cfa1ffeaa) has the server details and setup steps.

This repository records shared Minecraft versions, mod metadata, resource packs, and reviewed settings. Separate build recipes select content for player clients and survival/creative servers without duplicating complete packs. The player client pack remains optional. The shared versions are **Minecraft 1.21.10** and **Fabric Loader 0.19.5**. Server deployment and Modrinth publishing are still being set up.

## Distribution names

- **Blockery** is the umbrella project and the default, minimal player client (`blockery`).
- **Blockery Pro** is the separately available expanded client (`blockery-pro`).
- **Blockery Server Survival** and **Blockery Server Creative** are server outputs, not player client packs.

Client membership is not finalized. The `blockery` recipe has no selected mods yet;
Pro preserves the existing full client selection as a draft. Both server recipes
currently select the same 29 mod entries. No recipe includes configs until those files
are reviewed and explicitly selected. All four recipes have pending release checks.

## Build a distribution

The small Python build layer uses `uv` and the [pinned Packwiz build](docs/tooling.md).
Profiles are repository recipes, not a native Packwiz feature.

```sh
uv run --script scripts/build_pack.py list
uv run --script scripts/build_pack.py plan blockery-pro
uv run --script scripts/build_pack.py build blockery-server-survival --version infrastructure-preview --draft
```

Outputs go to ignored `local/dist/`. Drafts have `-draft` in their version and filename
and are not for publication. Normal release builds are blocked while a recipe has
pending checks. The empty minimal recipe cannot export yet, even as a draft.
See [tooling](docs/tooling.md#distribution-builder) for recipe editing and tests.

## Try the pack in Prism Launcher

The earlier combined export can still be imported into Prism Launcher. Direct root
exports bypass the new distribution recipes and release gates; they are legacy
validation candidates, not the named client/server releases. Install the
[pinned Packwiz build](docs/tooling.md), then run:

```sh
packwiz refresh
packwiz modrinth export -o Blockery-unreleased.mrpack
```

In Prism Launcher, choose **Add Instance → Import** and select `Blockery-unreleased.mrpack` to create a new instance.

Fresh Animations is included as a resource pack, but it needs Entity Model Features (EMF) to work. If you enable Fresh Animations, install EMF as well; it is not part of this pack yet.

## What's in here

- `pack.toml` and `index.toml` record the Minecraft and loader versions and the files Packwiz installs.
- `mods/`, `resourcepacks/`, and `config/` hold the shared pack definition. Packwiz records where to download each mod and resource pack; the downloads themselves are not committed here.
- `build/profiles.toml` defines explicit selections for client and server outputs; `scripts/build_pack.py` stages and exports them without changing root pack files.
- `tests/` covers recipe selection, inheritance, safety checks, and build isolation.
- `deploy/targets/` is reserved for settings that differ between the [main and creative servers](deploy/README.md). No differences have been confirmed yet.
- `docs/` has notes on [Packwiz tooling](docs/tooling.md) and [syncing local client data](docs/local-sync.md).

## Making changes

Make changes here first. After changing a config file or Packwiz metadata, run `packwiz refresh`, then review `packwiz list` and the Git diff. Keep worlds, player data, logs, backups, credentials, and private keys out of the repository. The [deployment notes](deploy/README.md) explain how shared settings and server-specific settings are meant to fit together.
