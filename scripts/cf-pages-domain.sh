#!/bin/bash
# Cloudflare Pages Custom Domain Setup Script
# Usage: ./cf-pages-domain.sh <domain> <project-name>

DOMAIN=$1
PROJECT_NAME=$2
ACCOUNT_ID="5470e26fcae9a4c79ec97311fd338cb4"
API_TOKEN="dU2HZFDqvJz1gjYlsVM8wyZke2ZmSmF-rqmEsLCA"

if [ -z "$DOMAIN" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <domain> <project-name>"
    echo "Example: $0 otta.honeger.com otta-kanban"
    exit 1
fi

# Get project ID
echo "Finding project ID for $PROJECT_NAME..."
PROJECT_ID=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
    "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects?name=$PROJECT_NAME" | \
    jq -r '.result[0].id')

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "null" ]; then
    echo "Error: Project '$PROJECT_NAME' not found"
    exit 1
fi

echo "Project ID: $PROJECT_ID"

# Add custom domain
echo "Adding custom domain: $DOMAIN..."
RESULT=$(curl -s -X POST -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/$PROJECT_ID/domains" \
    -d "{\"domain\":\"$DOMAIN\"}")

echo "Result: $RESULT"

# Check if successful
if echo "$RESULT" | jq -e '.success' > /dev/null; then
    echo "✓ Domain $DOMAIN added successfully!"
    echo "✓ Visit https://dash.cloudflare.com/pages/projects/$PROJECT_NAME/settings/custom-domains to verify DNS"
else
    echo "✗ Error adding domain"
    echo "$RESULT" | jq .
fi
