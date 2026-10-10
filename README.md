# Blockery

Blockery is a Minecraft modpack for friends playing together. It keeps the game version, mods, resource packs, and shared settings in one place so everyone can start with a compatible setup.

The current pack uses **Minecraft 1.21.10** and **Fabric Loader 0.19.5**. It can be imported into Prism Launcher now. The same pack is intended for the main and creative Bloom servers, with each server's own settings kept separate. Server deployment and Modrinth publishing are still being set up.

## Try the client pack

Packwiz can export this repository as a `.mrpack` file that Prism Launcher understands. Install the [pinned Packwiz build](docs/tooling.md), then run these commands from the repository root:

```sh
packwiz refresh
packwiz modrinth export -o Blockery-unreleased.mrpack
```

In Prism Launcher, choose **Add Instance → Import** and select `Blockery-unreleased.mrpack` to create a new instance.

Fresh Animations is included as a resource pack, but it needs Entity Model Features (EMF) to work. If you enable Fresh Animations, install EMF as well; it is not part of this pack yet.

## What's in this repository

- `pack.toml` and `index.toml` record the Minecraft and loader versions and the files Packwiz installs.
- `mods/`, `resourcepacks/`, and `config/` hold the shared pack definition. Packwiz records where to download each mod and resource pack; the downloads themselves are not committed here.
- `deploy/targets/` is reserved for settings that differ between the [main and creative servers](deploy/README.md). No differences have been confirmed yet.
- `docs/` has notes on [Packwiz tooling](docs/tooling.md) and [syncing local client data](docs/local-sync.md).

## Working on the pack

Make changes here first. After changing a config file or Packwiz metadata, run `packwiz refresh`, then review `packwiz list` and the Git diff. Keep worlds, player data, logs, backups, credentials, and private keys out of the repository. The [deployment notes](deploy/README.md) explain how shared settings and server-specific settings are meant to fit together.
