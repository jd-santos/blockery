# Tooling

## Packwiz

Packwiz is a local build-time tool. It is not installed on either Bloom server
and is not required while Minecraft is running.

This pack was prepared with the following Packwiz build:

- Source: `github.com/packwiz/packwiz`
- Commit: `ef87d964f8cb`
- Go module version: `v0.0.0-20260906154125-ef87d964f8cb`
- Go toolchain: `go1.27.1 darwin/arm64`
- Output architecture: `darwin/arm64`
- SHA-256: `d3af7948dfdeb6ddf4d00817415543e171ac60eaed6faf2a405f2d299af34214`

Packwiz does not currently expose a version flag. Inspect an installed binary's
embedded module and toolchain information instead:

```sh
go version -m "$(command -v packwiz)"
shasum -a 256 "$(command -v packwiz)"
```

### Rebuild this version

To build the same revision into `$HOME/.local/bin`:

```sh
GOBIN="$HOME/.local/bin" go install github.com/packwiz/packwiz@ef87d964f8cb
```

Do not replace the pinned revision with `@latest`. To update Packwiz, choose and
record a new commit, build it locally, inspect its embedded module information,
and review the changes it produces in a disposable pack before adopting it here.

## Coordinated upgrades

The [upgrade guide](upgrades.md) describes report-first maintenance, temporary disabling,
release-set artifacts, recommended final checks, and manual backup/archive rollback.
Run `uv run --script scripts/validate_pack.py` for offline source/index/profile checks.
`scripts/upgrade_pack.py report` assesses chosen targets without changing pins;
`disable`/`enable` preview and confirm global exclusions in `build/disabled-mods.toml`.
The version `apply` command is intentionally unimplemented and refuses changes.
`scripts/audit_dependencies.py PROFILE --jars DIRECTORY --java 21` reads detached pinned
JARs without downloads or execution. It inventories nested Fabric providers and checks
supported metadata constraints, leaving resolver choices unknown. See the
[local JAR audit](upgrades.md#audit-locally-supplied-jars) for layout, target overrides and limits.
See the [upgrade guide commands](upgrades.md#commands) for examples and coverage.
Implementation progress and remaining work are in the
[maintenance work record](../todo/work/002-pack-maintenance/README.md).

## Distribution builder

Use Python 3.11 or newer through `uv`; the builder has no third-party Python dependencies.
Packwiz remains the exporter. The builder does not download or execute Minecraft, deploy
anything, or publish to Modrinth.

`build/profiles.toml` has four recipes: `blockery-client`, `blockery-extras-client`,
`blockery-server-survival`, and `blockery-server-creative`. Each declares:

- `name`: the output pack's display name.
- `side`: `client` or `server`, inherited if omitted.
- `extends`: an optional parent recipe. Client/server cross-inheritance and cycles fail.
- `mods`: explicit `.pw.toml` paths under `mods/` or `resourcepacks/`.
- `files`: explicit reviewed files under `config/`. No globbing or automatic config copying.
- `pending`: release blockers such as unfinished selections, config audits, or runtime tests.

Inheritance unions the parent's and child's selections and pending checks, preserving order
and removing duplicates. A child cannot remove parent entries. The global disable policy is
applied consistently after inheritance and preserves original metadata/pins; `plan` reports
excluded entries and their reasons. Blockery Extras Client adds extras to the lightweight
client base; creative can add verified differences to the common survival selection. A
variation that must remove something needs a separate explicit selection, not a copied pack.
Config overlays with destination remapping are not implemented yet.

Recipes preserve original mod side metadata and reject entries incompatible with their
side. New source mods are not silently added to recipes. Dependency closure and runtime
compatibility must be checked separately. Plans validate names and source paths without
reading config contents or copying files:

```sh
uv run --script scripts/build_pack.py list
uv run --script scripts/build_pack.py plan blockery-extras-client
```

Blockery Client (`blockery-client`) selects 13 mods and Redstone Tweaks: voice chat, small UI helpers,
Xaero's maps, MiniHUD, and the existing optimization entries. Fabric API and MaLiLib
supply required APIs; XaeroLib is nested in the map downloads. Blockery Extras Client inherits every Blockery Client
entry and adds JEI, Axiom, Litematica, Tweakeroo, Inventory Profiles Next, Fresh Animations,
and the other retained client entries. Blockery Extras Client totals 44 mods and two resource packs.
Inventory Profiles Next 2.2.4 uses the existing libIPN 6.6.2 and Fabric Language Kotlin
pins. Fresh Animations has EMF 3.3.12 and the existing ETF 7.2.4 available in Blockery Extras Client.

The other old client entries remain in Blockery Extras Client as carry-over, not as approval of every
client-side gameplay mod or config. Review them before release. View Distance Fix
remains in Blockery Client to preserve the existing loadout, but its server-focused fog behavior
is not evidence of a client FPS improvement. No new optimization mods were added.

Server recipes retain 30 mod entries plus 11 reviewed shared gameplay config files.
Creative inherits both selections from survival. The explicit server-only
Fabric Permissions API 0.5.0 pin satisfies WorldEdit's integration version check; it does
not install a permission manager or grant players permissions. Armor stand resizing is
operator-only. Client drafts still omit configs. The comment-only Lithium config, empty
No Chat Reports server preferences, and FerriteCore defaults are not bundled. Voice/audio
networking and upload paths, WorldEdit storage/permissions, and chat integration settings
remain target-specific review work, not implicit overrides. See the
[server audit](../todo/work/001-bloom-migration/server-audit.md) for selection evidence.
Survival's local player check is owner-confirmed, and its `2026.10.12` non-draft candidate
has passed exact archive, fresh-start, and pinned-restart checks. Other recipes remain gated.
Client defaults, keybindings, retained extras, and clean-instance behavior still need
review. MiniHUD rendering/overlay defaults have not been runtime-verified for either
new candidate. Target settings and Bloom deployment behavior still need verification
before real deployment.

```sh
uv run --script scripts/build_pack.py build blockery-client --version naming-preview --draft
uv run --script scripts/build_pack.py build blockery-extras-client --version naming-preview --draft
```

The earlier server draft commands remain useful with a fresh version label; the
existing preview archives are retained and cannot be overwritten.

Each command stages selected sources in a temporary pack, refreshes its own index, and
exports into ignored `local/dist/`. Every recipe also stages exact copies of root `LICENSE`
and `build/NOTICE.txt` as `blockery-notices/LICENSE.txt` and `blockery-notices/NOTICE.txt`.
These two non-runtime files carry GPL text, license scope, third-party references, and the
source repository link. They are fixed build inputs, not configurable recipe paths;
missing inputs and symlinks fail. `plan` lists their destinations separately as `notices`.
Root `pack.toml`, `index.toml`, metadata, configs, and notice sources are not modified. Existing output files are never overwritten; choose a new version.
If copying an export fails or is interrupted by Python, the builder removes its own
partial output so the same version can be retried. A forced process kill may still leave
a partial file; inspect it before manually removing it.
Draft filenames and manifest versions end in `-draft`. They are infrastructure checks,
not publishable or runtime-validated releases. Empty recipes cannot export.

After resolving all pending checks in a recipe and its ancestors, a normal build uses:

```sh
uv run --script scripts/build_pack.py build blockery-server-survival --version 2026.10.12
```

`2026.10.12` is the selected first Survival server release version. Its owner-confirmed
local player check cleared the last Survival gate, and the non-draft export is retained
at `local/dist/blockery-server-survival-2026.10.12.mrpack`. Existing outputs are immutable;
running the command again refuses to overwrite it. Creative retains its variation-review
gate, and both client recipes remain gated. Removing pending checks is a deliberate
release-preparation edit, not something the builder does automatically. A successful
export does not establish deployment safety or authorize publication.

Private/runtime filenames, traversal, and symlinks are rejected. Explicit config inclusion
is an allowlist, not a secret-content scanner: review contents before adding a path.
The builder supports the root pack's identity and Minecraft/loader fields; unsupported
root pack options fail instead of being silently discarded.

Run fixture tests without network calls or a Minecraft process:

```sh
uv run --no-project python -m unittest discover -s tests -v
```

### Client smoke test

Import each new `naming-preview-draft` archive into a separate new Prism instance,
not an existing instance. Use Java 21, launch to the title screen, and create a disposable
singleplayer world. The legacy expanded-client infrastructure smoke test does not validate these
new selections. Both drafts intentionally omit configs, options, server lists, map history,
voice settings, and personal Axiom settings. No existing instance is changed by the build.

- Confirm the selected mods load and server-only additions are absent. Blockery Client must have
  no JEI, Axiom, Litematica, Tweakeroo, Inventory Profiles Next, or Fresh Animations.
- Check AppleSkin, shulker previews, status timers, both maps, and MiniHUD. Verify MiniHUD
  starts without expensive overlays enabled, and that map/voice/MiniHUD shortcuts are
  usable without collisions. Approve or revise defaults based on the actual instance,
  not the unbundled legacy configs.
- Enable Redstone Tweaks manually and check readability. In Blockery Extras Client, optionally enable
  Fresh Animations and check animated entities with its included EMF/ETF support.
- In Blockery Extras Client, check JEI, inventory sorting, and the specialist tools. Confirm Blockery Client's features
  remain available. Axiom's separate multiplayer authorization still applies.
- Compare responsiveness while exploring with maps active and when toggling MiniHUD
  overlays. Performance claims need actual hardware testing, not a mod count.
- Verify voice chat against an authorized compatible test server. Multiplayer checks
  must not change Bloom or imply permission to use a live world as a test environment.

Report errors using short non-sensitive excerpts, not full logs. Keep both normal
client releases gated until the exact candidates and any approved config changes pass.

No Bloom or world-migration test is needed to commit the builder. Real server startup,
config audits, updates, and rollback remain requirements for deployment, not evidence
provided by these local exports.

Builder sources, recipes, tests, Python caches, and Ruff caches are excluded from root
Packwiz exports. Run `packwiz refresh` after changing indexed sources or exclusions.
