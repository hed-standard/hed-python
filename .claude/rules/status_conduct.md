---
paths:
  - ".status/**"
---

# Working in .status/

- `.status/` is gitignored: the only copy is on this machine. Ask first before deleting, moving, or renaming anything here.
- `README.md`, `plans/`, and `prompts/` are living documents: edit them freely - tick a box, replace a section, rewrite the whole file - without asking. Before rewriting `README.md` wholesale, copy the old one to `scratch/readme_before_YYYY-MM-DD.md`. `notes/` is write-once. `decisions.md` and `development_history.md` are append-only: add an entry, never change or delete one.
- Every markdown file written here opens with a `For humans:` summary - three or four sentences at the very top: what the file is and what a person needs to take from it.
- The root holds only `README.md`, `decisions.md`, `development_history.md`, and `local-environment.md`. New material goes in `plans/`, `prompts/`, `notes/`, or `scratch/`.
- Filenames: lowercase ASCII, `_` as separator. Every plan, prompt, and note is `YYYY-MM-DD_slug.md`, date first - for a plan or prompt, the day it was opened. A file without a leading date is renamed, never left. No status word in a name.
- `archive/` has four places, and nothing goes anywhere else in it. A finished plan moves to `archive/completed_plans/` and a finished prompt to `archive/completed_prompts/`, names unchanged (split a plan's still-open boxes into a new plan first, and add a `development_history.md` entry). When the year turns, notes move to `archive/completed_notes/`, names unchanged. Anything else goes to `archive/<year>/`, names unchanged - files only, never a subdirectory, never non-markdown.
- Do not read `archive/` unless a file is named for you.
- Temporary scripts, experiments, and one-off test files go in `.status/scratch/` - never the repository root. `scratch/` may hold any file type; everywhere else is markdown only. Non-markdown that is not kept goes to `scratch/`, never `archive/`.
- `scratch/` is cleaned only when the developer asks for a cleanup - obvious junk only, never by age. List the files that will be deleted (path, size, and why each is junk) and ask whether it is okay to delete them. Once the developer says yes, delete exactly those files yourself; never hand the deletion back.
