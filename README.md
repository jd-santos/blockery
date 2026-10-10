# Blockery

Blockery is a Minecraft 1.21.10 pack using Fabric Loader 0.19.5. Packwiz manages the mods, resource packs, and shared configuration for clients and the planned main and creative Bloom servers. Worlds, player data, and other runtime files stay outside this repository.

## Import into Prism Launcher

Install the [pinned Packwiz build](docs/tooling.md), then run this from the repository root:

```sh
packwiz refresh
packwiz modrinth export -o Blockery-unreleased.mrpack
```

In Prism Launcher, choose **Add Instance → Import** and select `Blockery-unreleased.mrpack`. This creates a new instance. Check its Resource Packs screen after import: Fresh Animations is included as a download, but needs Entity Model Features (EMF) to work, and EMF is not in this pack.

Personal schematics, map data, and Axiom settings are not in the export. See [Local Minecraft sync](docs/local-sync.md) for the folders to carry between devices.

## Repository layout

- `pack.toml` and `index.toml`: Minecraft and loader versions, plus the Packwiz file index.
- `mods/` and `resourcepacks/`: download metadata. Mod files declare whether they belong on the client, server, or both.
- `config/`: reviewed settings shared through the pack.
- `deploy/targets/`: settings specific to the planned [main and creative Bloom targets](deploy/README.md). No target differences are confirmed yet.
- `docs/`: [Packwiz tooling](docs/tooling.md) and [local sync](docs/local-sync.md) instructions.
- `CONTEXT.md`: definitions used in the deployment design.

Make pack changes here first. After changing indexed files, run `packwiz refresh` and inspect the result with `packwiz list` and Git. Keep credentials, private keys, server addresses, worlds, player state, logs, and backups out of the repository. The generated No Chat Reports encryption file and personal Axiom settings are explicitly ignored.

## Distribution and servers

Modrinth is the planned client distribution path. The `.mrpack` above is available for local Prism imports now; this pack has not been published on Modrinth.

The main and creative Bloom targets are intended to receive the same server pack, followed by their own reviewed settings. A deployment command has not been defined. Bedrock access through Geyser and Floodgate is a possible later addition, not part of this pack.
