# Coordinated pack upgrades

Blockery uses one shared Packwiz source for both clients and both server recipes.
Upgrade that source once, then build each distribution from the same revision.
Matching source pins prevent drift; they do not establish runtime compatibility.

The first maintenance slice provides source validation, read-only candidate reports,
confirmed temporary exclusions, local pinned-JAR dependency audits, and draft CI artifacts.
Applying Minecraft/Loader/mod
version changes is not implemented: the `apply` command exits with an error and changes
nothing. See the [maintenance work record](../todo/work/002-pack-maintenance/README.md)
for remaining work.

## Current hosting

The owner reports that a generated server pack is running on the host through
mrpack4server, temporarily using a GitHub Release while Modrinth review is pending.
Keep the installed release deliberately pinned. Approval on Modrinth does not require
a Minecraft upgrade: changing the download source can be a separate operation.

Packwiz runs while maintaining/building the pack, not on the running server. A Git
merge, a new candidate archive, or a successful CI run must not update the host.

## Propose before applying

An upgrade starts with an assessment of a chosen Minecraft and Fabric Loader target.
Report the current and proposed versions, affected distributions, available compatible
mod candidates, unavailable releases, and unknown compatibility. An unavailable entry
needs an explicit decision: wait, retain a verified compatible pin, replace it, or
intentionally disable it. Do not silently keep an incompatible old version.

Assessment must not change canonical pack files. Before applying any implemented
change, show the exact proposal and require confirmation. If a proposal was saved,
reassess after changing its inputs rather than applying a stale report. A successful
metadata lookup or archive export is not a runtime test or dependency proof.

### Commands

```sh
# Offline integrity and recipe checks. No network access or source changes.
uv run --script scripts/validate_pack.py

# Assess the current platform. Substitute a chosen target when ready.
uv run --script scripts/upgrade_pack.py report --minecraft 1.21.10 --fabric 0.19.5
uv run --script scripts/upgrade_pack.py report --minecraft 1.21.10 --fabric 0.19.5 --online --json
```

Without `--online`, compatibility is explicitly `unknown`. Online mode queries public
Modrinth and Fabric metadata, selects the newest published matching release, and reports
required Modrinth dependency references per distribution. Add `--include-prerelease` to
consider beta/alpha candidates. `unavailable` means no match under that policy, not proof
that no compatible prerelease exists. `candidate` does not guarantee an upgrade over the
current pin or approval to install it. Lookup failures remain unknown, with errors shown.

Disabled entries are reported with reasons and are not queried or re-enabled. Online
results do not inspect downloaded JARs, nested providers, Fabric version predicates,
optional incompatibilities, or gameplay. Required project/version references that cannot
be established are listed for review, not silently resolved. Reports are informational:
command success means assessment completed, not that every entry is compatible. Inspect
the statuses and dependency findings before choosing changes.

### Audit locally supplied JARs

Use a detached download directory, not a live client/server instance. Supply the pinned
filenames recorded in selected `mods/*.pw.toml`, directly under that directory. For example,
`local/audit/jars/fabric-api-<pinned-version>.jar`. Extra files are ignored, not discovered
as additional providers. Resource packs and disabled entries are not read as mod JARs.
The audit does not download missing files, extract archives, execute mods, or write reports.

```sh
uv run --script scripts/audit_dependencies.py blockery-server-survival --jars local/audit/jars --java 21
uv run --script scripts/audit_dependencies.py blockery-client --jars local/audit/jars --java 21 --json
```

Each selected JAR must match its canonical SHA-256/SHA-512 pin before its root
`fabric.mod.json` and recursively declared nested JARs are inspected. Sources identify
nested provenance, for example `mods/example.jar!/META-INF/jars/library.jar`. Only Fabric
schema v1 is supported. Environment filtering follows the selected client/server recipe;
`provides` aliases use their provider's version. Unselected files cannot satisfy dependencies.

The platform defaults to the Minecraft and Loader versions in `pack.toml`. Optional
`--minecraft` and `--fabric` arguments assess those same pinned JARs against a chosen target;
they do not select or fetch the online report's candidates. Supply the intended `--java`
version explicitly, otherwise Java constraints remain unknown. Minecraft snapshots and
other versions needing game-provider normalization are not guessed.

The audit checks `depends` and `breaks` as hard constraints, reports `recommends` and
`conflicts` as warnings, and retains `suggests` as information. Supported Fabric predicates
include numeric comparisons, zero-padded component comparison, prereleases, ignored build
metadata (including punctuation such as `10+!`, which Fabric permits), space-separated AND,
array OR, caret/tilde ranges and major/minor X-ranges.
Fabric caret behavior is not npm's special handling for `0.x`. Arbitrary string equality
is supported where unambiguous; unsupported syntax, bounded-parser limits and extended
X-ranges such as `1.2.3.x` remain unknown rather than approximated. Build suffixes
containing whitespace also remain unknown in this bounded parser, even though Loader
permits arbitrary build contents.

Inspect the overall status **and individual findings**:

- `checked`: implemented metadata checks completed without hard violations or unknowns.
  Warnings can still be present. This is not a launch test, compatibility guarantee or release approval.
- `violated`: a selected top-level mod has a demonstrated hard constraint failure.
- `unknown`: missing/mismatched/malformed evidence, unsupported predicates, or unresolved
  selection prevents a conclusion. One incomplete selected JAR makes provider absence uncertain.

Nested JARs are candidate providers, not assumed simultaneously loaded. Their dependency
checks are conditional, and competing versions/aliases remain unknown. The report shows
candidate version matches but does not choose a resolver solution. Only the first 16
providers are repeated in a finding, with the full `provider_count`; the candidate inventory
remains available. These limits prevent large ambiguous inventories from inflating reports.

Reads are bounded (128 MiB per JAR, 512 MiB inspected bytes per audit, 1 MiB per metadata
file, depth eight, plus entry/candidate/constraint/alias caps). Symlinks, unsafe member paths,
duplicate ZIP members/JSON keys and unsupported compression are rejected. Central-directory
records are counted before `ZipFile` allocates entry objects; forged counts cannot bypass
the cap. ZIP64 central directories, multi-disk archives and prefixed/trailing layouts remain
unsupported and produce unknown evidence. A rejected subtree
is not retained as a partially trusted provider. Hash verification is not a full ZIP payload
or runtime audit. Dependency overrides, entrypoints, mixins, bytecode/API compatibility,
Fabric's complete resolver and gameplay remain outside this command.

Like `report`, command success means a report was produced, not that the pack passed.
Bad source/index integrity or invalid invocation fails the command; evidence gaps are
reported as unknown. This audit does not clear recipe gates or add a new CI release gate.

Semantics are grounded in the [Fabric v1 specification](https://wiki.fabricmc.net/documentation:fabric_mod_json_spec)
and Loader 0.19.5's [metadata parser](https://github.com/FabricMC/fabric-loader/blob/0.19.5/src/main/java/net/fabricmc/loader/impl/metadata/V1ModMetadataParser.java),
[version predicates](https://github.com/FabricMC/fabric-loader/blob/0.19.5/src/main/java/net/fabricmc/loader/impl/util/version/VersionPredicateParser.java)
and [comparison operators](https://github.com/FabricMC/fabric-loader/blob/0.19.5/src/main/java/net/fabricmc/loader/api/metadata/version/VersionComparisonOperator.java).
Loader's [numeric version parser](https://github.com/FabricMC/fabric-loader/blob/0.19.5/src/main/java/net/fabricmc/loader/impl/util/version/SemanticVersionImpl.java)
explicitly permits arbitrary build contents and ignores build metadata in comparisons.
The audit deliberately supports a subset; for example, non-string environment declarations
are unknown even though older wiki prose permits arrays.

### Underlying Packwiz updates

Packwiz supplies the underlying migration/update operations:

```sh
# Illustrative placeholders, not a selected upgrade target.
packwiz migrate minecraft <minecraft-version>
packwiz migrate loader <fabric-loader-version>
packwiz update --all
```

Use these only as part of a reviewed upgrade branch, not on the host. They are not a
single atomic upgrade transaction. Review the Git diff and account for skipped,
pinned, unavailable, newly required, or unsupported entries. `update --all` also
covers metadata retained for temporarily disabled entries; do not assume that a
build-time exclusion makes Packwiz skip it. The assessment tool skips disabled entries;
a future version-application engine must preserve that distinction too.

## Temporary disabling

Temporarily disabling a mod is a selection decision, not deleting its pin. Retain
its metadata and record why it is disabled so a later report can revisit it. The
first implementation uses a global policy: each distribution that selected the
entry omits it. This keeps the base and Extras client relationship consistent.

The persistent policy is `build/disabled-mods.toml`. These illustrative commands use a
real metadata path, but do not disable anything unless you confirm in a terminal:

```sh
uv run --script scripts/upgrade_pack.py disable mods/axiom.pw.toml --reason "Waiting for chosen target support"
uv run --script scripts/upgrade_pack.py enable mods/axiom.pw.toml
```

Both commands print the policy diff, affected distributions, and a dependency/world
warning, then require the exact response `yes`. Redirected/noninteractive input is
refused. Changes to source inputs during confirmation invalidate the request. The
commands change only the policy, not `.pw.toml` pins, recipes, or live installations.
No entries are disabled in the initial policy. Normal root Packwiz exports bypass this
policy as well as recipe gates; use the distribution builder.

Associated config allowlists are not automatically rewritten. Review any remaining
configs and required dependencies before publishing a pack with exclusions. Offline
validation cannot establish dependency safety, and a cleared release gate does not
become fresh approval of an exclusion.

Do not automatically disable dependents or re-enable a mod because a new upstream
version appears. Report any required dependency affected by the decision and resolve
it before considering the pack compatible. Libraries may still be needed by other
mods. Removing a content mod can affect world data even when the pack starts.

## Build and release together

Use the existing [distribution builder](tooling.md#distribution-builder), not a root
export that bypasses recipe selection. Build all affected outputs from the reviewed
source revision. Keep current client/Creative release gates unless their checks have
actually been resolved.

A coordinated release set should identify:

- The source revision and shared Minecraft/Fabric Loader versions.
- Each included distribution and its pack version.
- The exact archive checksum and download location.
- Temporarily disabled entries and other compatibility decisions.

Separate Modrinth projects have separate version IDs. They can still belong to one
release set. CI candidate artifacts are temporary test downloads, not public
releases or a stable production download endpoint. The explicit
[release workflow](tooling.md#prepare-an-official-pack) builds one gated distribution
and attaches its archive, checksums and source manifest to a draft GitHub release.
Test those bytes and publish the same draft without rebuilding. A gated distribution
must not be silently promoted just because another one is ready. Modrinth publishing
and host deployment remain manual.

Installed clients do not update merely because new archives exist. Give players the
matching base or Extras client candidate and an explicit launcher update/import path.
Do not tell them to update individual mods independently of the released pack.

## CI candidates

`.github/workflows/validate.yml` runs fixtures and source validation on pull requests,
pushes to `main`, and manual dispatch. Only pack/build-related PRs or a manual run with
`build_drafts` selected export the four drafts, audit archives and check source immutability.
Documentation/skill-only PRs and main pushes do not produce candidate artifacts.
The jobs use read-only permissions and pinned actions, Python 3.11 and, when building,
Go 1.27.1 with the documented Packwiz revision. See [CI routing](tooling.md#ci-checks-first-packs-when-needed).

The uploaded artifact contains only the four draft `.mrpack` files, `SHA256SUMS`, and
`ci-report.json`, retained for seven days. The audit checks ZIP safety/CRC, identities,
shared platform versions, selected download paths, declared download URLs/hashes/sides,
and exact override bytes. It does not download JARs or prove their dependency/runtime
compatibility. CI does not publish releases, clear pending checks, or contact the host.

To perform the archive audit locally after building all four drafts with the same label:

```sh
uv run --no-project python -m scripts.check_exports --version <draft-label-without-suffix>
```

## Before changing the host

Keep a known-good pack archive and its source/version/checksum, launcher selection,
and any required Java/startup settings. For a Minecraft upgrade, also preserve a
consistent pre-upgrade backup of the world and other target-owned state using Bloom.
Include custom world paths, mod-owned uploads, and access/config state where relevant.
Keep those backups and private settings outside Git and public CI artifacts.

Stop the server before the final consistent backup and update. Record which backup
matches which pack, and retain it through the upgrade. A backup job reporting success
is useful evidence; knowing where the backup is and how to restore it makes it usable.

## Recommended final testing

Testing depth should fit the change. These are practical recommendations, not a
requirement to build a separate mrpack4server test platform:

1. Run automated validation and inspect changed/disabled entries and unresolved
   warnings. Review all affected distributions, not only the server selection.
2. Launch each affected client candidate. Check that it reaches the title screen
   and can join a compatible test server. Keybinding and visual polish can be
   handled separately, but a candidate that cannot load/join is not validated.
3. For a server/Minecraft upgrade, prefer a private copied-world check. Confirm
   startup, basic gameplay, expected mod behavior, and clean save/stop. Do not have
   a copied server write to production integrations or the original world.
4. After the deliberate hosted update, check actual Minecraft/Loader versions,
   console errors, joining, expected functionality, and save/stop. Decide whether
   to keep the upgrade or roll back before accumulating much new world progress.

These checks are recommendations until performed. Neither CI nor this guide
claims that a candidate was gameplay-tested.

## Manual rollback

1. Stop the upgraded server. Retain its current state separately if needed for
   investigation; do not overwrite the known-good pre-upgrade backup.
2. Restore the previous pinned pack/launcher selection and matching runtime backup.
   Use Bloom's restore controls for the chosen backup and restore required startup
   settings separately if they changed. A filesystem backup may not include panel
   settings. Do not assume changing the pack URL removes every upgraded file.
3. For a Minecraft version rollback, restore the pre-upgrade world. Do not open a
   world saved by the newer version with the older server and expect a safe downgrade.
4. Start the restored server, check actual versions and basic gameplay, and tell
   players to use the matching client release. Record which release remains active.

Restoring a pre-upgrade backup discards progress since that backup. Pack archives
alone cannot undo changes made to worlds, generated configuration, or mod-owned data.

References: [Packwiz commands](https://packwiz.infra.link/reference/commands/packwiz/),
[mrpack4server](https://github.com/Patbox/mrpack4server), and
[Bloom backups](https://docs.bloom.host/backups).
