#!/usr/bin/env python3
"""
Upraví reminder poznámku přes complete + add
"""

import json
import subprocess
import datetime

# Získám všechny remindery
result = subprocess.run(
    ["remindctl", "show", "all", "--json"],
    capture_output=True,
    text=True
)

reminders = json.loads(result.stdout)

for item in reminders:
    if item['title'] == 'Chleba' and not item.get('isCompleted', True):
        uuid = item['id']
        title = item['title']
        list_name = item['listName']
        
        # Complete reminder
        result = subprocess.run(
            ["remindctl", "complete", uuid],
            capture_output=True,
            text=True
        )
        print(f"Completed: {uuid[:8]}...")
        
        # Add new reminder with same title and note
        new_note = "Akční cena: 24.90 Kč @ Penny (do 03.03.2026)"
        
        # Přidám nový reminder
        result = subprocess.run(
            ["remindctl", "add", title, "--list", list_name, "--notes", new_note],
            capture_output=True,
            text=True
        )
        print(f"Added with note: {new_note}")
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
