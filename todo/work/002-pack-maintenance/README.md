---
status: in_progress
pr: https://github.com/jd-santos/blockery/pull/4
---

# Coordinated pack maintenance

## Purpose

Maintain the client and server distributions together from the existing shared source.
Make proposed Minecraft, Fabric Loader, and mod upgrades understandable before changing
pins. Add small CI checks and draft artifacts without automating live updates.

## Decisions and boundaries

- The owner reports a generated server pack running on the host through mrpack4server,
  temporarily pinned to a GitHub Release while Modrinth review is pending. This is an
  owner-confirmed installation, not independently verified installed bytes or an update test.
- Reusable validation and an upgrade report are the priority. A proposed upgrade must
  report current and candidate pins, affected distributions, unavailable entries, and
  uncertainty before any source change is applied. Assessment is read-only by default.
- Any implemented apply operation must show its proposed changes and require explicit
  confirmation. Noninteractive execution must not imply consent. A saved plan, if supported,
  must not apply after its source inputs change or accept arbitrary replacement files.
- Temporary disabling keeps the original metadata and pins with a reason. Disabling is
  reversible, explicit, and visible in reports. The first policy may apply globally to
  every recipe selecting that entry, preserving base-to-extras inheritance. Do not silently
  disable dependents or automatically re-enable entries during updates. Warn about possible
  world effects when removing content mods; no automatic world migration is included.
- Keep the existing builder, explicit selections, one Minecraft/Loader source, and shared
  mod metadata. Do not create separate copies of each pack or a general dependency manager.
- It is acceptable to finish a bounded report-first foundation and explicitly defer the
  full upgrade apply engine or downloaded-JAR dependency audit. Stubs must refuse unsupported
  operations rather than report success. Document actual coverage and remaining work.
- CI should run tests, validate plans, build draft outputs with the pinned Packwiz revision,
  audit exports, and retain only intended candidate artifacts/reports. No publishing,
  deployment, production credentials, EULA acceptance, or live instance access is included.
- Rollback preparation belongs in a short manual playbook using retained pack archives and
  Bloom backups. Extensive mrpack4server-specific rehearsal is not a prerequisite for this
  maintenance tooling. Recommended testing goes at the end of the upgrade procedure.
- A coordinated release set should identify each artifact, source revision, Minecraft and
  Loader versions, and checksums. Public release automation is a later slice; candidate CI
  artifacts are not published releases. Promote tested bytes rather than rebuilding them.
- No actual Minecraft, Loader, mod pin, selection, or client configuration upgrade is
  authorized by this implementation request. Preserve release gates. The owner subsequently
  authorized committing ready work and shipping through a topic-branch PR if appropriate.
  Releases, host changes, and deletion of retained artifacts remain unauthorized.

## Ownership

The foundation merged in [PR #4](https://github.com/jd-santos/blockery/pull/4), with
[successful CI](https://github.com/jd-santos/blockery/actions/runs/38974744441).
The current dependency-audit slice is on `dependency-audit`, based on merged `origin/main`.
The parent is the sole repository writer; read-only correctness and design reviews
are complete, with final small corrections validated by the parent. Other worktrees and unrelated `research.md`
remain untouched. No pin changes, live-instance access, downloads, or deployment are
part of this slice.

## Acceptance criteria

- Reports distinguish current pins from candidates and known incompatibility from unknown
  support. No compatibility claim is based on a JAR filename or a successful export alone.
- Offline checks cover source/index integrity, recipe safety, and the implemented policy.
  Online checks, if implemented, have mocked tests and fail visibly on missing evidence.
- Assessment does not change pack inputs. Implemented mutations refuse absent confirmation
  and unsafe paths. Temporary disables retain pins and affect exports consistently.
- Existing builder commands remain compatible with an empty/absent disable policy. All
  existing and added tests pass. No runtime source pin or selected entry changes in this slice.
- CI uses read-only permissions, safe PR events, verified action pins, pinned Packwiz, and
  explicit artifact paths. It cannot publish, deploy, or clear a recipe gate.
- Maintained docs explain the real interfaces, scope of validation, temporary disables,
  upgrade path, recommended final testing, and a practical archive/backup rollback procedure.
- Correctness and design reviews inspect the integrated implementation. Local validation
  is distinguished from execution on GitHub Actions or a Minecraft client/server.

## Work

- [x] Record the approved scope, practical rollback approach, and disjoint worker lanes.
- [x] Implement and integrate the report-first upgrade/validation foundation.
- [x] Implement and integrate reversible temporary disabling without deleting metadata.
- [x] Implement and locally validate the small CI workflow and export audit.
- [x] Document actual commands and the coordinated upgrade path in `docs/upgrades.md`.
- [x] Add recommended final testing and a manual Bloom backup/archive rollback playbook.
- [x] Run integrated tests, safe current-source checks, diagnostics, and four draft export audits.
- [x] Obtain fresh correctness and design reviews of the integrated foundation.
- [x] Fix malformed API evidence handling and stale exclusion-preview checks; add regression
  fixtures and rerun local validation.
- [x] Complete the affected correctness follow-up, resolve its timestamp/dependency-type
  notes, and rerun local validation.
- [x] Commit the reviewed foundation with SSH signing and open a topic-branch PR.
  The unfinished implementation slices below remain in the live queue.
- [x] Add a read-only audit of locally supplied, hash-verified pinned JARs per recipe.
  - [x] Inspect Fabric schema-v1 metadata and recursively declared nested JARs without extraction.
  - [x] Evaluate required dependencies, breaks and warning-only constraints against active
    providers, aliases and explicit platform versions; preserve unknowns for resolver choices.
  - [x] Bound archive reads and reject unsafe paths, symlinks, malformed metadata and hash mismatches.
  - [x] Add fixtures for version predicates, nested/alias ambiguity, side filtering and read-only safety.
  - [x] Update maintained docs; run tests/static/source checks and correctness/design reviews.
- [ ] Extend audits to candidate downloads/plans and full resolver selection where needed;
  optionally query availability for disabled entries without re-enabling them. [context: medium]
- [ ] Implement confirmation-gated application of Minecraft/Loader/mod candidates with
  stale-input rejection and preserved disabled pins. The current `apply` stub refuses
  changes; assessment alone never upgrades source or a live instance. [context: medium]
- [ ] Make release validation specific to changed runtime inputs/final artifacts instead of
  treating an earlier cleared recipe gate as approval of future pins. [context: small]
- [ ] Add deliberate public artifact publication with a release-set manifest, checksums,
  exact tested bytes, and separate distribution identities. Preserve independent release
  gates; add Modrinth API publishing only if useful after project approval. [context: medium]
- [ ] Consider a repository-local agent skill after the maintained upgrade procedure and CLI
  have settled. A skill should reference the procedure, not duplicate or replace it. [context: small]

## Dependency-audit slice

`scripts/audit_dependencies.py PROFILE --jars DIRECTORY --java VERSION` reads selected pinned
mod filenames directly under a detached local directory. It does not fetch missing artifacts
or inspect a live instance. Platform overrides assess the same current pins against explicit
targets, not online candidate downloads. Canonical inputs and release gates are unchanged.
See [the maintained command reference](../../../docs/upgrades.md#audit-locally-supplied-jars).

Nested candidates and aliases have source provenance. Nested dependencies are conditional;
competing providers, unsupported evidence and incomplete inventories remain unknown. This
is an evidence audit, not a general solver. Archive, metadata, nesting, candidate, constraint,
alias and repeated-provider limits bound reads and report growth. Only schema v1 and the
documented subset of Fabric 0.19.5 predicates are claimed. Unsupported forms fail closed.

Local validation currently passes 75 tests (26 new), Ruff and fresh CLI Pyright. Active LSP
probes surfaced stale newly-created-module imports, contradicted by fresh Pyright and
executable imports/tests, plus regex-guarded numeric conversion warnings. Those were marked
false-positive with reasons, not hidden by source ignore comments.

A read-only run against retained `local/audit/jars` verifies all 30 pinned server JARs for
each server recipe and inventories 136 candidates each, including nested candidates. Neither
server report has a demonstrated hard violation; both remain unknown due resolver choices.
The client/Extras inventories have seven/18 missing pinned JARs respectively and remain
unknown, not compatible. No missing artifacts were downloaded and no retained file/report
was overwritten. This inventory run did not push, open a PR or execute Minecraft.

### Audit review dispositions

Design review `e9f7367c-e556-43bf-ba49-32ed6bb2c15e` found no issues (OK with notes).
Correctness review `9166c597-615b-45b7-9724-36026c102f35` raised two findings:

- Accepted: ZIP entry limits were enforced after `ZipFile` allocated the central-directory
  objects. A bounded preflight now counts actual central records before constructing
  `ZipFile`, validates ordinary single-disk layout, and rejects unsupported ZIP64 directory
  or prefixed/trailing layouts. Fixtures assert `ZipFile` is never called for oversized
  directories, forged small counts, malformed records and unsupported layouts.
- Invalid: rejecting build punctuation such as `10+!` would contradict
  [Loader 0.19.5's parser](https://github.com/FabricMC/fabric-loader/blob/0.19.5/src/main/java/net/fabricmc/loader/impl/util/version/SemanticVersionImpl.java).
  Its class contract explicitly permits arbitrary build contents; the constructor stores
  everything after the first `+`, and comparisons ignore it. Added audit-level fixtures for
  punctuation, empty and repeated-dot build suffixes, alongside an invalid-prerelease case.
  This is Fabric's extended grammar, not strict SemVer build validation.

All 75 fixtures and static/source checks pass after the preflight fix. The retained-JAR
inventory counts are unchanged. No second design round is needed. Deferred implementation
packets remain in the work list.

### Correctness follow-up and readiness

The owner authorized a Herdr fallback after native background review failed before startup
because the Pi host could not resolve `@earendil-works/chord` and its `context` subpath.
Failed runs `7cbca1de-1b84-43bb-9885-6c392d43bf23` and
`41e0d08a-6e36-402f-ae61-c31ae9204e9f` produced no review evidence; the original reviewer
was unavailable for resume. No host installation repair was attempted.

The owner supplied the completed read-only Luna follow-up from Herdr reviewer
`blockery-audit-review` (session `01a146fe-6dda-7782-b079-1636dd0b2c42`). It confirmed
that the allocation fix is sound on inspection and the `10+!` objection is invalid.
It identified one remaining layout check: central records could declare a nonzero
starting disk even with ordinary end-record disk fields. The parent added rejection of
nonzero per-entry disk starts before allocation, with disk-one and ZIP64-sentinel fixtures
that assert `ZipFile` is not called. The conservative whitespace build-suffix limitation
is now documented and covered by an audit fixture returning unknown. These small final
corrections were parent-validated, not independently re-reviewed. The agreed follow-up
round is complete; no broader hardening or additional review round is planned.

Fresh validation after those corrections passes all 75 tests, offline Ruff (including
an explicit import-order check) and fresh offline CLI Pyright for the three added Python
files, source validation for 106 indexed files/four profiles, and `git diff --check`.
Active LSP probes show no unsuppressed findings, with two files confirmed clean and one
inconclusive; five existing dispositions remain suppressed. Fresh CLI checks pass despite
an edit-time stale import-order warning. The reviewer inspected code/fixtures/docs but
did not run checks or fetch the linked Fabric source; execution evidence is the parent's.
The earlier stalled batch was aborted and replaced by individual bounded checks.

The audit slice has no known remaining blocker and is prepared for an owner-authorized
local commit on `dependency-audit`, based on `cebe72c`. The commit includes the three
Python files and five related documentation/work-record files. Canonical pack/index,
metadata, configs, recipes, disable policy and Packwiz exclusions have no diff. Unrelated
`research.md`, other worktrees and retained artifacts remain untouched. No push, runtime
test, publication or deployment is claimed. Deferred candidate-download/resolver/application
work remains in the work list; remote delivery is a separate step.

## Foundation validation

The integrated first slice passes 49 fixture tests and fresh Ruff/Pyright checks after
review fixes. Offline validation checks 106 indexed files and all four recipes. The prior
session verified `packwiz refresh` leaves canonical inputs unchanged; the resumed session
also verified no diff in pack/index, pins/configs, or selections. The policy has no disabled
entries. Four `maintenance-preview-20261016-1-draft` exports pass ZIP/CRC, identity/platform,
selected paths, declared URLs/hashes/sides, exact notice/config bytes, and checksums.
Ignored evidence: `local/dist/ci-report.json` and `local/dist/SHA256SUMS`. The submitted
Survival archive retains SHA-256 `c0d7bce2204c8abb04abe67a9339b92f0fb53a806c13ea259d2d8bd9ad01319a`.

Fresh active LSP probes report no diagnostics for the six changed Python source/test paths.
All four retained draft exports were audited again without overwriting archives or reports.
The pinned Packwiz binary matches the documented revision/checksum, and the four action
pins match their upstream tags. The final PR #4 `validate` check passed on head `0d32e38`,
verified at entry to the dependency-audit slice. Client/server runtime testing is not claimed.
Initial correctness/design reviews and the affected correctness follow-up
completed. All accepted findings are resolved with regression coverage; see review progress.
Existing client release checks remain open in the [migration record](../001-bloom-migration/README.md).
The [upgrade guide](../../../docs/upgrades.md) owns operator instructions; this record owns
execution progress and remaining implementation scope.

## Foundation handoff (retained historical evidence)

The instructions below describe the completed foundation session, not the current audit
slice. PR #4 is now merged with passing CI. Current scope and execution steps are above.

Handoff prepared at ~56% context. The reviewed foundation is committed and pushed in
[PR #4](https://github.com/jd-santos/blockery/pull/4). Check its final CI result before
considering merge. Do not infer release or deployment from this delivery. The unchecked
work above defines the remaining bounded implementation packets.

### Checkout and authority

- Branch: `pack-maintenance`, based on `5565f694157a1c9479feb8ce85bacce457621700`
  (merged client-split PR #3). Foundation commit: `6cd0e1b` (SSH-signed), pushed to
  `origin/pack-maintenance`. [PR #4](https://github.com/jd-santos/blockery/pull/4) is open.
- The owner authorized committing ready work and shipping through a topic-branch PR if
  appropriate. The current request resumes the bounded foundation review and delivery.
- Do not upgrade pins, activate exclusions, clear release gates, publish packs, deploy,
  touch Bloom, or remove retained artifacts. Preserve SSH signing and allow 240 seconds
  for an authorized signing attempt.
- `research.md` is unrelated and untracked. Do not read, edit, stage, or delete it.
  Ignore `local/` artifacts when staging. Do not use indiscriminate `git add .`.

### Review progress

The resumed session found 0/2 active slots and completed two fresh read-only reviews.
Correctness review `7891d32f-8557-4336-871e-31ee286f5f22` identified two P2 issues:
malformed Modrinth records/dependencies could raise uncaught errors, and the exclusion
baseline was captured after preview. Both are fixed in `scripts/upgrade_pack.py` with
four new regression tests. API records, dependency references, and loader evidence are
shape-validated; lookup failures remain unknown with errors. Exclusion changes now use
validated discovery, a baseline, revalidation, and unchanged checks before confirmation
and before writing. Old worktrees and artifacts remain untouched.

Design review `7d56b4b6-68ef-4c49-aaef-598e54928c41` found no blockers. Its optional
suggestion to embed source/run provenance in `ci-report.json` is deferred to release-set
tooling, where independently attributable artifacts are already planned.

Earlier follow-up launches failed before child startup due model configuration. The owner
authorized correcting provider mappings, and the successful read-only follow-up
`02ffa66b-cdc8-4f5c-8ad5-fe08750d21e3` confirmed both original findings resolved, with
an OK-with-notes verdict. It identified invalid timestamp strings and unsupported dependency
types as remaining malformed-evidence cases. The parent now parses timezone-aware publication
times, compares actual instants, normalizes report timestamps to UTC, and rejects unknown
dependency types. Added tests cover invalid/naive dates, offset ordering, unknown types,
and all four supported dependency types. All 49 fixtures and fresh static/source/LSP checks
pass. These final small corrections were parent-validated, not independently re-reviewed;
the agreed one-follow-up review cap is reached.

### Revalidation and delivery

Read `AGENTS.md`, this record, and the maintained tooling/upgrade docs first. Inspect
`git status --short --branch`, the tracked diff, and intended untracked files. Existing
changes span the scripts/tests/policy/workflow, README/changelog/tooling/upgrade docs,
workbench links, and the migration record's hosting/rollback clarification.

Run the following from the repository root. These are the checks already used locally;
rerun them after review fixes rather than treating this handoff as fresh execution evidence.

```sh
uv run --no-project python -m unittest discover -s tests -v
uv run --no-project python scripts/validate_pack.py
uvx ruff check scripts/validate_pack.py scripts/upgrade_pack.py scripts/check_exports.py tests/test_check_exports.py tests/test_upgrade_pack.py
uvx pyright scripts/validate_pack.py scripts/upgrade_pack.py scripts/check_exports.py tests/test_check_exports.py tests/test_upgrade_pack.py
git diff --check
```

Probe changed Python paths with active LSP diagnostics too. If imports remain stale,
compare them with fresh Pyright and executable imports; do not add ignore comments merely
to silence the stale server. Current expected fixture count is 49. Current-source validation
reports 106 indexed files and active download counts 14/46/30/30, with zero exclusions.

If exporter changes need new real artifacts, use the pinned Packwiz from `docs/tooling.md`,
build all four recipes with a new unused version label and `--draft`, then run
`uv run --no-project python -m scripts.check_exports --version LABEL` using that label.
Never overwrite retained previews. The existing audited label is
`maintenance-preview-20261016-1`; local audit/checksum files are evidence only and must not
be committed. Verify canonical pack/index, pins, configs, and recipe selections remain
unchanged against the base. GitHub Actions has not run this new workflow, and no new
Minecraft runtime or gameplay validation is claimed.

The parent verified public visibility, reviewed an explicit 17-file staged set, created
SSH-signed commit `6cd0e1b`, pushed the topic branch and opened PR #4. Only unrelated
`research.md` remains untracked. Local artifacts and user-wide provider settings are not
part of the PR. The initial CI run is
[38974684551](https://github.com/jd-santos/blockery/actions/runs/38974684551), queued at
inspection; later task-record updates can supersede it. Check the PR's current head checks,
not only that initial run. The parent task stays open for the deferred slices. No merge,
release, host changes or artifact deletion is authorized. Client Prism checks, Axiom
authorization, Modrinth moderation and deployment remain separate.
