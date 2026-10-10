# Deployment targets

Blockery has one shared Packwiz definition and multiple Bloom deployment targets. Both targets receive the same Minecraft version, loader, mods, and shared configuration from the repository root.

Target directories contain only intentional differences. They must not duplicate the shared pack or contain runtime state.

```text
deploy/
└── targets/
    ├── main/
    └── creative/
```

The target names are working labels. Rename them when the Bloom server names are verified if different labels would be clearer.

## Overlay policy

When target-specific settings are collected, store reviewed templates or overlays under the matching target directory. Use names such as `server.properties.template` so live files containing secrets cannot be mistaken for safe repository content.

Suitable target variations include:

- default game mode and whether it is forced;
- difficulty, spawn protection, and message of the day;
- level name and other world-selection settings;
- target-specific mod configuration that has been deliberately reviewed.

Do not store Bloom credentials, server addresses that should remain private, RCON passwords, proxy secrets, Floodgate keys, worlds, player data, logs, or backups here.

## Future deployment flow

Deployment automation should build the common server pack once, install it into the selected Bloom split, and then apply that target's overlay. It must leave runtime worlds and target-owned state untouched.

No deployment command exists yet. Add one only after the Bloom connection and update process have been verified.
