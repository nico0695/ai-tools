# Inventory

<!-- Owner: loga-inventory, worker. Built from loga_scan; rerun when logs are
     added. Screen identity comes from `Machine:` in the content, never from the
     file name — a file ending in " (1)" is another screen, not a duplicate. -->

## Digest

- files:
- screens:
- coverage:
- parse rate:
- blocker:

## Files

| Alias | File | Screen | Platform | Player | Range | Lines | parse_rate | Boots |
|---|---|---|---|---|---|---|---|---|
| F1 | `logs/<name>.log` | | | | | | | |

## Coverage and gaps

<Which screens and dates the logs actually cover, and what is missing for the
reported window. A period with no lines is not automatically a problem: a
scheduled power policy looks the same.>

## Suggested metadata

<!-- Confirmed by the user before status becomes "analyzing". -->

| Field | Suggested | Evidence |
|---|---|---|
| platform | | `F1:<line>` |
| player_version | | |
| screens | | |
| incident_window | | |

## Notes

<Anything that will bite later: low parse_rate, clock jumps, truncated files.>
