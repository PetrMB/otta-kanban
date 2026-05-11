#!/bin/bash
# Start Reachy Mini OpenClaw Daemon

cd ~/.openclaw/workspace/skills/reachy-mini
source ~/.venvs/reachy-mini/bin/activate
exec python3 reachy_openclaw_daemon.py
