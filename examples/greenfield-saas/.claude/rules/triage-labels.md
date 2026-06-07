# Triage labels

A 5-state vocabulary for issues/tickets, so humans and the factory share one
state machine. Map these to your tracker's real labels.

| State | Meaning | Who acts next |
|---|---|---|
| `needs-triage` | New, not yet assessed. | a human or the triager |
| `needs-info` | Blocked on a question/clarification. | the reporter |
| `ready-for-agent` | Scoped well enough for the factory to build autonomously. | the factory |
| `ready-for-human` | Needs human judgment (design, risk, ambiguity, security). | a human |
| `wontfix` | Decided not to do. | nobody — closed |

## Rules

- An issue enters `ready-for-agent` only when it has clear acceptance criteria
  and no open questions — otherwise `needs-info` or `ready-for-human`.
- Anything touching auth, billing, secrets, or irreversible data ops is
  `ready-for-human`, never `ready-for-agent`.
- The factory pulls only `ready-for-agent` work when running autonomously.
