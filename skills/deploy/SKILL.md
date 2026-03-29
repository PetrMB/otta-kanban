---
name: deploy
description: 'Deploys static websites to Cloudflare Pages. Use when user asks to deploy, publish, or update a website. Handles Cloudflare Pages deployments via wrangler CLI.'
metadata:
  {
    openclaw: {
      emoji: "🚀",
      requires: { "anyBins": ["wrangler"] },
    },
  }
---

# Deploy Skill

Deploys static websites to Cloudflare Pages.

## Project Location
```
~/CODE/
```

## Deployment Command
```bash
wrangler pages deploy ~/CODE --project-name=otta-kanban-v2 --commit-dirty=true
```

## Notes

- **Always use `--commit-dirty=true`** — the CODE directory has uncommitted changes
- **index.html** must exist in ~/CODE/ (rename files to this if needed)
- The project name is `otta-kanban-v2`
- URL format: `https://XXXXXXXX.otta-kanban-v2.pages.dev`
- If new project needed: change `--project-name=NEW_NAME`

## Deploy Steps

1. Ensure `index.html` exists in `~/CODE/`
2. Run: `wrangler pages deploy ~/CODE --project-name=PROJECT_NAME --commit-dirty=true`
3. Wait for "Deployment complete!" message
4. Copy the new URL from output
