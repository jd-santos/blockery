---
status: in_progress
pr: https://github.com/jd-santos/blockery/pull/2
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
- Prepare Blockery Server Survival for Modrinth first, for use with Bloom. Minimal and
  Pro client release preparation can wait. The user approved preparing the listing and
  distribution review, not uploading, configuring Bloom, or migrating runtime state.
  Draft copy and publication evidence are in [Modrinth release preparation](modrinth-release.md).
- Describe the pack's intended audience as a small, private, whitelisted friends-and-family
  server, not a public server listing. The artifact does not enforce or include a whitelist.
  Disclose AI assistance with Packwiz configuration, Python tooling/tests, dependency checks,
  deployment preparation, and writing, including the required Modrinth content-disclosure
  setting. Do not imply that hosted migration has happened or that AI created the upstream mods.
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

The current pack has 46 mod entries: 26 marked `both`, 16 marked `client`, and 4 marked
`server`. Both server recipes select 30 entries and 11 reviewed gameplay config files.
Local fresh-world startup and console shutdown passed for both exact server drafts.
The owner confirmed completion of the linked local player check and authorized clearing
Survival's gate. The non-draft `2026.10.12` Survival candidate passed exact payload,
fresh-start, pinned-restart, and save/stop checks; see [release evidence](modrinth-release.md#non-draft-candidate).
Deployment validation remains open.

The selected entries are AppleSkin, Architectury API, Armor Poser, AudioPlayer,
Axes Are Weapons, Axiom, Bookshelf Inspector, Cloth Config API, Collective,
Coord Finder, Fabric API, Fabric Language Kotlin, FallingTree, FerriteCore,
Just Enough Items, Just Mob Heads, Just Player Heads, Lithium, No Chat Reports,
Text Placeholder API, Shulker Drops Two, Silence Mobs, Simple Voice Chat,
Styled Chat, View Distance Fix, and WorldEdit. The three server-only additions are
Adventure Platform, Better Fabric Console, and Inhabitor. An explicit Fabric Permissions
API 0.5.0 server-only pin was subsequently added to satisfy WorldEdit's undocumented
integration requirement; it is not a permission manager.

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
and the proposed launcher. The later exact-release audit found that AudioPlayer/Styled
Chat JAR metadata does not require Adventure Platform; see the [server audit](server-audit.md).

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
without requiring an arbitrary startup script. The pinned 0.5.1 candidate has passed
isolated local installation/start/stop checks, not Bloom or updater validation. It is
not adopted for deployment.

The upstream GitHub API reports [0.5.1](https://github.com/Patbox/mrpack4server/releases/tag/0.5.1)
as the latest non-prerelease, published 2026-08-31. This direct check supersedes search
excerpts showing 0.5.0 as latest. Release notes include a fix for `server-overrides`.
The project has public source under MIT and is maintained by [Patbox](https://github.com/Patbox),
a Fabric mod developer. This establishes a credible candidate, not a security audit or
proof of correct Bloom operation. The pinned 0.5.1 source was inspected before local
execution; unresolved helper-pinning and lock/removal behavior are in the server audit.

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
- [x] Record the user's successful Pro draft Prism smoke test.
- [ ] Verify side declarations, server dependencies, exported server files, and compatibility.
  - [x] Check all 29 exact Modrinth records, download hashes, and server-visible Fabric dependency IDs, including nested JARs.
  - [x] Review non-sensitive gameplay config candidates and record findings in the [server audit](server-audit.md).
  - [x] Record the user's review of the config candidates and apply operator-only armor stand resizing to the shared source.
  - [x] Implement the shared server config allowlist and verify both exact draft exports.
  - [ ] Assess remaining target-specific networking, storage, permission, and chat integration needs.
  - [x] Install the exact survival draft locally and confirm Minecraft/Loader pins at the EULA gate, without accepting the EULA or creating a world.
  - [x] Resolve WorldEdit's undocumented Permissions API `>=0.5.0` integration requirement with an explicit 0.5.0 server pin and repeat initialization.
  - [x] Obtain Minecraft EULA acceptance for the disposable local test and verify fresh-world startup and graceful shutdown for both exact server drafts.
  - [x] Verify player-facing gameplay and operator/non-operator permissions using the [local player check](modrinth-release.md#local-player-check); owner-confirmed completion and authorization to clear the gate, not independently observed by the agent.
- [ ] Establish client/server output conventions and client profile boundaries before
  release cleanup. Keep the player-facing Blockery identity separate from server
  deployment releases; settle default/full/minimal client scope and visibility.
- [ ] Prepare the Survival server release first; retain client release/config review as deferred work.
  - [x] Draft project fields, description, and server-specific version changelog in [Modrinth release preparation](modrinth-release.md).
  - [x] Revise the public copy for the private whitelisted audience, add specific AI-assistance disclosure and No Chat Reports behavior, and keep internal test provenance in the evidence sections rather than the listing.
  - [ ] Verify the actual Modrinth editor's server-side environment, AI content-disclosure setting, all 30 version dependencies, and Permissions results before submission; prepared copy does not verify account-side fields.
  - [x] Verify all 30 exact Modrinth-hosted downloads against the tested survival archive and confirm its 11 selected overrides with no bundled JARs/resource packs.
  - [x] Record GPL for original Blockery material, third-party terms for all third-party works including Axiom, and a normal release channel without a beta label.
  - [x] Confirm GPL-3.0-or-later and initial version `2026.10.12`, and add the scoped repository license declaration.
  - [x] Include exact GPL text, scoped third-party notices, and a source link in the licensed Survival draft; verify archive contents and installed notice bytes.
  - [x] Run 17 unit tests, active changed-file checks, and fresh-world/pinned-restart/save-stop tests of the exact licensed Survival draft.
  - [x] Complete fresh correctness/design review of notice staging and release documentation; clarify the player-permission gate, add its inherited-gate regression assertion, and pass the single design follow-up.
  - [x] Deliver the matching GPL-covered source revision and identify it in the version notes: [`3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f`](https://github.com/jd-santos/blockery/tree/3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f). The authorized topic-branch push and unauthenticated public access are verified; all artifact source inputs match that revision. This is source delivery, not Modrinth publication.
  - [x] Confirm Axiom whitelist status: the user still needs to request it; verified Modrinth-hosted file references can be published separately from runtime authorization.
  - [ ] Obtain the Axiom whitelist or applicable license before intended private multiplayer use; do not collect private identifiers.
  - [x] Verify the approved public shared-pack boundary: 30 mod references, 11 reviewed gameplay configs, and two notices; keep target-owned infrastructure/runtime settings outside the artifact and retain their Bloom deployment review separately.
  - [x] Prepare ordinary configuration-override disclosure and upstream permission evidence for Modrinth review without claiming a blanket config exemption.
  - [ ] Address any configuration permission evidence requested during the authorized Modrinth moderation process.
  - [x] Record the owner's local player-check confirmation, clear only Survival's gate, export non-draft `2026.10.12`, and verify its exact archive plus fresh-start/pinned-restart/save-stop behavior. All 18 unit tests pass; Creative and clients remain gated.
- [ ] Before client publication, finalize minimal/Pro selections, review the legacy 56 shared
  overrides for intended distribution/client placement, verify permissions, and test the
  exact named candidate in a clean client instance.
- [ ] Choose hosting/publication and a pinned updater release after checking distribution permissions.
  For Modrinth, prepare project summary/description, categories, license, optional icon/support
  links, and version metadata/changelog. Obtain publication authorization before uploading.
  Generate the separate Bloom launcher configuration only after the release IDs/URL are known.
- [ ] Verify a clean remote install on staging, including actual Minecraft/loader versions.
- [ ] Verify repeat starts remain pinned and a deliberate release update works without recurring mod uploads.
  - [x] Repeat local starts of both exact corrected server drafts; verify unchanged pins, no reinstall, and clean console shutdown.
  - [ ] Verify hosted/remote pinned starts and deliberate release updates.
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
Manual Prism smoke-test instructions are in `docs/tooling.md`. The user subsequently
confirmed the Pro draft test looks good. This confirms the reported client smoke test,
not final client membership, bundled configs, or dedicated-server compatibility.

The [server audit](server-audit.md) checked all 29 exact releases and hash-verified JARs,
including nested Fabric metadata. No required server-visible dependency ID is missing.
Modrinth's Bookshelf Inspector listing requires Mod Menu, but the JAR does not declare
it as a required dependency; do not add a client-only mod to the server on that basis.
Fourteen non-sensitive gameplay/config candidates were reviewed. The user reviewed them
and requested `restrictResizeToOP = true` in `config/armorposer.toml`. The shared source
now has that setting; no other config values changed. Routine selection can proceed from
this review without per-setting questions. Survival now selects 11 shared gameplay files;
creative inherits them. Client configs remain unselected. No-op Lithium, empty No Chat
Reports server preferences, and FerriteCore defaults remain unbundled. Target-specific
networking, upload/storage paths, permissions, and chat integration still need assessment.
The initial audit ran no downloaded code. The later local preflight is recorded below;
no live server was changed.

The two new `gameplay-config-preview-draft` server exports under `local/dist/` contain
29 exact pinned downloads and 11 byte-identical selected config overrides, with no extra
files. All original side flags are preserved: 26 both-side mods and three server-only mods.
Minecraft 1.21.10, Fabric 0.19.5, and operator-only armor stand resizing were verified in
both archives. Source hashes stayed unchanged during archive validation and creative
export. An initial archive-check assertion incorrectly expected every mod to be server-only;
corrected the check to compare against each source declaration, without changing metadata.
The survival artifact from that export passed the corrected checks; it was not overwritten.

All 14 unittest cases pass, including new real-recipe config inheritance/staging and
release-gate checks. Active checks of the changed Python/TOML files reported no findings.
The JSON language server reports 26 comment errors in existing JSON5 configs; these were
marked false positives because JSON5 allows comments. No mod config comments were removed.
Local Java is Azul Java 21.0.4. Fresh correctness/design reviews found no blockers in
the recipe/config slice. Reviewers checked sources/docs and archive member paths; they
did not independently run tests or decompress archive payloads. Parent-provided checks
established pins, byte equality, tests, diagnostics, and Git status.

An isolated ignored survival sandbox was prepared and mrpack4server 0.5.1's published
SHA-256 verified before execution. Its source was inspected. Installation and Fabric
initialization reported Minecraft 1.21.10 / Loader 0.19.5, installed all 29 exact mod pins,
and left all 11 shared config files byte-identical to the reviewed sources. EULA remained
false and no world directory was created. The process did not exit after the EULA gate;
it was terminated at the 180-second bound, not stopped gracefully. No listeners remained
on the intended loopback test ports. The [server audit](server-audit.md#pinned-installer-and-local-preflight)
records sandbox settings, launcher caveats, and the WorldEdit warning: its optional
Permissions API integration requires `>=0.5.0`, but Loader selected 0.4.2-patbox.1 and
WorldEdit fell back to Minecraft permissions. The explicit API pin recorded below
resolves that fallback; real player permissions still need testing.
That initial preflight made no new mod/version pin or EULA acceptance. The later corrected
local tests are recorded below; no updater adoption, remote action, or world migration
was performed.

The user then accepted the Minecraft EULA for disposable local tests only. Added
server-only Fabric Permissions API 0.5.0, Modrinth project `lzVo0Dll` / version `6lShH56u`,
a release declaring Minecraft 1.21.9/1.21.10 and Fabric support. Its download SHA-512 and
Fabric metadata were verified. Both new `permissions-api-preview-draft` exports contain
30 exact pinned downloads plus the same 11 byte-identical reviewed configs; four downloads
are server-only. Client recipe selections remain unchanged and all release gates remain.

Both exact corrected outputs installed into separate ignored local sandboxes, reached
`Done`, created separate disposable normal-terrain worlds, answered `list` and `worldedit
version`, and accepted console `stop`. Each saved players/worlds and exited 0 without
forced termination. Loader selected Permissions API 0.5.0 and the WorldEdit fallback
warning disappeared. Installed top-level JAR hashes and all selected config bytes matched
the source. Live socket checks showed only loopback Minecraft TCP 25575 and Voice Chat
UDP 24465. No players joined and no gameplay/permission enforcement test is claimed.
The initial corrected survival run used incomplete flat-world generator settings and
logged a generator error. The local-only harness was changed to normal terrain and both
outputs rerun in fresh directories, with no error lines. Armor Poser's missing-refmap
warning and the non-TTY terminal warning remained. Neither prevented start/stop; the
refmap warning still needs consideration during actual armor-stand behavior testing.

Both normal-terrain sandboxes were then restarted without rewriting settings or changing
artifacts. Each retained its exact pack/mod pins, selected API 0.5.0, reported no installer
rerun, answered console commands, saved, and exited 0 without forced termination. Loopback
listeners were verified again, all selected config bytes stayed unchanged, and no error
lines appeared. This is local cached restart evidence, not a hosted update or panel test.

All 15 unit tests passed after the new server-only dependency selection regression check;
active checks of the changed Python/TOML files and `git diff --check` passed. Canonical
pack/index and selected-source hashes and runtime/repository exclusions were rechecked.
The single fresh follow-up correctness/design review round found no blockers in the
Permissions API fix or local startup claims. Reviewers checked public metadata, recipes,
tests, docs, and permitted JSON runtime summaries; they did not independently run the
server/tests or inspect private logs. Exact archive hashes, runtime summaries, and remaining
validation are in the [server audit](server-audit.md).

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
of config contents or permissions. That legacy export was not paired with a launcher
configuration. The later ignored local sandbox uses the pinned launcher and `local.mrpack`;
no Bloom launcher configuration has been prepared.

[Packwiz's publishing guide](https://packwiz.infra.link/tutorials/hosting/modrinth/)
requires exporting `.mrpack`, not a separate repository-level Modrinth config file.
[Modrinth's permissions guide](https://support.modrinth.com/en/articles/8797527-obtaining-modpack-permissions)
explains that exact files hosted on Modrinth are eligible for use in Modrinth modpacks;
review other bundled content separately and meet any applicable conditions.

Fresh local dedicated-server world startup and console shutdown passed. The owner later
confirmed the local player check, permitting the non-draft Survival candidate recorded in
[release preparation](modrinth-release.md#non-draft-candidate). Remote installation,
updater releases/removals, rollback, and world migration have not been tested.
The older root export has not been regenerated.

Both target mod lists and the retention decision are now available. Remaining checks
include existing mod compatibility/dependencies and choosing hosted distribution before
staging installation. Settings reported by the user should later be corroborated by
startup output.

## Bounded work packets

- Inventory and side/dependency validation: focused change [context: small].
- Hosted install and lifecycle/update verification: subsystem cluster [context: medium].
- Runtime migration and rollback rehearsal: subsystem cluster [context: medium].

These packets describe future scope, not authorization to launch agents or change production.
