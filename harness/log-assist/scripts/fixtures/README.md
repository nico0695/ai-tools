# Fixtures

Synthetic logs for manual testing of the scripts. **No real customer data is ever committed
here**: analyses live in `analyses/`, which is gitignored.

## `sample.log`

472 lines, one screen, `tizen`, player `6.4.2408.2600`, dated 2026-01-15. A miniature of the
corpus characterized in [`docs/log-format.md`](../../docs/log-format.md). Every shape in it was
observed in real logs; every identity value in it is invented.

What it exercises:

| | |
|---|---|
| The 60-second tick | seven lines (telemetry, display policy, next-policy, reboot countdown, remote control, panel, heartbeat) — 52 % of a real log's volume |
| Two boots | 53-`=` banner, epoch-window timestamps at `1969-12-31`, `Dir failed` errors, handshake `LICOK`, `No tenant code found` warning |
| Reboot reasons | `Scheduled reboot` and `SOFT_CLEAN_COMMAND` |
| Status and sync blocks | 54-`=` delimiters, sync open with embedded title, `Members:` with one `[Master]`, three `PLAYING` rows, `(MASTER)` after two spaces |
| Playlist change | the real sequence, with no `Clearing current playlist` |
| Heartbeat outage | a streak of 15 `Error: Network Error` failures, then recovery |
| Storage incident | `[Tizen Storage] The storage is locked` alternating with `Checking playlist failed` (note the double space), ending in a reboot |
| Bracket depths | 1, 2 and 3 groups, including `[MENUBOARD_TPL] [INFO] [OffsetsManager]` where the nested status sits in the middle |
| Long lines | one DEBUG line of 1,157 chars with raw JSON, past the ~325-char ceiling the rest respect |
| A coverage gap | several hours with no lines |

Verified invariants: 472 of 472 lines match the line regex; `={53}` count is exactly twice the
boot count; no stack traces; no multi-line messages; no blank lines; LF endings; ASCII only;
trailing newline present.

## What it deliberately does not contain

Because the characterized corpus does not contain them, and a fixture that teaches the parser
a phenomenon that was never observed is worse than no fixture:

- stack traces (`^\s+at\s`) — a webOS phenomenon, 0 of 172 ERROR lines on Tizen
- split-brain (two `[Master]` marks) — 0 % of snapshots in the corpus
- the black-screen cascade — `Clearing current playlist`, `preloadNextMedia`, `[Global Error Handler]` all absent
- webOS components such as `[Webos Storage Manager]`

If a script needs one of these, add a sibling fixture whose name says it is fabricated
(`sample-<case>-synthetic.log`) rather than mixing invented phenomena into this file.

## Proportions are not faithful

A 472-line miniature cannot reproduce the level mix of a 157,100-line corpus and still be
event-rich. Here ERROR is 5 % where the corpus had 0.11 %, and DEBUG is 2 % where the corpus
had 10.56 %. **The fixture exercises shapes, not distributions.** Use it to check that a script
parses and counts correctly, never to calibrate a threshold.
