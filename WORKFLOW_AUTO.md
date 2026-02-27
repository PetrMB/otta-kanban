# WORKFLOW_AUTO.md - Automated Workflows

This file contains automated workflow configurations and cron jobs.

## Daily Automated Checks

### Morning Routine (8:00 AM)
- **Shopping Deals Check**: Run `scripts/shopping-deals.py` and send results via iMessage
  - Checks current deals on shopping list items
  - Sends formatted results to user

### Morning Routine (8:07 AM)
- **Price Flyers OCR Check**: Run `scripts/akcniceny-ocr.py` and send results via iMessage
  - Scans price flyers for special offers using OCR
  - Searches for keywords like "sleva", "akce", "výprodej"

## Cron Jobs

```
0 8 * * * python3 ~/.openclaw/workspace/scripts/shopping-deals.py
0 8 7 * * python3 ~/.openclaw/workspace/scripts/akcniceny-ocr.py
```

## Manual Triggers

- Shopping deals check: `python3 ~/.openclaw/workspace/scripts/shopping-deals.py`
- Price flyers OCR: `python3 ~/.openclaw/workspace/scripts/akcniceny-ocr.py`
