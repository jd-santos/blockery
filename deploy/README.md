# Deployment targets

Blockery has shared Packwiz sources and multiple Bloom deployment targets. Server build
recipes select metadata/configs from those sources; player clients are separate outputs.
`blockery-server-survival` selects the shared server mod list, and
`blockery-server-creative` inherits that selection. Both currently have pending config
and runtime checks, so their exports are drafts, not deployment-ready packs.

The existing `main/` directory corresponds to survival. It has not been renamed.
The creative directory remains `creative/`. These target directories are not complete
pack copies or player client profiles.

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

The local builder composes each server output from shared sources and its explicit
recipe. Target templates/overlays are not automatically included yet; their selection
and destination handling need review before implementation. Never inherit client configs
into a server output merely because they exist at the repository root.

Future deployment automation should install the selected pinned server output and apply
reviewed target settings. It must leave runtime worlds and target-owned state untouched.
See [tooling](../docs/tooling.md#distribution-builder) for local draft export commands.

No remote deployment command exists yet. Add one only after the Bloom connection and
update process have been verified.
