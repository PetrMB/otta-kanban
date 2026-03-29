---
name: claude
description: 'Delegates coding tasks to Claude Code (claude CLI). Use when the user asks to run a task with Claude, or to build/create code files, scripts, or apps. Claude Code uses Anthropic API with --print --permission-mode bypassPermissions for non-interactive execution.'
metadata:
  {
    openclaw: {
      emoji: "🤖",
      requires: { "anyBins": ["claude"] },
      install: [
        {
          id: "claude-code",
          kind: "node",
          package: "@anthropic-ai/claude-code",
          bins: ["claude"],
          label: "Install Claude Code CLI (npm)",
        },
      ],
    },
  }
---

# Claude Code Agent

Use the `claude-code` script to delegate tasks to Claude Code.

## Usage

```bash
claude-code "your prompt here"
```

## Examples

### Build a file
```bash
claude-code "Create a responsive CSS grid layout"
```

### Build a project
```bash
claude-code "Build a REST API with Express.js"
```

### Edit/refactor files
```bash
claude-code "Add error handling to auth.js"
```

## Notes

- Claude Code is non-interactive (uses `--print --permission-mode bypassPermissions`)
- Works in any git directory or created temp repo
- Fast for one-shot tasks, slower for complex multi-file projects
- Model: uses default Claude model via Anthropic API
