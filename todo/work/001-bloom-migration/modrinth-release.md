# Survival server Modrinth release preparation

This is draft listing copy and publication evidence, not a published release or a Bloom
installation guide. The execution checklist remains in [the migration work record](README.md#work).
Client pack publication is deferred.

## Project fields

| Field | Value |
| --- | --- |
| Title | Blockery Server Survival |
| Requested slug | `blockery-server-survival`, subject to availability |
| Project type | Modpack |
| Summary | A survival server pack for a small, private community, with building tools, gameplay tweaks, and performance mods. |
| Environment | Dedicated server only. Verify the closest accurate server-side option in the current editor; this is not a client pack. |
| Minecraft | 1.21.10 |
| Loader | Fabric; the artifact pins Fabric Loader 0.19.5 |
| Java | 21 or newer |
| Categories | Select accurate server-pack categories offered by the editor, such as lightweight and vanilla-like if available. |
| License | `GPL-3.0-or-later` for original Blockery material. All third-party works, including Axiom, retain their own terms. |
| Source | Use the public, version-pinned source URL in the version notes below; it includes the matching license, recipes, and build inputs even before the PR merges. |
| Initial version | `2026.10.12`, confirmed by the owner; non-draft candidate built and locally verified |
| Release channel | Release, as requested by the owner; no beta label |
| Content disclosure | Enable **Contains AI-generated content**. The description below explains the assistance with Packwiz configuration, tooling, deployment preparation, and writing. |
| Icon | Optional; no asset selected. Any future artwork must comply with Modrinth's prohibition on AI-generated project-page images. |

No project, version, icon, or permissions evidence has been uploaded. Slug availability
and the editor's current category choices have not been checked through an account.

## Description draft

Copy the following section only after confirming it matches the final artifact.

### About

I put Blockery Server Survival together for a small, private, whitelisted server for
friends and family. It's a Minecraft 1.21.10 Fabric pack based on our existing mod setup:
building tools, a few survival tweaks, and performance mods. Keeping the versions and
shared settings in Packwiz gives me a repeatable setup instead of passing around copies
of a server folder.

This is the server pack, not a player client pack. Sharing it makes the setup available
to other small groups, but this page isn't a public server listing or an invitation to join.

### What's included

- WorldEdit, Axiom, and Armor Poser for building and editing.
- Whole-tree breaking with normal durability costs, player and mob head drops, and mob silencing.
- Two shulker shells when a shell drop occurs, rather than a guaranteed drop on every kill.
- Simple Voice Chat and AudioPlayer server components, plus Styled Chat.
- Lithium, FerriteCore, View Distance Fix, Better Fabric Console, and Inhabitor.
- No Chat Reports, configured to convert player chat to game messages without requiring
  players to install No Chat Reports on their clients. This changes how chat is presented
  and its availability for Minecraft's signed-chat reporting.

Armor stand resizing requires operator status. FallingTree breaks trees up to 100 blocks,
uses normal tool durability, and can be disabled by sneaking; whole-tree breaking is off
in creative mode. Player deaths drop a head, while mob head drops use per-mob chances.

### Installation and client features

Use a server installer that supports Modrinth `.mrpack` files, with Java 21 or newer.
The pack pins Minecraft 1.21.10 and Fabric Loader 0.19.5. Don't import this download into
a client launcher as the Blockery player pack.

Features such as voice chat and the Axiom editor need their corresponding client mods.
This download doesn't install anything on players' computers. Separate Blockery client
packs are planned but aren't part of this release.

Configure your host's ports, voice/audio settings, world path, permissions, and access
lists separately. Although my server is whitelisted, this pack doesn't enable or populate
a whitelist for you. It includes no world, operator list, private server properties,
upload storage, credentials, or launcher JAR, and doesn't set the game mode or difficulty.

Axiom has separate usage terms. Non-commercial private multiplayer servers need the
author's multiplayer whitelist, and commercial use requires the applicable license.
I still need to obtain that Axiom authorization for our server. It is separate from our
Minecraft player whitelist and isn't granted by downloading this pack. See
[Axiom's project page](https://modrinth.com/mod/axiom) and
[EULA](https://axiom.moulberry.com/eula).

### Testing and updates

The release has passed local fresh-install, restart, world-save, and shutdown checks.
I've also checked gameplay and operator/non-operator permissions locally. Moving the
pack onto our hosted server and testing updates, backup restoration, and rollback are
still ahead. Back up your world and other runtime data before installing or updating;
the pack doesn't guarantee that an installer will preserve custom storage paths.

### AI assistance

I used AI assistance to turn our existing mod setup into pinned Packwiz metadata and
reviewed configuration, write the Python build scripts and tests, check dependency
metadata, and troubleshoot local installation. It also helped plan deployment and draft
the documentation and this page.

The included mods are existing third-party projects credited through Modrinth. AI wasn't
used by this project to create those mods; the assistance was with managing, configuring,
and preparing to deploy the pack. I make the mod and gameplay decisions and review the
changes before deployment.

### License and source

Original Blockery pack definitions, tooling, documentation, and original configuration
contributions are GPL-3.0-or-later. The mods and other upstream material retain their own
licenses and usage terms. License text and third-party notices are included in the pack.
The [source repository](https://github.com/jd-santos/blockery) records the selections and
build process; the version notes identify the matching source revision.

## Version changelog draft

- Initial dedicated survival server pack for Minecraft 1.21.10 and Fabric Loader 0.19.5.
- Select 30 pinned Modrinth mod downloads and 11 shared gameplay configs.
- Configure operator-only armor stand resizing and the documented shared gameplay settings.
- Include Fabric Permissions API 0.5.0 to satisfy WorldEdit's permissions integration.
- Validate local fresh-world start, pinned restart, and save/stop behavior.
- Check gameplay and operator/non-operator permissions locally.
- Configure No Chat Reports to convert chat to game messages without requiring the client mod.
- Include GPL-3.0-or-later text, scoped third-party notices, and the source repository link.

Source revision: [`3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f`](https://github.com/jd-santos/blockery/tree/3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f).

Only use this changelog if the final candidate retains these selections and passes its
own final checks. Do not describe the project-wide `Unreleased` notes, which also cover
client/build work, as this server version's changelog.

## Distribution evidence

Checked on 2026-10-12 against Modrinth's public project and exact-version APIs:

- All 30 selected filenames, URLs, hashes, project IDs, and version IDs match exact
  files hosted on Modrinth, including projects marked All Rights Reserved.
- The tested survival archive has those same 30 indexed downloads and exactly the
  11 selected config override files. The archive's empty `overrides/` directory is
  not an additional payload file. No JARs, resource packs, worlds, or runtime data are bundled.
- The audited artifact is `local/dist/blockery-server-survival-permissions-api-preview-draft.mrpack`,
  SHA-256 `a993e1c14fa087dcec605696d644638151bfbebf0d5ad823d19744fb6e7a1362`.
  It is still a draft and must not be uploaded as the release.
- Detailed public API receipts are retained in ignored
  `local/audit/modrinth-server-publication.json`. The canonical pins remain in the
  recipe's selected `mods/*.pw.toml` files, not this receipt.

[Modrinth's permissions guide](https://support.modrinth.com/en/articles/8797527-obtaining-modpack-permissions)
allows use of a specific Modrinth-hosted file in a Modrinth modpack. This applies to the
indexed hosted downloads; it is not blanket permission to rehost JARs, relicense their
contents, use commercial features, or redistribute unrelated external assets.

Serilum also publishes modpack permission while the downloads stay within CurseForge
or Modrinth: [Collective](https://github.com/Serilum/Collective),
[Just Mob Heads](https://github.com/Serilum/Just-Mob-Heads),
[Just Player Heads](https://github.com/Serilum/Just-Player-Heads),
[Shulker Drops Two](https://github.com/Serilum/Shulker-Drops-Two), and
[Silence Mobs](https://github.com/Serilum/Silence-Mobs).
These statements are supporting evidence, not a relicensing of their source or generated comments.

The 11 overrides are reviewed configuration, not mod binaries. Original Blockery material
is declared GPL-3.0-or-later in the [repository README](../../../README.md#license), with
full GPL v3 text in [LICENSE](../../../LICENSE). Preserve all third-party
terms/notices and account for any third-party configuration text
in Modrinth's permissions review. No Axiom config is included, and no new external asset
has been added in this preparation pass. Do not claim that every override is independently
authored or covered by the hosted-download rule.

## Decisions and release gates

The owner confirmed GPL-3.0-or-later for original Blockery material, initial version
`2026.10.12`, and the normal release channel rather than beta. The release channel does
not change the validation limits listed above.

The isolated recipe builder now stages exact copies of `LICENSE` and `build/NOTICE.txt`
under `blockery-notices/`. The licensed Survival draft is
`local/dist/blockery-server-survival-2026.10.12-draft.mrpack`, SHA-256
`f9e320d457010e71f9a98852cbb41670550c1a422d2f994a50118d6b60f361c7`.
It contains 30 downloads, 11 config overrides, and exactly two notice overrides. Its mod
file index, dependencies, and gameplay config bytes match the earlier tested draft.
Both notices match their source bytes; no other payload files were added. Archive evidence
is retained in ignored `local/audit/2026.10.12-exports.json`.

This exact archive passed fresh-world startup and a second pinned start in ignored
`local/server-smoke/blockery-server-survival-2026.10.12-licensed/`. Both runs answered
console commands, saved, and exited 0 without forced termination. Mod, config, and notice
bytes matched; API 0.5.0 was selected, with no WorldEdit fallback or error lines. Minecraft
and Voice Chat listeners were loopback-only. The Armor Poser refmap and non-TTY terminal
warnings remained, and no players joined. Separate `smoke-summary.json` and
`restart-summary.json` preserve these results. All 17 unit tests and active changed
Python/TOML checks passed. That draft validation preceded the owner-confirmed player
check and non-draft candidate below.

Fresh correctness and design reviews checked staging safety, tests, license scope, and
release claims. The design finding was resolved by making the inherited player-permission
gate explicit and asserting it in the real-recipe tests. The single design follow-up found
no blockers. Reviewers inspected source/docs and permitted JSON summaries; archive, command,
and server validation came from the parent. Additional output-symlink test cases and client
credit-list wording were non-blocking suggestions, deferred to their relevant future scope.

The matching source revision is now public at
[`3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f`](https://github.com/jd-santos/blockery/tree/3f72b0f5ecc7869e8939cf32bec9b394fc7d9c4f).
The authorized source push published the reviewed build inputs, license, and notices.
Unauthenticated GitHub access to the commit, license, and recipes was verified, and all
artifact source inputs match that revision byte for byte. Use the full revision link in
version notes, not only the repository homepage. This source delivery does not publish
the Modrinth artifact or authorize Bloom deployment.

The owner confirmed that an Axiom multiplayer whitelist still needs to be requested.
That is not a publication blocker for the verified Modrinth-hosted Axiom file reference;
it remains a prerequisite for intended private multiplayer use under the author's terms.
Do not imply that publication grants authorization, and do not post private whitelist
identifiers or commercial account details in this workbench.

The publication boundary is the already approved shared 30-mod, 11-config selection,
plus the two license notices. The exact archive check confirms that no target networking,
upload/storage paths, WorldEdit host settings, chat integrations, server properties, or
private access lists were added. Target settings remain operator-owned and outside the
published pack, as described in the installation section. Their live values still need
review before Bloom deployment, not before distributing this shared artifact.

The owner confirmed the local player check and authorized proceeding with the normal
build. Survival's gameplay/permission gate is now cleared. Creative retains its separate
variation-review gate, and both client recipes remain gated. This records owner-reported
player validation, not an agent-observed test or authorization for private multiplayer use.

Publishing an artifact is separate from adopting mrpack4server on Bloom or migrating
worlds. The launcher candidate remains 0.5.1, and the Bloom project/version configuration
cannot be prepared until verified release IDs or a hosted artifact URL exist.

## Non-draft candidate

The owner reported the local check complete and authorized clearing the gate and building
`2026.10.12`. The non-draft artifact is
`local/dist/blockery-server-survival-2026.10.12.mrpack`, SHA-256
`c0d7bce2204c8abb04abe67a9339b92f0fb53a806c13ea259d2d8bd9ad01319a`.
Its manifest has version `2026.10.12`, Minecraft 1.21.10, and Fabric Loader 0.19.5.
All 30 download references, hashes, sides, 11 config payloads, and two notice payloads
match the licensed draft and current sources. Only manifest version/ordering differs;
no extra payload or runtime data was added. Canonical source hashes stayed unchanged.
Archive checks are retained in ignored `local/audit/2026.10.12-release-exports.json`.

This exact artifact passed fresh installation/startup and a pinned restart in the new
ignored `local/server-smoke/blockery-server-survival-2026.10.12-release-final/` sandbox.
Both runs answered console commands, saved worlds/players, and exited 0 without forced
termination or errors. Installed mod/config/notice bytes matched, API 0.5.0 was selected,
and the WorldEdit fallback was absent. Listeners were loopback-only; the restart did not
reinstall. The refmap and non-TTY warnings remain. These automated runs had no players;
the separate player check is owner-confirmed on the byte-identical licensed draft.
Evidence is in `smoke-summary.json` and `restart-summary.json`. All 18 unit tests pass,
including normal-version/source-preservation and remaining-profile gate checks.

This is an unpublished Modrinth release candidate, not a Bloom deployment. Matching
source delivery is verified above. Modrinth publication authorization/moderation, Axiom
private-multiplayer authorization, and Bloom-specific install/update/rollback/migration
checks remain separate work.

## Submission workflow (not executed)

Git commits and pushes do not submit this project to Modrinth. Publishing automation has
not been configured for this work. New projects require an explicit submission followed
by [human moderation](https://support.modrinth.com/en/articles/8793355-project-review-times).
The initial project becomes public after approval. Later versions of an approved project
generally do not require another project approval, but unknown external content can still
be withheld pending permission information. Review times fluctuate; do not promise a date.

1. Use the verified public source revision already linked in the version notes above.
   Source delivery is complete; preserve the exact commit link when copying those notes
   into Modrinth. The source is on the public topic branch and does not require a PR merge
   to be accessible.
2. Create a Modrinth **modpack** project draft using the fields and description above,
   not a joinable Server Project. Verify the available slug, accurate server-side
   environment, and editor categories. Enable **Contains AI-generated content** and retain
   the specific disclosure in the description. This is required by
   [Modrinth's AI disclosure rules](https://modrinth.com/legal/rules#61-disclosure-of-ai-generated-content);
   prose alone is not a substitute for the content-disclosure setting. Do not add
   AI-generated artwork. The private, whitelisted audience describes the intended use,
   not an included access list or enforced whitelist setting.
3. Upload only `blockery-server-survival-2026.10.12.mrpack`, with version `2026.10.12`
   and the release channel. Confirm the uploaded file matches the candidate's SHA-256.
   Verify that all 30 pinned mods are correctly identified in the version's Dependencies
   section; do not assume the valid archive alone proves the listing metadata is complete.
4. Review Modrinth's Permissions page and resolve any unknown-content requests using the
   evidence below. Do not label third-party generated text as entirely original Blockery
   work. The [external-content workflow](https://modrinth.com/news/article/modpack-permissions)
   requires necessary licensing information before submission; automated attribution is
   not a substitute for permission.
5. With publication authorization, submit the project for review and monitor its
   Moderation tab. Address moderator requests without claiming approval in advance.
6. After approval, record the actual public project/version IDs and verified download
   URL for later pinned Bloom launcher preparation. Approval does not authorize Bloom
   deployment, updater adoption, or world migration.

The source has been pushed to GitHub. No Modrinth draft creation, upload, submission,
or artifact publication has been performed. The operator uses their own authenticated
Modrinth UI; no credentials are needed in this repository or shared with the agent.

## Configuration permission disclosure

The overrides are ordinary functional configuration, including generated setting-description
comments. [Modrinth describes configuration files as normal modpack contents](https://support.modrinth.com/en/articles/8802250-modpacks-on-modrinth).
Its permissions guide does not explicitly exempt configuration comments or prohibit these
ordinary overrides. Disclose the 11 files during moderation review rather than claim that
the hosted-binary permission rule automatically covers them or invent an author-permission
requirement for every setting. Preserve upstream terms and address any moderator request.

## Local player check

The ignored licensed sandbox above is disposable, has no production data, and is stopped.
Use a fresh Prism instance with the previously tested Pro draft as a compatible test client;
this does not settle the client release membership. Do not import the server artifact as
that client. The following check needs the owner's real client session, not credentials
shared with an agent.

1. Start the existing licensed sandbox in a local terminal:

   ```sh
   cd local/server-smoke/blockery-server-survival-2026.10.12-licensed
   env -u JAVA_TOOL_OPTIONS -u JDK_JAVA_OPTIONS -u _JAVA_OPTIONS \
     /usr/bin/java -Xms512M -Xmx2G -Djava.awt.headless=true -jar server.jar nogui
   ```

2. Use console `whitelist off` only in this loopback-only disposable sandbox, then connect
   the test client to `127.0.0.1:25575`. Use console `gamemode creative YOUR_PLAYER_NAME`
   to prepare a small test area if needed; do not put account names in the public work record.
3. As a non-operator, verify normal armor stand posing is usable but resizing is denied.
   Verify a small WorldEdit edit is denied under the default permission setup.
4. Use console `op YOUR_PLAYER_NAME`; verify resizing and a one-block WorldEdit edit/undo
   work. Then use `deop YOUR_PLAYER_NAME` and verify resizing is denied again. This tests
   default operator behavior, not a fine-grained permissions-manager policy.
5. Switch to survival using the console. Break a small tree and check normal durability
   use; try sneaking to disable whole-tree breaking. Check the gameplay features actually
   intended for the first release. Leave Axiom's pending multiplayer authorization separate.
6. Disconnect, restore `whitelist on`, and use console `stop`. Report only pass/fail by
   feature and a short non-sensitive error excerpt if needed, not logs or access-list files.

The owner confirmed completion of this local check and authorized clearing Survival's
gate. The Armor Poser refmap warning still appears; the reported behavior check provides
local functional evidence, not proof that every mixin or client combination is unaffected.
Host networking, uploads, integration settings, and Bloom panel/update/migration tests remain
separate deployment work.

## Policy references

- [Modrinth content rules](https://modrinth.com/legal/rules)
- [Modpack file format](https://support.modrinth.com/en/articles/8802351-modrinth-modpack-format-mrpack)
- [Environment labels](https://modrinth.com/news/article/new-environments)
- [Modrinth modpack permissions process](https://modrinth.com/news/article/modpack-permissions)
- [Axiom commercial-use notice](https://axiom.moulberry.com/download)

Project environment labels and each indexed mod file's physical install sides are different
metadata. Preserve the reviewed `both`/`server` file declarations; do not mark every
both-side dependency server-only merely because this project is a server distribution.
