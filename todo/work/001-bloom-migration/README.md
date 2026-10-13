---
status: in_progress
---

# Bloom migration and remote updates

## Purpose

Verify that the repository defines the required server mods, then validate a remotely
fetched installation and repeatable update process on the newly created third Bloom
split before migrating survival or creative. Avoid recreating staging when the updater
is introduced.

## Decisions and boundaries

- The user confirmed the exported client pack works in Prism and local conversion is complete.
- Survival and creative already run on Bloom; the new split is empty. Treat it as the
  eventual deployment destination, not a disposable server. Keep it stopped while preparing
  installation; use local validation first and a separate temporary world for its pack boot.
- Agent API access is deferred. Do not request credentials or configure remote access now.
- The user reports Minecraft 1.21.10 and Fabric Loader 0.19.5 in the existing server settings,
  matching `pack.toml`. The older sandbox JAR filename is not proof of the running version.
  Confirm actual startup output before migrating worlds.
- Prefer a hosted pack and updater over manually uploading a complete instance.
- The existing Blockery distribution is the player-facing client pack. Server deployment
  artifacts/configuration are distinct outputs, potentially one each for survival and
  creative. Do not label the current combined validation export a finished server release.
- Preserve one shared source of truth without duplicating complete packs per target.
  Explicit distribution/profile selection must distinguish client content from server
  content and reviewed target variations. Creative-only mods and survival omissions
  remain undecided.
- The default player-facing `blockery` client pack should be minimal. The expanded
  loadout is named `blockery-pro` and will be separately available. Selection should
  distinguish broadly useful mods from specialist tools, but individual membership
  (including MiniHUD) is deferred until client release preparation. Blockery is also
  the umbrella repository/project name, not shorthand for the full client loadout.
- The user approved a small Python build layer managed through `uv`. Profiles are
  repository build recipes, not a native Packwiz feature. Packwiz supports client/server
  side metadata and optional mods, but does not provide named profile inheritance.
  Implement explicit recipes and isolated generated packs without changing root sources.
  Client membership and config approvals can remain pending while infrastructure is built.
  [Packwiz metadata reference](https://packwiz.infra.link/reference/pack-format/mod-toml/)
- Prefer separate Modrinth client projects for minimal and full loadouts rather than
  interleaving them as releases in one update stream. Modrinth's
  [content rules](https://modrinth.com/legal/rules) distinguish direct linear upgrades
  from files with different functionality. No project creation or upload is authorized.
- Keep production intact while testing staging with a disposable world, then a private copy.
- Do not publish, change live settings, transfer private state, or cut over without the
  user's authorization for those operations.
- Parent owns repository writes. The earlier read-only commit audit found no pending
  changes before this migration record was created.

## Repository evidence

After the approved additions, the pack has 45 mod entries: 26 marked `both`, 16 marked
`client`, and 3 marked `server`. Server selection includes 29 entries. This is metadata
validation, not a verified dedicated-server boot.

The selected entries are AppleSkin, Architectury API, Armor Poser, AudioPlayer,
Axes Are Weapons, Axiom, Bookshelf Inspector, Cloth Config API, Collective,
Coord Finder, Fabric API, Fabric Language Kotlin, FallingTree, FerriteCore,
Just Enough Items, Just Mob Heads, Just Player Heads, Lithium, No Chat Reports,
Text Placeholder API, Shulker Drops Two, Silence Mobs, Simple Voice Chat,
Styled Chat, View Distance Fix, and WorldEdit. The three server-only additions are
Adventure Platform, Better Fabric Console, and Inhabitor.

The index also contains client-oriented configs. Mod side filtering does not by itself
prove configs/resource packs are filtered appropriately. Inspect the exported server
contents and test them rather than assuming every indexed file belongs on the server.

The user supplied survival's 27 mod filenames and cautioned that old versions may be
outdated or incompatible. Treat them as evidence of installed features, not versions to
copy or proof of current compatibility. Creative's supplied 27 filenames match survival
exactly. Both targets therefore retain the same mod list for now. The user approved adding
the three missing projects to the shared server selection.

### Survival comparison

Before the three additions, filename/project comparison against the original 26
server-selected repository entries found:

- 24 projects in common: 11 identical filenames and 13 different filenames. Identical
  filenames are not proof of identical file contents or compatible releases.
- Survival-only: `adventure-platform-fabric-6.7.0.jar`,
  `better-fabric-console-mc1.21.10-1.2.7.jar`, and
  `inhabitor-fabric-1.21.10-1.0.6.jar`.
- Repository-only: Fabric Language Kotlin and Text Placeholder API. Verify dependency
  requirements rather than removing them merely because no standalone old JAR is listed.
- Different filenames: Architectury API, Armor Poser, AudioPlayer, Axiom,
  Bookshelf Inspector, Cloth Config API, Collective, Fabric API, FerriteCore,
  Just Enough Items, Lithium, Simple Voice Chat, and WorldEdit.
- Identical filenames: AppleSkin, Axes Are Weapons, Coord Finder, FallingTree,
  Just Mob Heads, Just Player Heads, No Chat Reports, Shulker Drops Two,
  Silence Mobs, Styled Chat, and View Distance Fix.

[Better Fabric Console](https://modrinth.com/mod/better-fabric-console) documents
server-side console improvements and an Adventure Platform dependency. Evaluate both
as a pair if retaining the console mod, including compatibility with Bloom's web console
and the proposed launcher. Dependencies of the exact AudioPlayer/Styled Chat releases
remain unverified; do not assume Adventure is required by them.

[Inhabitor](https://modrinth.com/mod/inhabitor) provides chunk inhabited-time tools
for world pruning and a related tracking fix. The approved additions are Better Fabric
Console 1.2.7, Adventure Platform 6.7.0, and Inhabitor 1.0.7. Packwiz resolved these
for the pack's Minecraft version, and their exact Modrinth version records all declare
Minecraft 1.21.10 and Fabric support. Console requires Adventure Platform and Fabric API;
Adventure Platform requires Fabric API, which is already present. All three new entries
are restricted to `server` so they are not installed by clients. This validates release
metadata and listed dependencies, not runtime behavior.

## Survival runtime inventory

The user supplied a root-directory listing, not the contents of `mods/`.

- `Vicious Blockery 1.21.10/` is a candidate world directory. Confirm it matches
  `level-name` without collecting the full `server.properties` file.
- `audioplayer_uploads/` is candidate mod-owned runtime state to preserve and test
  alongside AudioPlayer configuration. It must not become a distributed pack asset.
- `ops.json`, `whitelist.json`, and both ban lists need private migration review.
- `config/` needs selective review rather than wholesale replacement or copying.
- `better-fabric-console/` suggests another component to check against the mod list;
  the folder alone does not establish that its mod is currently installed.
- Existing dated archives are rollback candidates, not proof of a current complete backup.
- `.cache/`, `.fabric/`, `libraries/`, and `versions/` are regeneration candidates;
  logs, crash reports, and console history are not pack inputs.

Explicitly review protection for the actual world path and `audioplayer_uploads/`
before testing updater preservation. Do not rely only on protection of `world/`.

## Hosted installation candidate

[Patbox's mrpack4server](https://github.com/Patbox/mrpack4server) documents operation
as a custom server JAR, fetching a Modrinth pack or remotely hosted `.mrpack`, and
installing/starting Fabric. This fits the visible Bloom `Server Jar File` setting
without requiring an arbitrary startup script. It is a candidate, not a tested or
adopted dependency. Choose and record a specific launcher release before installation.

The upstream GitHub API reports [0.5.1](https://github.com/Patbox/mrpack4server/releases/tag/0.5.1)
as the latest non-prerelease, published 2026-08-31. This direct check supersedes search
excerpts showing 0.5.0 as latest. Release notes include a fix for `server-overrides`.
The project has public source under MIT and is maintained by [Patbox](https://github.com/Patbox),
a Fabric mod developer. This establishes a credible candidate, not a security audit or
proof of correct Bloom operation. Evaluate the pinned 0.5.1 code before running it.

Pack hosting means a downloadable release artifact, not another rented game server.
Modrinth or static HTTPS storage could provide it; neither has been chosen or published.

[Packwiz's Modrinth export](https://packwiz.infra.link/tutorials/hosting/modrinth/)
preserves declared mod sides. Native hosted Packwiz installation is another option
if Bloom confirms a supported pre-start hook or custom startup command.

The launcher documents explicit `project_id` and `version_id` configuration and a
URL override. Prefer pinned releases and deliberate promotion over latest-on-restart.
External hosting and Modrinth publication remain undecided. Publishing permissions
and distribution safety must be checked before making the pack public.

The launcher documents protected paths and additional `lockedpaths.txt` entries;
its default protected world path is `world`. Custom world names and mod-owned state
need explicit review. Overwrite protection is not proof of removal behavior or backup.

[Bloom backups](https://docs.bloom.host/backups) support locked backups, downloads,
and restoration to another split. Record panel Java, startup, ports, and server type
separately because file backups do not establish preservation of panel settings.

## Build-layer scope

- Recipes select explicit metadata and reviewed config paths from the shared sources.
  Generated packs and exports belong under ignored `local/`, not in target source trees.
- `blockery-pro` can inherit the client base; both server recipes can reuse one server
  selection. Do not inherit client configuration into server outputs.
- Keep the minimal selection undecided and preserve the current full client mod selection
  as a draft Pro recipe. No config is implicitly copied or approved by inventorying it.
- Pending recipes must refuse normal release builds. Explicit draft builds are for
  infrastructure checks, not publication or claims of runtime compatibility.
- Validate recipe inheritance, mod sides, confined paths, private/runtime-file exclusions,
  source immutability, and generated pack/export selection with local tests.
- No Modrinth upload, Bloom changes, launcher execution, or world transfer in this slice.

## Work

- [x] Finish the uv/Python recipe builder slice.
  - [x] Implement explicit same-side inheritance, isolated staging, path checks, and draft gates.
  - [x] Document names, usage, release blockers, and deferred membership/config decisions.
  - [x] Run fixture tests, active diagnostics, real draft exports, and source-immutability checks.
  - [x] Resolve fresh correctness/design review findings.
- [x] Inventory repository mod side declarations and identify a fixed-JAR hosted installer candidate.
- [x] Obtain filename-only mod inventories from survival and creative and classify missing,
  extra, version-different, and target-specific entries. Do not collect secrets or full server dumps.
- [ ] Verify side declarations, server dependencies, exported server files, and compatibility.
- [ ] Establish client/server output conventions and client profile boundaries before
  release cleanup. Keep the player-facing Blockery identity separate from server
  deployment releases; settle default/full/minimal client scope and visibility.
- [ ] Prepare a publishable pack: choose a release version instead of `unreleased`, review
  the 56 shared override files for intended distribution and client/server placement, verify
  content permissions, and test the exact candidate in a clean client and local server.
- [ ] Choose hosting/publication and a pinned updater release after checking distribution permissions.
  For Modrinth, prepare project summary/description, categories, license, optional icon/support
  links, and version metadata/changelog. Obtain publication authorization before uploading.
  Generate the separate Bloom launcher configuration only after the release IDs/URL are known.
- [ ] Verify a clean remote install on staging, including actual Minecraft/loader versions.
- [ ] Verify repeat starts remain pinned and a deliberate release update works without recurring mod uploads.
- [ ] Test mod addition/removal, config overwrite behavior, runtime-state preservation, download
  failure behavior, effective heap settings, console input, and graceful panel Stop/Restart.
- [ ] Verify backup restoration and record rollback procedure and required panel settings.
- [ ] Inventory worlds, access lists, target settings, identity/proxy setup, mod-owned state,
  and private integrations needed for migration. Never have staging write to production databases.
- [ ] Test a consistent copied world privately, with correct player identity and target behavior.
- [ ] Obtain cutover authorization, preserve a final rollback copy, and migrate the selected target.
- [ ] Update deployment operating docs with the verified install/update/rollback process.

## Validation and next input

The uv/Python builder is implemented in `scripts/build_pack.py`, with recipes in
`build/profiles.toml` and fixture tests in `tests/test_build_pack.py`. All 12 unittest
cases passed after review fixes. Active LSP checks of the script, tests, and TOML recipe reported no
findings. Real draft exports under `local/dist/` passed archive checks: Pro contains
44 download entries (client mods plus two resource packs); survival and creative each
contain 29 server mod entries. All preserve Minecraft 1.21.10 / Fabric 0.19.5 and use
an `infrastructure-preview-draft` manifest version. None include config overrides or
build/repository files. Root pack/index/source metadata hashes were unchanged by all
three builds. All four normal release builds refused while pending decisions remain.
Root `packwiz refresh` and `git diff --check` passed. Fresh correctness and design
reviews found no blockers. Their low-priority extension-case and partial-copy cleanup
findings were fixed: bundled binary/metadata suffix checks are case-insensitive, and
failed/interrupted copying removes only the newly created output. Regression tests
cover uppercase suffixes, copy failures, Python interruption, and successful retry.
Tests, active script/test diagnostics, and diff checks passed after the fixes. Reviewers
inspected code/docs; command and archive validation evidence came from the parent.
The commit audit found Ruff cache files in the root Packwiz index. Added explicit Git
and Packwiz Ruff-cache exclusions, refreshed the index, and rechecked that caches and
builder/workbench files are not indexed. The draft recipe exports were already isolated
and unaffected. Fixture tests and diff checks passed again during commit preparation.
Manual Prism smoke-test instructions are in `docs/tooling.md`; no user test is claimed.

Minimal/Pro membership can wait until the first client release; it does not block
server build infrastructure. Config audits and dependencies still block real server
deployment. Existing full client metadata remains in the Pro draft, not discarded.

Local TOML parsing established the metadata counts above. Modrinth API records verified
the three added releases' declared Minecraft/Fabric compatibility and listed dependencies.
`packwiz refresh` and an export to ignored `local/Blockery-server-validation.mrpack`
succeeded. Checks passed for pack/index/mod hashes, Minecraft/loader pins, all three new
mods' `client: unsupported` / `server: required` export flags, task-file exclusions, and
`git diff --check`. Fresh correctness and design reviews found no blockers in the
additions. The design review's baseline-count clarification was applied here. Reviews
inspected repository metadata and docs; API/export checks were parent-provided evidence.

Read-only inspection of `local/Blockery-server-validation.mrpack` found format version 1,
Minecraft 1.21.10 / Fabric 0.19.5, and version ID `unreleased`. All 47 download entries use
`cdn.modrinth.com` and include SHA-1/SHA-512 hashes. No mod JAR or resource-pack ZIP is
bundled in overrides; Axiom is also a Modrinth download. The archive has 56 files under
shared `overrides/`, with no client/server override folders. This is not a complete review
of config contents or permissions. No launcher JAR or Bloom configuration has been prepared.

[Packwiz's publishing guide](https://packwiz.infra.link/tutorials/hosting/modrinth/)
requires exporting `.mrpack`, not a separate repository-level Modrinth config file.
[Modrinth's permissions guide](https://support.modrinth.com/en/articles/8797527-obtaining-modpack-permissions)
explains that exact files hosted on Modrinth are eligible for use in Modrinth modpacks;
review other bundled content separately and meet any applicable conditions.

No dedicated-server boot, remote installation, updater release, mod removal, rollback,
or world migration has been tested. The older root export has not been regenerated.

Both target mod lists and the retention decision are now available. Remaining checks
include existing mod compatibility/dependencies and choosing hosted distribution before
staging installation. Settings reported by the user should later be corroborated by
startup output.

## Bounded work packets

- Inventory and side/dependency validation: focused change [context: small].
- Hosted install and lifecycle/update verification: subsystem cluster [context: medium].
- Runtime migration and rollback rehearsal: subsystem cluster [context: medium].

These packets describe future scope, not authorization to launch agents or change production.
