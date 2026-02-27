#!/bin/sh
# Ranní briefing - Čeština
# Posílá se v 6:30 každé ráno

SCRIPT_DIR="$HOME/.openclaw/workspace/scripts"

# 1. Počasí v Praze
uvitcho=$("$SCRIPT_DIR/uvitcho-dnes.sh" 2>/dev/null)

# 2. Kalendář - získá první tři události (vyžaduje gog autentizaci)
# Pokud není nakonfigurováno, použije fallback
kalendar=$(gog calendar events list --limit 3 --account default 2>/dev/null | head -20 || {
    # Fallback: vytvořit prázdný kalendář s nástinem
    echo "📅 Kalendář:"
    echo "Připomeňte: gog auth configure pro přístup k kalendáři"
})

# 3. BBC Novinky
novinky=$(python3 "$SCRIPT_DIR/bbc-novinky.py")

# Formátování zprávy
cat << EOF
🌞 Ranní briefing - $(date "+%d. %m. %Y")

${uvitcho}

${kalendar}

${novinky}
EOF
