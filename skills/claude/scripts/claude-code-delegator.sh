#!/bin/bash
# claude-code-delegator.sh
# Delegates tasks to Claude Code from OpenClaw

WORKDIR="${CLAUDE_WORKDIR:-~/CODE}"
PROMPT="$1"

if [ -z "$PROMPT" ]; then
    echo "Usage: claude-code-delegator.sh <prompt>"
    exit 1
fi

# Ensure git repo exists
if [ ! -d "$WORKDIR/.git" ]; then
    mkdir -p "$WORKDIR"
    git init "$WORKDIR" 2>/dev/null
fi

cd "$WORKDIR"
claude --print --permission-mode bypassPermissions "$PROMPT"
