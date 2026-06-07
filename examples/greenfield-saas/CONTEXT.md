# Domain context — Tasker

The shared, ubiquitous language of this domain. Use these terms **exactly** in
code, comments, commits, specs, and conversation. The documentator keeps this
file current; do not let terminology drift.

Specialization: **domain** — team productivity.

## Entities

- **task** — A unit of work (related: user, project)
- **project** — A grouping of tasks (related: task)
- **user** — A team member (related: task)

## Glossary

- **backlog** — tasks not yet started
- **wip** — work in progress

## Key workflows

1. Create a task
2. Assign a task
3. Move a task across states

---

> When a change introduces a new term, relationship, or workflow, update this
> file in the same change (it's part of the definition of done). When a term here
> stops matching the code, that's a bug — fix one or the other.
