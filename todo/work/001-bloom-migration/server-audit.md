# Server dependency and config audit

## Scope and evidence

Audit the current survival recipe and the identical inherited creative selection before
local startup. No production files, server credentials, worlds, or remote settings were
accessed. The dependency/config review was static. A later isolated local installer and
Loader preflight was run with `eula=false`. After the user accepted the Minecraft EULA
for disposable local testing, both corrected outputs passed fresh-world startup and
console shutdown. These stages are recorded below.

The initial 29 pinned Modrinth version records declare Minecraft 1.21.10 and Fabric support.
Each selected download URL and SHA-512 matched its exact version record. Downloaded
JARs were hash-verified before reading their `fabric.mod.json` metadata and recursively
reading declared nested JAR metadata. This dependency evidence is static, not a complete server behavior or security review.

The ignored `local/audit/` directory contains public version records, verified JARs,
and extracted Fabric metadata. It is disposable audit evidence, not runtime state or a
new pack source. Reproduce the audit from the version IDs and download hashes in the
recipe's selected `.pw.toml` files, not from an upstream latest-version query.

## Initial dependency findings

- The 29 top-level JARs contain 144 Fabric metadata entries including nested libraries.
  Excluding client-only entries leaves 135 entries, including duplicates. Every required
  server-visible dependency ID is supplied by the selected/nested mods or by Minecraft,
  Java, and Fabric Loader. ID presence does not establish Loader resolution or runtime safety.
- Non-wildcard inter-mod requirements are met by the supplied versions: Cloth Config
  20.0.149 meets Armor Poser's `>=20`; Collective 8.13 meets `>=8.8`/`>=8.9`; Fabric API
  0.138.4 meets the listed `>=0.91`, `>=0.127.0`, and `>=0.137.0` requirements;
  Voice Chat API 2.6.24 meets `>=2.6.0`.
- The selected Fabric API is newer than the `<0.134.1+1.21.10` versions explicitly
  rejected by AudioPlayer, Coord Finder, Inhabitor, Simple Voice Chat, and View Distance Fix.
- The highest declared minimum Loader version is 0.19.5, required by Fabric Language
  Kotlin. Keep the current Loader pin. The highest declared Java minimum is 21.
- Nested duplicates include Cloth Config, Placeholder API, Admiral, and Fabric API modules.
  Fabric Loader must resolve these in the local boot. Do not delete shared dependencies
  merely because another mod embeds an older copy.

### Releases needing filename clarification

| Pin | Exact JAR evidence | Consequence |
| --- | --- | --- |
| [Axes Are Weapons 1.9.4](https://api.modrinth.com/v2/version/IgfXr6Py) | Requires Minecraft `>=1.21.5`, Cloth Config, and the `fabric` alias provided by Fabric API. | Its `1.21.5` filename does not exclude 1.21.10. No replacement is justified by the filename alone. |
| [Styled Chat 2.10.0](https://api.modrinth.com/v2/version/ub8BCtuy) | Requires Minecraft `>=1.21.2-alpha.24.33.a` and Loader `>=0.15.10`; embeds Placeholder API and other libraries. | The `1.21.9` filename is not an incompatibility finding. Its Fabric metadata does not require Adventure Platform. |
| [AudioPlayer 2.4.1](https://api.modrinth.com/v2/version/qHG6nngD) | Requires Minecraft 1.21.10 and `voicechat_api >=2.6.0`. | Simple Voice Chat supplies the required API. Its Fabric metadata does not require Adventure Platform. |
| [Bookshelf Inspector 2.3](https://api.modrinth.com/v2/version/pQMFOXad) | Modrinth lists Mod Menu as required; the JAR's `depends` does not. Its Mod Menu integration is a separate entrypoint. | Do not add client-only Mod Menu to the server based on the project-level dependency listing. Confirm dedicated-server startup. |

Minecraft predicates such as Architectury's `~1.21.7` and Bookshelf Inspector's
`~1.21.9-beta.1` are ranges, not exact-version pins. The exact Modrinth records list
1.21.10. Loader's resolver and server execution remain the final startup checks.

## Reviewed config candidates

These repository files were read for this audit. The user reviewed the candidates and
requested operator-only armor stand resizing. That change is applied to the shared
`config/armorposer.toml`; all other reviewed settings remain unchanged. Routine file
selection can proceed from this review without asking for approval of each setting.
The survival recipe now selects 11 shared gameplay config files; creative inherits them.
The empty No Chat Reports server preferences, comment-only Lithium config, and FerriteCore
performance defaults remain unbundled. Client recipes still omit configs. This review is
not evidence of current production settings.

| Candidate | Relevant behavior or disposition |
| --- | --- |
| `config/axesareweapons.json5` | Enables Looting for axes and enchanting-table integration; other weapon classes remain disabled. |
| `config/bookshelfinspector-config.yml` | Enables lectern behavior; scale/roman settings also affect presentation. Confirm server consumption in the boot. |
| `config/collective.json5` | Shared dependency settings, including drop enumeration and entity replacement behavior. |
| `config/fallingtree.json` | Instantaneous whole-tree breaking, maximum 100 blocks, normal durability cost, sneaking disables it, and creative breaking is off. |
| `config/justmobheads.json5` | Uses per-mob chances; Looting is enabled and player kills are not required. |
| `config/justmobheads/headchances.txt` | Custom per-mob chance table. Keep with the main Just Mob Heads config if selected. |
| `config/justplayerheads.json5` | Player deaths always drop a head. |
| `config/shulkerdropstwo.json5` | Drops two shells when the drop occurs; `alwaysDropShells` is false. This is not a guaranteed two-shell drop per kill. |
| `config/silencemobs.json5` | Silence Stick command is cheat-gated; requires a held stick and renames affected mobs. |
| `config/NoChatReports/NCR-Common.json` | Does not require the client mod; converts chat to game messages. Not the private encryption file. |
| `config/NoChatReports/NCR-ServerPreferences.json` | Empty signing-mode map. Consider leaving to mod defaults. |
| `config/armorposer.toml` | Includes client settings. The user requested `restrictResizeToOP = true`, now applied to the shared source. Verify enforcement during server testing. |
| `config/ferritecore.mixin.properties` | Performance settings plus client/model settings; risky small threading detector stays disabled. Prefer mod defaults unless overrides are intentional. |
| `config/lithium.properties` | Comments only, with no overrides. Omit rather than copying a no-op file. |

Do not copy client UI, minimap, schematic, rendering, or personal tool configs into server
outputs. Keep voice/audio networking, upload paths, WorldEdit storage/permissions, and
chat integration review separate. Files that may contain credentials or private endpoint
settings must be inspected by the user, not collected as full dumps. No contents of
AudioPlayer/Voice Chat server properties, WorldEdit properties, or Styled Chat config were
read in this audit.

## Remaining deployment checks

1. Keep the 11-file shared gameplay allowlist separate from target-specific settings;
   do not copy all root configs or import private live configuration.
2. Review target networking, upload/storage paths, WorldEdit permissions, and chat
   integration requirements. Local-only test settings are not deployment settings.
3. Test actual player gameplay and operator/non-operator permissions in disposable local
   sessions, including armor stand resizing. Startup is not proof of feature behavior.
4. Verify installer helper pinning, repeat pinned starts, deliberate updates, lock/removal
   semantics, protected custom runtime paths, download failures, and backup/rollback.
5. Obtain publication/deployment authorization separately. Test the Bloom environment
   before considering private world migration or cutover.

The user confirmed the Pro draft Prism smoke test looks good. It does not satisfy any
of the server startup or configuration checks above.

## Pinned installer and local preflight

The [mrpack4server 0.5.1 release](https://github.com/Patbox/mrpack4server/releases/tag/0.5.1)
was downloaded to ignored local audit storage, not adopted for Bloom. The standard JAR
has SHA-256 `67629c5c573c899bd896b2d48d6b6921d6980aaae93c302ba3f335609335a7d5`, matching
GitHub's release digest. Its manifest reports 0.5.1 and its main class uses Java 21 bytecode.
The pinned public source was inspected before execution.

Relevant source findings, not a full launcher security audit:

- [Main](https://github.com/Patbox/mrpack4server/blob/0.5.1/src/main/java/eu/pb4/mrpackserver/Main.java)
  installs and then launches in the same JVM. No install-only branch was found; `nogui`
  is passed through. JVM heap flags apply to this local in-process launch.
- [FabricInstallerLookup](https://github.com/Patbox/mrpack4server/blob/0.5.1/src/main/java/eu/pb4/mrpackserver/installer/FabricInstallerLookup.java)
  chooses the current stable Fabric installer for a fresh install. Minecraft and Loader
  are pinned by the pack, but this helper is not independently pinned. This test selected
  Fabric installer 1.1.2. Record/rehearse this behavior before claiming reproducible deployment.
- [Constants](https://github.com/Patbox/mrpack4server/blob/0.5.1/src/main/java/eu/pb4/mrpackserver/util/Constants.java)
  protects `world`, not every custom world/upload directory. Explicit custom locks remain
  required for production paths.
- [MrPackInstaller.cleanupLeftoverFiles](https://github.com/Patbox/mrpack4server/blob/0.5.1/src/main/java/eu/pb4/mrpackserver/installer/MrPackInstaller.java)
  does not consult the lock set when removing previously managed files. Test lock/removal
  interaction with synthetic data before trusting it to preserve target-owned state.

The ignored sandbox is `local/server-smoke/survival-gameplay-config-preview/`. It contains
an exact copy of the new survival draft as `local.mrpack`, the verified launcher as
`server.jar`, and newly authored local-only test settings. Minecraft binds to loopback
port 25575; Voice Chat is configured for loopback UDP 24465. RCON/query are disabled,
the whitelist is enabled, and the intended world is `disposable-smoke-world`. No live
server settings were imported. EULA remains false; no acceptance was made for the user.

The launcher was run with Java 21, `-Xms512M -Xmx2G`, and `nogui`. Environment-injected
JVM options were excluded so they could not bypass the EULA gate. It installed all 29
selected mods, and initialization reported Minecraft 1.21.10 / Fabric Loader 0.19.5.
All installed top-level mod hashes match their source pins. All 11 shared configs remained
byte-identical to their reviewed sources after initialization. No disposable world directory
was created. The process remained alive after the EULA message and was terminated at the
180-second bound (exit 143). This is not a clean shutdown or successful world boot.
No listener remained on the two intended local test ports afterward.

### Runtime finding: WorldEdit permissions

WorldEdit 7.4.0-beta-01 warned that `fabric-permissions-api-v0` 0.4.2-patbox.1 is unsupported
and fell back to Minecraft permissions. Static disassembly of the pinned WorldEdit JAR
shows an integration check for API `>=0.5.0`, absent from its required Fabric dependency
metadata. The fallback checks operator status, with additional WorldEdit cheat-mode and
creative-access configuration switches; it is not safe to assume fine-grained permission
nodes still apply. The resolution below removes the fallback warning; permission behavior
still has not been tested with players.

### Resolution and corrected fresh-world tests

Added an explicit server-only [Fabric Permissions API 0.5.0 pin](https://api.modrinth.com/v2/version/6lShH56u),
project `lzVo0Dll`. This exact release declares Minecraft 1.21.9/1.21.10 and Fabric support.
Its JAR declares `fabric-permissions-api-v0` 0.5.0, Loader `>=0.17.0`, Minecraft `>=1.21.9`,
and `fabric-api-base`, already supplied by the selected Fabric API. The download's SHA-512
matches Modrinth metadata. Packwiz initially generated `side = "both"`; it was deliberately
set to `server` to match the project's server-required/client-unsupported declarations.
This is a library, not a permission manager, and adds no player grants. Client recipes do
not select it. Runtime Loader selection confirms 0.5.0 supersedes the older nested copy.

The corrected server drafts each have 30 exact pinned downloads (26 both-side and four
server-only), the same 11 byte-identical shared config overrides, Minecraft 1.21.10 / Fabric
0.19.5, and no extra packaged files. Both normal releases remain blocked. Exporting left
all shared pack/index/mod/config source hashes unchanged.

| Exact ignored artifact | SHA-256 |
| --- | --- |
| `local/dist/blockery-server-survival-permissions-api-preview-draft.mrpack` | `a993e1c14fa087dcec605696d644638151bfbebf0d5ad823d19744fb6e7a1362` |
| `local/dist/blockery-server-creative-permissions-api-preview-draft.mrpack` | `8ffef25f887cfcb6f9d59c818110b7279bdf86f4e626ef2522f4834affb7665f` |

After the user accepted the Minecraft EULA for this disposable test, new isolated local
sandboxes were created with `eula=true`. Production and the initial EULA-gated sandbox
were not changed. The local harness is retained in ignored `local/audit/run_local_smoke.py`;
export receipts are in `local/audit/permissions-preview-exports.json`. It verifies artifact
and launcher hashes, streams readiness, sends console commands, bounds runtime, and records
installed mod/config checks. It is not a repository deployment command.

The initial corrected survival run logged a flat-world generator-settings error caused by
the harness's incomplete local flat preset. It still started/stopped, but was not accepted
as the final result. Changed only local test settings to normal terrain, then installed
both exact artifacts into new, separate directories under `local/server-smoke/`:

- `blockery-server-survival-permissions-api-preview-normal/`
- `blockery-server-creative-permissions-api-preview-normal/`

Each directory retains `smoke-summary.json` and private `smoke-console.txt`. Do not commit
these, generated mod configs, access lists, or test worlds. Local settings use survival or
creative mode respectively, but they do not approve production target differences.

Both corrected runs reached `Done`, created separate `disposable-smoke-world/level.dat`
files, answered `list` with zero players and `worldedit version` with 7.4.0-beta-01, accepted
`stop`, saved players/worlds, and exited 0 without forced termination. Runtime was 36.6
seconds for survival and 35.1 seconds for creative. Loader selected Permissions API 0.5.0;
WorldEdit's permissions fallback warning disappeared. All 30 installed top-level mod hashes
matched the source pins, and all 11 selected configs remained byte-identical. Live process
socket checks showed Minecraft only on loopback TCP 25575 and Voice Chat only on loopback
UDP 24465. No error lines were reported in the corrected normal-terrain runs.

Both normal-terrain sandboxes were then started a second time without changing pack
artifacts or rewriting local settings. Each retained the pinned pack and all 30 mod
hashes, selected API 0.5.0, and produced no installation/update branch message. Readiness,
console commands, saves, and exit 0 passed without forced termination, with no error lines
or selected config changes. Loopback-only listeners were confirmed again. Runtime was
18.0 seconds for survival and 17.8 seconds for creative. The same directories retain
separate `restart-summary.json` and private `restart-console.txt`; initial smoke evidence
was not overwritten. This demonstrates local cached pinned restarts, not remote hosting
or deliberate update/removal behavior.

All 15 unit tests, active changed Python/TOML checks, canonical pack/index/selected-source
hash checks, exclusion checks, and `git diff --check` passed. The single fresh follow-up
correctness/design review round found no blockers. Reviewers inspected source/metadata,
docs, and permitted JSON summaries, not private logs or live gameplay; runtime and command
validation were performed by the parent. No publication, Bloom changes, or private
state transfer occurred in this slice.

Warnings remained for Armor Poser's missing mixin refmap and the redirected non-TTY
terminal. Neither prevented startup, console input, or shutdown. Do not assume the refmap
warning is harmless for gameplay until armor stand behavior is exercised. No clients joined,
so operator-only resizing, permission nodes, mod gameplay, voice/audio, and cross-client
compatibility remain unverified. The tests do not validate Bloom panel Stop/Restart,
remote artifacts, updates, rollback, or migrated worlds.
