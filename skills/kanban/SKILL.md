---
name: kanban
description: Manage Kanban board for otto.honeger.com (backlog, in-progress, done). Add, remove, update tasks with priorities.
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "os": ["darwin", "linux"],
        "requires": { "bins": ["git"] },
      },
  }
---

# Kanban Manager

This skill helps manage the Kanban board at https://otto.honeger.com by editing the markdown source files in `projects/kanban/`.

## Location
- Workspace: `~/.openclaw/workspace/projects/kanban/`
- Files: `backlog.md`, `in-progress.md`, `done.md`, `kanban.html`

## Commands

### Add Task
- Add to backlog: `kanban add backlog "[task]"`
- Add to in-progress: `kanban add in-progress "[task]"`
- Add to done: `kanban add done "[task]"`

### Remove Task
- Remove from backlog: `kanban remove backlog "[task]"`
- Remove from in-progress: `kanban remove in-progress "[task]"`
- Remove from done: `kanban remove done "[task]"`

### Show Board
- `kanban show` - Display all sections

### Update Priority
- `kanban priority [section] [task] [high|medium|low]`

### Sync to Web
- `kanban sync` - Build HTML and commit to git

## Example Usage
- "Přidej task do backlogu: iOS/Android App"
- "Odstraň z rozpracováno: Otík Cloudflare Replicant"
- "Ukaž mi kanban"
- "Synchruj kanban na web"

## Notes
- Tasks are stored in markdown format
- HTML is auto-generated from markdown files
- Changes are committed but not auto-pushed; run `git push` manually
