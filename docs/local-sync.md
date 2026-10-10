# Local Minecraft sync

Packwiz manages the shared pack. Syncthing can manage personal Minecraft data that should follow one player between trusted machines but should not be published with the pack.

Do not sync the whole `.minecraft` directory. It contains logs, caches, downloaded libraries, server history, and other runtime data that is noisy, machine-specific, or private.

## Instance root

For Prism Launcher on macOS, an instance normally stores Minecraft data under:

```text
~/Library/Application Support/PrismLauncher/instances/<instance>/.minecraft/
```

Choose the equivalent instance directory on each device. The instance folder names do not need to match because each Syncthing folder can use a different local path.

Close Minecraft on a device before making large changes or resolving conflicts. Several mods rewrite their state files while the game is running.

## Recommended folders

Create separate Syncthing folders for the data that matters. This is easier to audit than maintaining a long ignore list for `.minecraft`.

| Syncthing folder | Path relative to `.minecraft` | Contents | Recommendation |
| --- | --- | --- | --- |
| Blockery schematics | `schematics/` | Litematica and WorldEdit schematic files | Sync |
| Blockery Litematica state | `config/litematica/` | Per-world placements, selections, and server profiles | Sync between trusted devices |
| Blockery Axiom state | `config/axiom/` | Preferences, blueprints, hotbars, and tool presets | Sync with the ignores below |
| Blockery MiniHUD state | `config/minihud/` | Per-world MiniHUD state | Optional |
| Blockery Stendhal books | `config/stendhal/books/` | Personal and server documentation books | Optional |
| Blockery JEI state | `config/jei/world/` | Per-world bookmarks and lookup history | Optional |
| Blockery Xaero data | `xaero/` | Maps and waypoints | Optional; large and frequently updated |

The current instance has Litematica state for local worlds and multiplayer servers, plus schematic files in both `.litematic` and `.schem` formats. Some filenames expose server names or addresses, so keep these Syncthing folders limited to trusted devices.

## Axiom ignores

The pack leaves Axiom preferences to each player. To carry yours between devices, sync `config/axiom/` and add this `.stignore` file inside that directory on every device:

```text
(?d).DS_Store
(?d).axiom.json.backup
(?d)imgui.ini
```

This syncs `axiom.json` along with personal content in:

- `blueprints/`
- `tool_presets/`
- `hotbars/`

Hotbar filenames can include server names or addresses. Keep them in the private sync folder even if the contents seem harmless.

`axiom.json` can also contain an editor layout tied to a display size. Check the layout after opening Axiom on a device with a different screen.

Syncthing does not synchronize `.stignore` itself, and it only reads that file from the root of the corresponding Syncthing folder. See Syncthing's [Ignoring Files documentation](https://docs.syncthing.net/users/ignoring.html) for the pattern rules.

## Packwiz-managed files

Do not separately sync files already managed by `index.toml`. In particular:

- `config/litematica.json`
- `config/minihud.json`
- the tracked files directly under `config/jei/`
- the tracked defaults under `config/xaero/`

Syncing these files through both Packwiz and Syncthing creates two writers for the same state and makes later pack updates harder to reason about.

## Syncthing settings

- Use **Send & Receive** when each machine may create or edit content.
- Enable file versioning on each device where you want recovery from changes received from another device. Syncthing does not archive a file's own local edits; see its [File Versioning documentation](https://docs.syncthing.net/users/versioning.html).
- Keep conflict files until their contents have been reviewed. Mod state is often JSON or text and can sometimes be reconciled manually.
- Exclude `.DS_Store`, temporary files, and backup files from each folder.
- Let Syncthing finish before opening the same Minecraft instance on another device.

The repository's ignored `local/` directory is available for manual snapshots or experiments. It is not required when Syncthing points directly at the selected live instance directories.
