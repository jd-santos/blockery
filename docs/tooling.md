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

## Distribution builder

Use Python 3.11 or newer through `uv`; the builder has no third-party Python dependencies.
Packwiz remains the exporter. The builder does not download or execute Minecraft, deploy
anything, or publish to Modrinth.

`build/profiles.toml` has four recipes: `blockery`, `blockery-pro`,
`blockery-server-survival`, and `blockery-server-creative`. Each declares:

- `name`: the output pack's display name.
- `side`: `client` or `server`, inherited if omitted.
- `extends`: an optional parent recipe. Client/server cross-inheritance and cycles fail.
- `mods`: explicit `.pw.toml` paths under `mods/` or `resourcepacks/`.
- `files`: explicit reviewed files under `config/`. No globbing or automatic config copying.
- `pending`: release blockers such as unfinished selections, config audits, or runtime tests.

Inheritance unions the parent's and child's selections and pending checks, preserving order
and removing duplicates. It cannot remove parent entries. Pro can add extras to the minimal
client base; creative can add verified differences to the common survival selection. A
variation that must remove something needs a separate explicit selection, not a copied pack.
Config overlays with destination remapping are not implemented yet.

Recipes preserve original mod side metadata and reject entries incompatible with their
side. New source mods are not silently added to recipes. Dependency closure and runtime
compatibility must be checked separately. Plans validate names and source paths without
reading config contents or copying files:

```sh
uv run --script scripts/build_pack.py list
uv run --script scripts/build_pack.py plan blockery-pro
```

The minimal client selection is still empty. Pro retains the current client loadout;
server recipes retain the current server mod selection plus 11 reviewed shared gameplay
config files. Creative inherits both selections from survival. The explicit server-only
Fabric Permissions API 0.5.0 pin satisfies WorldEdit's integration version check; it does
not install a permission manager or grant players permissions. Armor stand resizing is
operator-only. Client drafts still omit configs. The comment-only Lithium config, empty
No Chat Reports server preferences, and FerriteCore defaults are not bundled. Voice/audio
networking and upload paths, WorldEdit storage/permissions, and chat integration settings
remain target-specific review work, not implicit overrides. See the
[server audit](../todo/work/001-bloom-migration/server-audit.md) for selection evidence.
All recipes remain drafts. MiniHUD and other membership decisions can wait until client
release preparation. Dedicated-server behavior and target settings must be verified before
real deployment.

```sh
uv run --script scripts/build_pack.py build blockery-pro --version infrastructure-preview --draft
uv run --script scripts/build_pack.py build blockery-server-survival --version permissions-api-preview --draft
uv run --script scripts/build_pack.py build blockery-server-creative --version permissions-api-preview --draft
```

Each command stages selected sources in a temporary pack, refreshes its own index, and
exports into ignored `local/dist/`. Root `pack.toml`, `index.toml`, metadata, and configs
are not modified. Existing output files are never overwritten; choose a new version.
If copying an export fails or is interrupted by Python, the builder removes its own
partial output so the same version can be retried. A forced process kill may still leave
a partial file; inspect it before manually removing it.
Draft filenames and manifest versions end in `-draft`. They are infrastructure checks,
not publishable or runtime-validated releases. Empty recipes cannot export.

After resolving all pending checks in a recipe and its ancestors, a normal build uses:

```sh
uv run --script scripts/build_pack.py build blockery --version YOUR_RELEASE_VERSION
```

Replace `YOUR_RELEASE_VERSION` with a real version instead of `unreleased`. Removing pending checks is a deliberate
release-preparation edit, not something the builder does automatically. A successful
export does not establish mod compatibility, permissions, or deployment safety.

Private/runtime filenames, traversal, and symlinks are rejected. Explicit config inclusion
is an allowlist, not a secret-content scanner: review contents before adding a path.
The builder supports the root pack's identity and Minecraft/loader fields; unsupported
root pack options fail instead of being silently discarded.

Run fixture tests without network calls or a Minecraft process:

```sh
uv run --no-project python -m unittest discover -s tests -v
```

For a manual client smoke test, import
`local/dist/blockery-pro-infrastructure-preview-draft.mrpack` into a new Prism instance,
not an existing instance. Use Java 21, launch to the title screen, and create a disposable
singleplayer world. Confirm the selected client mods load and server-only additions are
absent. This draft intentionally has no configs, so it does not test the old personalized
settings or the final minimal/Pro split. Leave Fresh Animations disabled unless EMF has
also been installed. Report errors using a short non-sensitive excerpt, not a full log.

No Bloom or world-migration test is needed to commit the builder. Real server startup,
config audits, updates, and rollback remain requirements for deployment, not evidence
provided by these local exports.

Builder sources, recipes, tests, Python caches, and Ruff caches are excluded from root
Packwiz exports. Run `packwiz refresh` after changing indexed sources or exclusions.
