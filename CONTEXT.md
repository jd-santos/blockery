# Blockery

Blockery defines one shared Minecraft pack that can run on more than one server. Each server keeps its own mutable world and operational state.

## Language

**Pack**:
The shared set of Minecraft and loader versions, mods, and managed configuration required by compatible servers and clients.
_Avoid_: Server, world

**Deployment target**:
An independently operated server instance that receives the pack and owns its runtime state. The current targets are the main server and the creative sandbox.
_Avoid_: World, pack

**Target variation**:
An intentional setting or file that differs between deployment targets while the underlying pack remains shared.
_Avoid_: Separate pack, fork

**Runtime state**:
Mutable data owned by a deployment target, including worlds, player data, logs, caches, and backups. Runtime state is not part of the pack.
_Avoid_: Configuration

**Client distribution**:
The client-compatible form of the pack provided to players, primarily through Modrinth.
_Avoid_: Server pack
