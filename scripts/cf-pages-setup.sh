#!/bin/bash
# Cloudflare Pages Full Setup Script
# Usage: ./cf-pages-setup.sh <domain> <directory> <project-name>

DOMAIN=$1
DIRECTORY=$2
PROJECT_NAME=$3
ACCOUNT_ID="5470e26fcae9a4c79ec97311fd338cb4"

if [ -z "$DOMAIN" ] || [ -z "$DIRECTORY" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <domain> <directory> <project-name>"
    echo "Example: $0 otta-kanban.honeger.com ./dist otta-kanban"
    exit 1
fi

# Step 1: Deploy to Pages
echo "=== Step 1: Deploying to Cloudflare Pages ==="
wrangler pages deploy "$DIRECTORY" --project-name="$PROJECT_NAME"

# Step 2: Add custom domain
echo ""
echo "=== Step 2: Adding custom domain ==="
./scripts/cf-pages-domain.sh "$DOMAIN" "$PROJECT_NAME"

# Step 3: Instructions for DNS
echo ""
echo "=== Step 3: DNS Configuration ==="
echo "1. Go to Cloudflare Dashboard → DNS → $DOMAIN"
echo "2. Add CNAME record: www → $PROJECT_NAME-<hash>.pages.dev"
echo "3. Wait for DNS propagation (up to 24h, usually faster)"
echo "4. Custom domain will show as 'Active' in Pages dashboard"
