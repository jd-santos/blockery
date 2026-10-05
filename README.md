# Blockery

Git and Packwiz will be the source of truth for the desired Minecraft pack configuration. This repository is separate from the live server directory hosted by Bloom. It will describe what to install and configure; it will not contain the running world or other server runtime state.

## Distribution plan

- **Server:** build from this repository, review locally, then deploy the intended server files to Bloom.
- **Clients:** export the client pack from Packwiz and use Modrinth as the primary install and update experience for friends.
- **Fallback:** offer a Packwiz Installer-based instance for people who use a compatible launcher and do not use Modrinth.
- **Bedrock:** if Bedrock access is added, run Geyser and Floodgate on the server side. Keep Floodgate's private key out of Git.

The Minecraft version, mod loader, and Bloom deployment method are not set yet. Initialize Packwiz after choosing the version and loader, then import existing mods and configs after reviewing them for secrets and runtime data.

## Repository layout

- `pack.toml`, `index.toml`: Packwiz metadata and indexed file manifest (created by `packwiz init`).
- `mods/`: Packwiz mod metadata files. Use Packwiz side settings to distinguish client, server, and shared mods.
- `config/`: configuration files intentionally managed as part of the pack.
- `resourcepacks/`, `shaderpacks/`: optional client assets managed by the pack.
- `deploy/`: reviewed build/deployment scripts for Bloom, once its workflow is known.
- `docs/`: operating notes and decisions that should travel with the repository.
- `.packwizignore`: files that belong in the repository but must not be installed into a Minecraft instance.
- `AGENTS.md`: repository context and constraints for AI-assisted work.

## Working rules

1. Make changes here first. Do not edit the live Bloom server as the source of truth.
2. Keep world saves, logs, backups, crash reports, player/admin state, credentials, and private keys out of Git.
3. Review imported config files before adding them. Redact or replace credentials, tokens, webhook URLs, and private endpoints.
4. Update Packwiz's index after manually adding or editing indexed files: `packwiz refresh`.
5. Test server and client builds before publishing or deploying changes.

## Getting started

After deciding on the Minecraft version and loader:

```sh
cd ~/Repos/blockery
packwiz init
```

Then add mods and configs through Packwiz, review changes with Git, and build the client distribution for Modrinth. Deployment and publishing instructions will be added after the Bloom workflow and hosting location are confirmed.

## Security check before sharing

Before making the repository public, inspect tracked files for credentials and private runtime data. If a credential was committed, rotate it; deleting it in a later commit does not remove it from Git history.
