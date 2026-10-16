# Quick client playtest

Budget: 10–15 minutes for Blockery Client. Stop at the first crash or join failure;
report it rather than spending the session debugging. Test the current pins, not an
upgrade. This is a practical smoke test for a small friends' server, not exhaustive QA.

## Before starting

- Import the exact draft `.mrpack` you intend to share into a **new Prism instance**
  using Java 21. Keep your existing instance unchanged. Note the archive filename.
- Use a disposable singleplayer world first. Join a server only with the owner's
  approval, using an ordinary player account. No host changes, admin commands,
  mass edits or production-world experiments are needed.

## The useful ten minutes

| Time | Check | Pass looks like |
| --- | --- | --- |
| 2 min | Launch and create a disposable world. | No missing-mod dialog or crash; world renders and controls work. |
| 3 min | Join the approved compatible server. Walk around, open a chest, move a cheap item and place/break an ordinary block where allowed. | No disconnects, unusable lag, inventory glitches or interaction failures. |
| 2 min | Open and close the world map, voice menu and MiniHUD controls. Return to movement/chat after each. | Controls are discoverable and usable without one shortcut triggering multiple unwanted actions. Check Controls only if a collision appears. |
| 2 min | With one friend, exchange a sentence in voice chat both ways. | Both can hear each other; mute/push-to-talk behaves as expected. If nobody is available, mark voice **not tested**, not passed. |
| 1 min | Disconnect, quit normally, relaunch and rejoin. | No crash; the instance and any settings changed during the test still work. |

If server access is unavailable, do the interactions in the disposable world and
mark multiplayer/voice untested. A local pass does not establish multiplayer support.

## Only if you will actually use Extras

Give a separate fresh Extras instance another five minutes:

- Launch and join the same approved server. Check JEI search and ordinary inventory use.
- In a disposable creative world, open the one specialist tool you care about most.
  Do not test mass edits on the shared world. Axiom multiplayer permissions are separate.
- Optionally enable Fresh Animations and look at a nearby mob. Skip visual polish if
  it is not relevant to the players using this pack.

Do not exhaustively exercise every mod, benchmark FPS, or review every keybinding.
If ordinary play feels fine, collect real annoyances during the next normal session.

## Send back four lines

```text
Archive / Java: <filename> / 21
Launch / join / rejoin: pass, fail, or not tested
Maps / controls / voice: pass, issue, or not tested
Blocker: none, or a short description and non-sensitive error excerpt
```

Fix crashes, inability to join, broken ordinary interactions and unusable required
controls first. Cosmetic issues and optional tools can wait. Do not share full logs,
private server addresses or personal instance settings in the repository.

This checklist does not automatically clear recipe release gates. It is **not required
to push the dependency-audit tooling**, which changes no pack pins or selections. Before
releasing a client candidate, review the actual results and any remaining
[client requirements](tooling.md#client-smoke-test).
