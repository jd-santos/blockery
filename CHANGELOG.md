# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
This project does not currently declare a Semantic Versioning policy.

## Unreleased

### Added

- Add the initial Minecraft 1.21.10 Fabric pack with pinned mods, reviewed configuration, and two client resource packs.
- Add a guide for syncing local client data between devices.
- Add server-only Better Fabric Console, its Adventure Platform dependency, and Inhabitor for both deployment targets.
- Add uv/Python build recipes for Blockery Client, Blockery Extras Client, and survival/creative server outputs, with draft release gates and isolated exports.
- Pin server-only Fabric Permissions API 0.5.0 to resolve WorldEdit's permissions integration warning.
- Include GPL text, scoped third-party notices, and a source link in every recipe export.
- Add client-only Inventory Profiles Next 2.2.4 and EMF 3.3.12 to Blockery Extras Client, using the existing libIPN, Kotlin, and ETF dependencies.
- Add offline pack integrity checks and read-only Minecraft/Fabric/mod candidate reports. Version application remains unimplemented; temporary global mod exclusions preview a diff and require interactive confirmation while retaining pins.
- Add read-only CI checks, four draft exports, archive audits, checksums, and seven-day candidate artifacts, without publishing or deployment.
- Document coordinated upgrades, recommended final testing, and manual rollback using retained pack archives and Bloom backups.

### Changed

- Name the client distributions Blockery Client (`blockery-client`) and Blockery Extras Client (`blockery-extras-client`), keeping Blockery as the umbrella name and server identities unchanged.
- Record Fabric Loader 0.19.5 as the shared pack loader.
- Select 11 reviewed shared gameplay configs for both server drafts and restrict armor stand resizing to operators.
- Keep personal Axiom settings and generated No Chat Reports encryption data outside the public pack.
- License original Blockery material under GPL-3.0-or-later while preserving third-party terms.
- Clear Survival's local release checks after owner-confirmed player validation and prepare the non-draft `2026.10.12` candidate; client and Creative releases remain gated.
- Populate the lightweight Blockery Client with voice chat, UI helpers, maps, MiniHUD, Redstone Tweaks, and existing optimization entries. Blockery Extras Client inherits it and adds specialist tools and visuals; both remain config-free drafts pending clean-client checks.
