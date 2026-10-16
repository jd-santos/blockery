---
status: in_progress
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

Work is on `pack-maintenance`; the parent is the sole repository writer. The CI worker
supplied a read-only workflow/archive-audit proposal from an isolated worktree. The parent
applied and strengthened it, implemented the upgrade foundation, and owns validation,
documentation, and this workbench. Only the parent launches reviewers or other agents.

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
- [ ] Commit the reviewed foundation with SSH signing and open a topic-branch PR if ready.
  Keep the unfinished implementation slices below in the live queue. [context: small]
- [ ] Finish downloaded-JAR/nested-provider/Fabric version-constraint checks and optional
  availability queries for disabled entries. The first report checks Modrinth required
  dependency references, not full closure. [context: medium]
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

## Validation

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
pins match their upstream tags. GitHub Actions execution and client/server runtime testing
are not claimed. Initial correctness/design reviews and the affected correctness follow-up
completed. All accepted findings are resolved with regression coverage; see review progress.
Existing client release checks remain open in the [migration record](../001-bloom-migration/README.md).
The [upgrade guide](../../../docs/upgrades.md) owns operator instructions; this record owns
execution progress and remaining implementation scope.

## Handoff for a new session

The earlier handoff was prepared at ~17% context. The resumed session completed review and
fixes. Finish delivery of the bounded foundation, not the deferred apply engine.

### Checkout and authority

- Branch: `pack-maintenance`, based on `5565f694157a1c9479feb8ce85bacce457621700`
  (merged client-split PR #3). Maintenance changes are uncommitted; no maintenance PR exists.
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

Once reviews and checks pass, load `repo-commit`, `commit-message-writer`, and `ship`.
Verify public visibility with `gh repo view --json isPrivate`, inspect an explicit staged
file list for sensitive or unrelated content, make a signed commit, and push/open a PR only
for the ready foundation. Update this record with actual review and PR evidence. Keep the
parent task open for the deferred slices; do not mark the whole maintenance effort complete.
Inspect the PR's actual checks after opening it, and distinguish pending CI from passed CI.
Client Prism checks, Axiom authorization, Modrinth moderation, and deployment remain separate.
