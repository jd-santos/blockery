# Previous Survival release note

Style reference: [Blockery Server Survival 2026.10.12](https://github.com/jd-santos/blockery/releases/tag/server-survival-2026.10.12),
published October 16, 2026. The body below preserves its content with Markdown links
and whitespace normalized. Its counts, requirements, permissions and release status
are historical, not defaults to copy into future notes. This is a fixed style
snapshot, not a maintained mirror of the release page.

---

The first standalone release of Vicious Blockery’s Survival server pack. It's a
mostly vanilla survival pack that adds building tools, survival tweaks, voice chat,
and performance mods in a version-pinned setup.

This is a dedicated server pack, not a player client pack.

### Requirements

- Minecraft 1.21.10
- Fabric Loader 0.19.5
- Java 21
- A server installer that supports `.mrpack` files, such as
  [mrpack4server](https://github.com/Patbox/mrpack4server)

### Included

- Building tools: WorldEdit, Axiom, and Armor Poser, with operator-only armor
  stand resizing.
- Survival tweaks: whole-tree breaking with normal durability costs, player
  and mob head drops, mob silencing, and two shells when a shulker shell drop
  occurs.
- Communication: Simple Voice Chat, AudioPlayer, and Styled Chat. Voice and
  Axiom features require their corresponding client mods.
- Performance: Lithium, FerriteCore, View Distance Fix, and Inhabitor.
- Chat configuration: No Chat Reports converts player chat to game messages
  without requiring its client mod, changing signed-chat reporting availability.

The pack contains 30 pinned mod downloads, 11 reviewed gameplay configurations,
and license notices.

### Installation notes

Download `blockery-server-survival-2026.10.12.mrpack` from the release assets.
The automatically generated source archives are not installable packs.

Configure your world, access lists, permissions, networking, and host-specific
settings separately. This release includes no world, credentials, operator list,
private server properties, or launcher JAR. It does not enable a whitelist for you.

Back up existing server data before installing or updating.

Axiom multiplayer use requires separate authorization under
[Axiom’s terms](https://axiom.moulberry.com/eula). Downloading this pack does not
grant that authorization.
