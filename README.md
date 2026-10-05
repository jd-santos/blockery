# Blockery

Git and Packwiz will be the source of truth for the desired Minecraft pack configuration. One shared pack supports multiple Bloom deployment targets. This repository is separate from their live server directories and will not contain running worlds or other server runtime state.

## Distribution plan

- **Servers:** build the shared pack from this repository, review it locally, then deploy it to the main and creative Bloom targets. Apply target-specific settings afterward.
- **Clients:** export the client pack from Packwiz and use Modrinth as the primary install and update experience for friends.
- **Fallback:** offer a Packwiz Installer-based instance for people who use a compatible launcher and do not use Modrinth.
- **Bedrock:** if Bedrock access is added, run Geyser and Floodgate on the server side. Keep Floodgate's private key out of Git.

The Minecraft version, mod loader, and Bloom deployment method are not set yet. Initialize Packwiz after choosing the version and loader, then import existing mods and configs after reviewing them for secrets and runtime data.

## Repository layout

- `pack.toml`, `index.toml`: Packwiz metadata and indexed file manifest (created by `packwiz init`).
- `mods/`: Packwiz mod metadata files. Use Packwiz side settings to distinguish client, server, and shared mods.
- `config/`: configuration files intentionally managed as part of the pack.
- `resourcepacks/`, `shaderpacks/`: optional client assets managed by the pack.
- `deploy/targets/`: reviewed settings that differ between the main and creative Bloom targets. Shared pack content does not belong here.
- `docs/`: operating notes and decisions that should travel with the repository.
- `CONTEXT.md`: canonical language for the pack, deployment targets, and runtime state.
- `.packwizignore`: files that belong in the repository but must not be installed into a Minecraft instance.
- `AGENTS.md`: repository context and constraints for AI-assisted work.

## Working rules

1. Make changes here first. Do not edit the live Bloom server as the source of truth.
2. Keep world saves, logs, backups, crash reports, player/admin state, credentials, and private keys out of Git.
3. Review imported config files before adding them. Redact or replace credentials, tokens, webhook URLs, and private endpoints.
4. Update Packwiz's index after manually adding or editing indexed files: `packwiz refresh`.
5. Test server and client builds before publishing or deploying changes.

## Deployment targets

The main server and creative sandbox are separate Bloom server splits that receive the same pack. Their worlds and operational state remain independent.

```text
shared Packwiz server build
├── main target + main overlay
└── creative target + creative overlay
```

Only intentional differences belong in a target overlay. See [`deploy/README.md`](deploy/README.md) for the current layout and rules.

## Getting started

After deciding on the Minecraft version and loader:

```sh
cd ~/Repos/blockery
packwiz init
```

Then add mods and configs through Packwiz, review changes with Git, and build the client distribution for Modrinth. Deployment and publishing instructions will be added after the Bloom workflow and hosting location are confirmed.

## Security check before sharing

Before making the repository public, inspect tracked files for credentials and private runtime data. If a credential was committed, rotate it; deleting it in a later commit does not remove it from Git history.
