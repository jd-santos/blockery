# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
This project does not currently declare a Semantic Versioning policy.

## Unreleased

### Added

- Add the initial Minecraft 1.21.10 Fabric pack with pinned mods, reviewed configuration, and two client resource packs.
- Add a guide for syncing local client data between devices.
- Add server-only Better Fabric Console, its Adventure Platform dependency, and Inhabitor for both deployment targets.
- Add uv/Python build recipes for Blockery, Blockery Pro, and survival/creative server outputs, with draft release gates and isolated exports.
- Pin server-only Fabric Permissions API 0.5.0 to resolve WorldEdit's permissions integration warning.

### Changed

- Record Fabric Loader 0.19.5 as the shared pack loader.
- Select 11 reviewed shared gameplay configs for both server drafts and restrict armor stand resizing to operators.
- Keep personal Axiom settings and generated No Chat Reports encryption data outside the public pack.
