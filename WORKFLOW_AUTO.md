# WORKFLOW_AUTO.md - Automated Workflows

This file contains automated workflow configurations and cron jobs.

## Daily Automated Checks

### Morning Routine (8:00 AM)
- **Shopping Deals Check**: Run `scripts/shopping-deals.py` and send results via iMessage
  - Checks current deals on shopping list items
  - Sends formatted results to user

## Cron Jobs

```
0 8 * * * python3 ~/.openclaw/workspace/scripts/shopping-deals.py && imsg send --to ott0 --text "Results here"
```

## Manual Triggers

- Shopping deals check: `python3 ~/.openclaw/workspace/scripts/shopping-deals.py`
