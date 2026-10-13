# Blockery

Blockery is the umbrella project and shared source definition. Explicit build recipes
produce distinct client and server distributions. Each server keeps its own mutable
world and operational state.

## Language

**Pack source**:
The canonical Minecraft/loader versions, reusable mod metadata, and reviewed configuration
from which distributions are selected. Root files are not a finished server release.
_Avoid_: Server, world

**Build profile**:
A repository recipe selecting source metadata and reviewed files for one output. This is
our Python build layer, not a native Packwiz feature or a launcher's installed instance.
_Avoid_: Release version

**Distribution**:
A named installable output with a specific audience. `blockery` is the default minimal
player client; `blockery-pro` is the expanded client. `blockery-server-survival` and
`blockery-server-creative` are server outputs. Membership and configuration approvals
remain unfinished, so current recipe builds are drafts.
_Avoid_: World, deployment target

**Deployment target**:
An independently operated server instance that receives a server distribution and owns its runtime state. The current targets are the main server and the creative sandbox.
_Avoid_: World, pack

**Target variation**:
An intentional setting or file that differs between deployment targets while their source definition remains shared.
_Avoid_: Separate pack, fork

**Runtime state**:
Mutable data owned by a deployment target, including worlds, player data, logs, caches, and backups. Runtime state is not part of the pack.
_Avoid_: Configuration

**Client distribution**:
A player-facing pack provided separately from server deployment outputs, primarily through Modrinth.
_Avoid_: Server pack
