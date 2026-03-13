#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

VAULT_ROOT = Path("/Users/otto/Documents/OTTO")
IGNORE_DIRS = [".obsidian", ".git", "node_modules"]

def get_basenotes():
    """Získej všechny .md soubory s bez cesty názvy."""
    notes = []
    for md_file in VAULT_ROOT.rglob("*.md"):
        # Ignoruj .obsidian a další
        if any(ignore in md_file.parts for ignore in IGNORE_DIRS):
            continue

        # Jen názvy bez přípony
        basenames = []
        for name in [md_file.stem, md_file.name]:
            # Memory souborů - formát: 2026-03-12
            if re.match(r'^\d{4}-\d{2}-\d{2}$', name):
                basenames.append(name)
            # Ostatní soubory - celý název bez .md
            elif not name.endswith('.md'):
                basenames.append(name)

        notes.append({
            'path': md_file,
            'basenames': basenames,
            'stem': md_file.stem
        })

    return notes

def find_wikilinks(content):
    """Najdi všechny wiki linky v obsahu."""
    links = []
    for match in re.finditer(r'\[\[([^\]]+)\]\]', content):
        link = match.group(1)
        # Odstraň aliasy: [[Název|alias]] -> Název
        clean_link = link.split('|')[0]
        links.append(clean_link)
    return links

def get_all_links(notes):
    """Vytvoř mapu všech wiki linků."""
    link_map = {
        'links': {},  # link -> soubor
        'inbound': {}  # soubor -> set odkazujících
    }

    for note in notes:
        with open(note['path'], 'r', encoding='utf-8') as f:
            content = f.read()

        links = find_wikilinks(content)
        for link in links:
            link_map['links'][link] = note['path']

    return link_map

def find_unconnected(notes):
    """Najdi nespojené poznámky."""
    all_content = ""

    # Load všech souborů pro hledání incoming links
    for note in notes:
        with open(note['path'], 'r', encoding='utf-8') as f:
            all_content += f.read() + "\n"

    unconnected = []

    for note in notes:
        # Hledej odkazy na všechny možné názvy
        has_incoming = False
        for basename in note['basenames']:
            # Hledej [[basename]] v obsahu
            pattern = r'\[\[' + re.escape(basename) + r'\]'
            if re.search(pattern, all_content):
                has_incoming = True
                break

        if not has_incoming:
            unconnected.append(note)

    return unconnected

def main():
    notes = get_basenotes()
    print(f"📚 Celkem poznámek: {len(notes)}", file=sys.stderr)

    unconnected = find_unconnected(notes)
    print(f"❌ Nespojené: {len(unconnected)}", file=sys.stderr)

    print("\n📄 NESPOJENÉ POZNÁMKY:", file=sys.stderr)
    for note in unconnected:
        print(f"  - {note['path']} ({note['stem']})", file=sys.stderr)

if __name__ == '__main__':
    main()