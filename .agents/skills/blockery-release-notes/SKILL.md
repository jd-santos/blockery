---
name: blockery-release-notes
description: Writes player-facing or server-operator release notes for Blockery's client and server packs. Use when drafting a Blockery GitHub or Modrinth release, describing a new pack version, or preparing notes for the release workflow.
metadata:
  version: "1.0.0"
  category: documentation
  requires: "core-writing, technical-writing, changelog-writer"
---

# Blockery release notes

Apply `core-writing` and `technical-writing` first. Use `changelog-writer` when
updating the repository changelog, but don't turn pack release notes into a commit
log or a summary of developer tooling. These are operator-installed shared skills,
not vendored in this repository; `metadata.requires` documents the relationship,
not an automatic loader. If they're unavailable, say so and use this baseline:
write directly for the player or operator, avoid em dashes and filler, and preserve
requirements, user actions and uncertainty. Don't install or copy skills without approval.

Read [the previous Survival note](references/previous-survival.md) for the baseline
voice and level of detail. It is a historical example, not current release evidence.
Read the repository's `docs/tooling.md` section **Prepare an official pack** before
preparing notes for the workflow. Locate repository paths from the Git root; paths
under `references/` here are relative to this skill.

## Establish what is actually shipping

1. Identify the distribution and version. There are four separate packs:
   `blockery-client`, `blockery-extras-client`, `blockery-server-survival`, and
   `blockery-server-creative`. Don't announce all four when only one is being released.
2. Inspect `pack.toml`, the selected recipe in `build/profiles.toml`, inherited entries,
   and `build/disabled-mods.toml`. Use the builder's `plan` command to confirm the
   effective selection. Preserve side declarations and pending release checks.
3. Read the previous release for **that distribution**, the changelog, and the relevant
   source diff. The latest release across the whole repository may be a different pack.
   Where available, compare its archive manifest or release-set evidence rather than
   assuming the current recipe describes the old release. Ask about material gaps.
4. Establish Minecraft, Fabric Loader and Java requirements, changed mods/configs,
   important permissions, and any required user action. Check the actual archive or
   release manifest when one exists. Don't recycle old counts or compatibility claims.
5. Separate evidence from intention: successful CI, a generated archive and an empty
   `pending` list do not prove runtime compatibility. Never claim testing, publication,
   moderation approval, deployment or migration success without evidence.

For a first client release, explain why someone would choose it. For an update,
focus on what changed and what an existing player needs to do. For a server release,
address the operator and distinguish bundled gameplay settings from host-owned state.

## Draft for a person choosing a download

Start with a short paragraph saying which pack this is and why the release matters.
State **player client** or **dedicated server** early. Use short sections:

- **Requirements:** verified Minecraft, Loader, Java and installer requirements.
- **What's changed:** useful differences from that pack's previous release. For a
  first release, use **Included** instead, grouping highlights by what they do.
- **Installation notes:** the exact `.mrpack` asset filename and any update actions.
  Explain that GitHub's source-code ZIP/tar archives aren't installable packs.
- **Known limitations:** only material limitations for this release; omit if none
  are known. Never hide an unresolved release blocker as an ordinary caveat.

Don't list every library or imply installed editing tools grant server permissions.
Explain dependencies that affect use, such as matching client mods for voice features.
For Axiom, retain its separate licensing/multiplayer authorization caveat and link to
[its terms](https://axiom.moulberry.com/eula) when relevant.

Server notes should remind operators to back up existing data and configure world,
access lists, permissions and networking separately. Client notes should explain
fresh-instance installation or verified upgrade steps, not server administration.
Mention optional resource-pack activation when applicable.

## Save and check

For the GitHub workflow, save the body to `docs/releases/<tag>.md`, where the tag is
the profile without `blockery-`, followed by `-<version>`. Example:
`blockery-extras-client` version `2026.10.20` uses
`docs/releases/extras-client-2026.10.20.md`. This is an example name, not a chosen release.
The workflow supplies the release title; don't repeat it as a giant heading in the body.

Check the filename, versions, counts, scope and claims against the intended artifact.
Link supporting sources rather than pasting private logs or machine paths. Keep
unverified facts in the response to the owner, not as TODO placeholders in publishable
notes. If essential facts are missing, leave the draft unapproved and ask.

Writing notes does not authorize clearing recipe gates, changing pins, committing,
running the release workflow, publishing, uploading to Modrinth or deploying.
