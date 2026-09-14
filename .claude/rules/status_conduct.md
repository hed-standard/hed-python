---
paths:
  - ".status/**"
---

# Working in .status/

- `.status/` is gitignored: the only copy is on this machine. Never delete,
  move, or rewrite a file here without asking first. Appending is fine.
- Every markdown file written here opens with a `For humans:` summary - three
  or four sentences at the very top: what the file is and what a person needs
  to take from it.
- The root holds only `README.md`, `decisions.md`, `development_history.md`,
  and `local-environment.md`. New material goes in `plans/`, `prompts/`,
  `notes/`, or `scratch/`.
- `README.md`, `plans/`, and `prompts/` are freely revised. `notes/` is
  write-once. `decisions.md` and `development_history.md` are append-only:
  add an entry, never rewrite or delete one.
- A finished plan moves to `archive/completed_plans/` (split still-open boxes
  into a new plan first) and gets an entry in `development_history.md`.
- Temporary scripts, experiments, and one-off test files go in
  `.status/scratch/` - never the repository root. `scratch/` may hold any
  file type and is deleted unread; everywhere else is markdown only.
- Do not read `archive/` unless a file is named for you.
- Filenames: lowercase ASCII, `_` as separator. Notes are
  `YYYY-MM-DD_slug.md` (date first); plans and prompts are `slug.md` - no
  date, no status word in the name.
