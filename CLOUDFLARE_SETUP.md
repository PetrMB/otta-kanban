# Cloudflare Setup Documentation

## Quick Start - Deploy site to Cloudflare Pages

### Method 1: Full automation (recommended)
```bash
./scripts/cf-pages-setup.sh <domain> <directory> <project-name>
# Example:
./scripts/cf-pages-setup.sh otta-kanban.honeger.com ./dist otta-kanban
```

### Method 2: Manual步骤
```bash
# 1. Deploy
wrangler pages deploy ./dist --project-name=otta-kanban

# 2. Add custom domain
./scripts/cf-pages-domain.sh otta-kanban.honeger.com otta-kanban
```

### Method 3: Dashboard only
1. Go to Cloudflare Dashboard → Pages
2. Create project or select existing
3. Deploy from Git or direct upload
4. Add custom domain in Settings → Custom domains

## Custom Domain Setup流程

1. **Push content** to Pages (`wrangler pages deploy`)
2. **Add domain** via script or dashboard
3. **Configure DNS** in Cloudflare DNS settings:
   - CNAME: `www` → `project-name.pages.dev`
   - Or A record: `@` → Cloudflare IP (if apex domain)
4. **Wait for activation** (usually instant, max 24h)

## Workflow for Multiple Sites

For `www.honeger.com/xy` vs `xy.honeger.com`:

```
Option A: Separate Pages projects
├─ otta-kanban.honeger.com → otta-kanban project
└─ www.honeger.com/kanban → same project, different domain

Option B: Workers routing (advanced)
├─ Workers script routes requests
├─ xy.honeger.com → proxy to Pages project
└─ www.honeger.com/xy → same proxy
```

## Available Scripts

| Script | Purpose |
|--------|---------|
| `cf-pages-domain.sh` | Add custom domain to existing project |
| `cf-pages-setup.sh` | Full deploy + domain setup |
| `cf-pages-deploy.sh` | Deploy only (create if needed) |

## API Requirements

- Account ID: `5470e26fcae9a4c79ec97311fd338cb4`
- API Token: See `CLOUDFLARE_CONFIG.md`
- Permissions: Pages:Edit, Zone:Read

## Notes

- Custom domains may require DNS propagation
- Pages projects are accessible at `*.pages.dev` by default
- SSL certificates are automatic for custom domains
- Free tier: unlimited pages, 500 builds/month
