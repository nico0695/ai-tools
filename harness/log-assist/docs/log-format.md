# Dex Player log format — verified reference

Normative reference for the `loga_core` parser. Every statement carries its evidence and its
**scope**: an invariant holds everywhere, a platform fact holds on one platform, and a corpus
measurement describes the logs it was measured on and nothing more. Confusing the three is the
main way this document could do damage.

## 1. Evidence base

Two independent corpora, **335,515 lines, 24 files, 0 lines outside the line format**.

| | Corpus A | Corpus B |
|---|---|---|
| Files | 10 | 14 |
| Lines | 157,100 | 178,415 |
| Platform | tizen | 9 webos, 5 tizen |
| Screens | 1 | 12, across 5 sync groups |
| Player | 6.4.2408.2600 | 6.7.2601.2300, 6.7.2508.0100, 6.4.2408.2600 |
| Range | 2026-08-20..2026-09-10 | 2025-09 .. 2026-02 |
| Notable | DEBUG enabled by remote tag; epoch window on every boot | stack traces, split-brain, `Clearing current playlist` |

Neither corpus lives in this repository: both carry real customer names.
`scripts/fixtures/sample.log` is a synthetic miniature of corpus A.

Citations name the file and line of whichever corpus measured them.

## 2. Invariants — verified on both corpora, safe to codify

### 2.1 Line format

```regex
^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\.(\d{2}) (INFO|SUCCESS|ERROR|DEBUG|WARNING) (.*)$
```

335,515 of 335,515 lines match. Also verified across both corpora:

- Exactly one space between fields; the level is not padded; sub-second is always 2 digits.
- **Every line is atomic.** No continuation lines and no multi-line messages exist — not even for
  stack traces, whose frames each carry their own timestamp and level (§3.2).
- No blank lines, no BOM, LF endings, trailing newline present.
- The level is `WARNING`, never `WARN`.
- **Files are UTF-8 and may contain multibyte characters.** 4 of the 24 files do, including a `ñ`
  inside a component name (`[EMBEBIDO 4V4 Acompañantes 2m50s]`, `PJ - 6DIC 4.log`). Decode as UTF-8;
  never cut a line by bytes.

### 2.2 The level is positional

The level is field 4 and only field 4. Never determine it by searching the message for a level name.
Corpus A contains 41,981 lines carrying a bracketed `[INFO]` token inside the message; a text search
would misclassify every one.

### 2.3 Anchored patterns apply to the message, not to the line

`^Dex Player [\d.]+$`, `^={53}$`, `^\s+at\s` and every pattern in `scripts-idea/` are anchored
against the **message** — what remains after the level. Applied to the raw line they return **zero
hits**, because every line begins with its timestamp.

More precisely, there are two anchor points, and a matcher should try both: the **text**, after the
bracket groups (`^Fail parsing JSON\. File:`), and the **raw message**, including them
(`^\[Server Manager\] Machine:`). The reference catalog writes patterns the first way. This is the easiest way to conclude a corpus
has no boots when it has thirty.

### 2.4 Component: open vocabulary, parsed positionally

A message may open with bracket groups. Parse at most **4**; a group whose content is exactly a level
name is the **nested status**, wherever it sits; the remaining groups, in order, form the component
path; what follows is the text.

**Component names are an open vocabulary.** They vary by screen, template, customer and platform, and
they may contain spaces and non-ASCII. Never match them against a list.

Observed depth differs sharply between corpora, which is exactly why the rule is defensive rather
than fixed:

| | Corpus A | Corpus B |
|---|---|---|
| Max groups | 3 | **2** |
| Lines with a nested status | 41,981 (`[MENUBOARD_TPL] [INFO] …`) | **0 in 178,415 lines** |
| `MENUBOARD_TPL` second group | always `[INFO]` | always the sub-component (`[DataManager]`) |

So the three-group, nested-status shape is **one template's shape, not the format's**. A parser that
assumed either corpus was typical would be wrong about the other.

### 2.5 Effective level

When a nested status is present it takes priority for filtering and counting. Because that makes a
count diverge from a plain `grep`, any script reporting by level says it used the effective level and
shows the raw line level when they differ.

**A nested status that differs from the line level has never been observed** — 0 cases in 335,515
lines. The rule is a guard, not a described behavior.

### 2.6 Counting boots

```regex
^Dex Player [\d.]+$      # against the message; exactly one match per boot
```

The `=` banner also works but must be halved, and it is not the only `=` line:

| Form | What it delimits |
|---|---|
| `^={53}$` | boot banner, two per boot, wrapping the version line |
| `^={54}$` | device status block (open and close) **and** the sync block close |
| `^={19}SYNC GROUP INFO={20}$` | sync block open — 54 chars, title embedded, does **not** match `^={54}$` |

`banner53 / 2 == boot count` held in all 24 files independently.

Two files of corpus B have no status block at all (`^={54}$` = 0), so identity there comes only from
the handshake.

### 2.7 Order by position, never by timestamp

Timestamps carry no timezone, and both a cold boot (§3.3) and a clock correction move them backwards.
Order by `(file, line)`. Any cross-screen time comparison is an assumption and is labeled as one.

### 2.8 Identity comes from content

`[Server Manager] Machine: <value>` is authoritative, never the file name. Supporting fields, when the
status block exists: `Hostname: <IP> <MAC>`, `Serial Number:`, `Machine ID:`, `Machine Sync ID:`,
`Client IP:`.

Two traps, both observed:

- **`Machine:` is not always a name.** `QMC32 QA 2.log:32` repeats the `Hostname:` value, so the
  machine reads as `<IP> <MAC>`. Do not treat that as a screen name.
- **A ` (1)` suffix means nothing on its own, and never deduplicate.** Corpus B proves the dangerous
  case: `20260222-0.log` and `20260222-0 (1).log` are *different screens* of the same group on the
  same day (`Machine ID` 98311 vs 98305), and `20260223-0.log` / `20260223-0 (1).log` are different
  screens with *exactly the same line count*, 5,472 — the strongest possible invitation to deduplicate
  and the clearest proof that it would be wrong. Corpus A shows the benign case, where ` (1)` hangs
  off a folder and is the same screen over a different date range. Resolve identity; never guess from
  the name.

## 3. Platform-scoped facts

Verified per platform. Do not generalize either column.

| | tizen | webos |
|---|---|---|
| Telemetry cadence | 60 s | **300 s** |
| RAM range | 648 – 885 Mb (corpus B) · 564 – 866 Mb (corpus A) | 1,064 – 1,288 Mb |
| CPU peak after boot | **98–99 %** within 10 s, then 27–33 % | ~73–77 % |
| Stack traces | 0 | 21.5 – 49.6 % of ERROR lines, in 3 of 9 files |
| `[Webos Storage Manager]`, `[Channel Manager]`, `[Global Error Handler]` | absent | present |
| `[Tizen App] Device time:` / `[Tizen Storage]` | present | absent |
| Input messages | `Remote Control Enabled` (INFO), `Panel Unlocked` (SUCCESS) — corpus A only | `Remote Control enabled`, `Panel enabled` |
| Heartbeat failure cause | `Error: Network Error` | mostly `timeout of Nms exceeded` |

The Tizen CPU peak is a real, repeatable shape: in all 5 Tizen files of corpus B the **first telemetry
sample after each boot is the file maximum**, 98–99 %. Corpus A never exceeded 54 % — the same
platform, a different screen. Measure; do not threshold.

### 3.1 Stack traces, where they exist

```
ERROR [Global Error Handler] IO_ERROR: Failed to open the file … Error: IO_ERROR: …
ERROR     at onFailure (file://<PATH>/main.js:26500:22)
ERROR     at e.value (file://<PATH>
```
`20260220-0.log:22302-22304`

- Each frame is a **complete line** with timestamp and `ERROR` level; the message matches `^\s+at\s`
  and carries no component. Fold frames into the preceding event; they are not events.
- Header and frames share the exact centisecond, so group by `(timestamp, level, line adjacency)`.
- **Frames are truncated at the line ceiling.** `20260219-0.log` has 253 frames that are byte-identical
  because one frame was cut at the same point 253 times. Counting them as 253 distinct errors would be
  wrong.

### 3.2 The epoch window

On a cold boot the player can start before the system has NTP time, and the first seconds are stamped
at epoch 0 rendered in local time — `1969-12-31 21:00:xx` at UTC-3. **Detect as "within one day of
epoch 0", never by hardcoding the date**, since another timezone renders it differently.

Corpus A: 286 lines, 9 of 10 files, always inside a boot, 13 of 18 boots affected, window 14–31 s,
closing at the first `[Tizen App] Device time:` with a real year.
Corpus B: **0 lines in 30 boots, on both platforms.**

So it is neither universal nor known to be Tizen-only: it depends on how the device was restarted.
The rule stays as a defense — a wall-clock delta across that window produced a spurious 84,462-second
gap in corpus A — but its absence in a corpus means nothing.

## 4. Corpus-scoped — measure, never assume

The numbers below describe the logs they were measured on. **No script turns one into a verdict**;
each compares against the range observed in the logs it is analyzing and says so. This is decision
C-45 / D-12 of the plan, and the table is the argument for it: every row where the two corpora
disagree is a threshold that would have produced false positives.

| Signal | Corpus A | Corpus B |
|---|---|---|
| Level mix | INFO 74.4 / SUCCESS 14.9 / DEBUG 10.6 / ERROR 0.11 | DEBUG absent in 12 of 14 files |
| ERROR forms | 6 distinct | 5 – 137 lines per file, more forms |
| CPU max | 54 % | 98–99 % (tizen), 77 % (webos) |
| RAM floor vs the documented 648 Mb | 12.6 % of samples below it | none below it |
| Heartbeat timeouts | 0 | 79 in one file |
| Split-brain | 0 % of 18 snapshots | **41.7 %** — 5 of 12 webOS `Members:` lines with more than one `[Master]` |
| `Clearing current playlist` | 0 | present in all 9 webOS files, 69 in one |
| Media rotation p50 | 240 s | varies by media duration |
| Max line length | 5,681 (DEBUG JSON) | 1,093 (DEBUG JSON), 356 (webOS error text) |
| Noise concentration | top 20 forms = 73.6 % | ~10 % is one webOS storage message |

**Noise is derived, not listed**: computed by frequency over the corpus at hand. Hidden lines are
always counted, because several matter by their absence.

## 5. Structures

### 5.1 Boot
Banner of 53 `=` wrapping `Dex Player <version>`, then `Platform "<platform>"`, `Device UserAgent:`,
node service start, and — on a cold boot — the epoch window closing at the first real `Device time:`.
`ERROR Dir failed playlists` / `Dir failed schedules` inside a boot are normal.

### 5.2 Handshake
`Fetching dex config` → `Sending Handshake` → `Hostname:` → `The player has connectivity with the
server` → `SUCCESS Handshake received. Code "LICOK"` → `Machine:` → `Machine HB Interval: <n> seconds`.
`LICOK` was the only code in both corpora. A boot may never reach the handshake.

### 5.3 Status block and sync block
The status block is delimited by 54 `=` and carries `Player Version:`, `Serial Number:`,
`Webview Version: ` (trailing space), `Client IP:`, `Machine ID:`, `Machine Tags:`,
`Machine Sync ID:  <n>` (double space), `Multicast IP:  <ip>` (double space), and a second CPU/RAM
reading as `CPU usage: <n>%. Used RAM: <n> Mb` — no component prefix, so the telemetry regex misses it.

Then `[Player] [Sync] Version: <v> - Group: <g> - Members: <ip> [Master] <ip> <ip> ` — **the line ends
with a space** — and the sync block, whose member rows are
`<ip> | <state> | Playlist: <id> [<ts>] | Schedule: <id> [<ts>] | Playlist To Change: [<files>]`.

Format details that are evidence and must survive verbatim: the master row ends with two spaces then
`(MASTER)`; non-master rows end with one space; and two timestamp formats coexist in the same row —
`Playlist:` uses colons and a `Z`, `Schedule:` uses dots and no `Z`.

Member states observed: `PLAYING`, `NEW`, `DOWNLOAD`, `READY`. `Group: undefined - Members: ` with an
empty list is a real state (`20260222-0.log`).

### 5.4 Playlist change
Corpus A: `STOP_TPL received` → `Processing State Sync` → `Playing Playlist` → `Clean media managers
on unload` → `PLAYLIST ID` → `New Playlist received` → `Playing Schedule` → `PLAY burst`.
Corpus B (webOS) additionally has `[Playlist Manager] Clearing current playlist` and the
`[Channel Manager] preloadNextMedia` / `playNextMedia` cycle, both absent from corpus A.

## 6. Rules for the parser

1. Match the line format; a non-matching line is counted and reported, never dropped silently.
2. Read the level positionally.
3. Apply anchored patterns to the **message**, never to the raw line.
4. Parse up to 4 bracket groups; identify the nested status by content, in any position.
5. Never carry a whitelist of component names; expect spaces and non-ASCII in them.
6. Count boots by `^Dex Player [\d.]+$`; halve any `={53}` count.
7. Flag the epoch window and exclude it from wall-clock deltas.
8. Order by `(file, line)`.
9. Resolve screen identity from `Machine:`, tolerating an `<IP> <MAC>` value; never deduplicate by
   file name or line count.
10. Fold `^\s+at\s` frames into the preceding event, and treat byte-identical truncated frames as one.
11. Derive noise by frequency over the corpus at hand.
12. Measure against the observed range; never hardcode a threshold.
13. Truncate long lines for display at 300 chars with `…[+N chars]`; expect lines beyond 5,000.
14. Preserve excerpts byte for byte, including double and trailing spaces.

## 7. Relationship to `scripts-idea/`

`scripts-idea/` was measured on corpus B. Where this document and that one disagreed, the
disagreement was almost always **scope**, not error: corpus A is Tizen-only and single-screen, so it
could not see stack traces, split-brain, webOS storage, or the black-screen cascade, and its RAM, CPU
and PLAY numbers describe one screen.

Confirmed in `scripts-idea/` by corpus B: the webOS 300 s / 1,064–1,288 Mb and Tizen 60 s / 648–885 Mb
figures are exact on all four bounds; the 98 % post-boot CPU peak is exact on Tizen; the 20 % stack
trace share is real on webOS and higher; split-brain at 25 % is real and here reaches 41.7 %;
`Read operation completed` really is ~10 % of a webOS log; ` (1)` files really are different screens.

Corrected by corpus A: components can carry a third group and a nested status; `Input Manager` message
wording differs by platform; `All tasks were finished` is too rare to be a shutdown signal, and
`System will reboot. Reason: <reason>` is the reliable one.

For the parser, this document governs. For platform-specific patterns and flows — especially webOS —
`scripts-idea/` remains the broader reference.
