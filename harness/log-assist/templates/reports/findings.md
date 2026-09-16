# Findings report — <ref>

<!-- Owner: loga-report, worker. Written to reports/<YYYYMMDD>-findings.md when
     there is a conclusion. Under 800 words. Every citation must resolve:
     loga_verify_citations exits 0 before this is shown, or it is not emitted. -->

## Digest

- conclusion:
- outcome:
- evidence:
- limits:

## Reported problem

<What the user reported, and over what window. Two or three lines.>

## Conclusion

`<confirmed | probable>` — <what happened, in two to four lines. State the
mechanism, not just the symptom. If the mechanism is not established, the
outcome is `probable` and this says which link is missing.>

## Evidence

| Id | What it shows | Citation |
|---|---|---|
| F-01 | | `logs/<file>:<line>` |

## Ruled out

<!-- Built from the `## Discarded` sections of record/. What looked like a cause
     and is not, with the reason — this is often the most useful part. -->

- <what was ruled out, and why> — `logs/<file>:<line>`

## Comparison

<!-- Only when 2 or more screens were in scope; otherwise remove this section. -->

<What the other screens did over the same window, and what that adds.>

## Limits

<What these logs cannot show. What would be needed to go further: more days,
another screen, a specific counter. Be concrete.>

## Suggested action

<What a human should do next. The harness does not act.>

## For Jira

```text
<5 to 8 lines, ready to paste: symptom, window, screens, conclusion, evidence
reference, suggested action.>
```
