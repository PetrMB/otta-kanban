#!/usr/bin/env python3
"""Denní záloha paměti - zálohuje MEMORY.md a daily notes do backup/memory/"""

import os
import shutil
from datetime import datetime

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

def backup_memory():
    now = datetime.now()
    backup_dir = os.path.join(WORKSPACE, "backup", "memory")
    os.makedirs(backup_dir, exist_ok=True)

    # Zálohovat MEMORY.md
    memory_file = os.path.join(WORKSPACE, "MEMORY.md")
    if os.path.exists(memory_file):
        backup_file = os.path.join(backup_dir, f"MEMORY-{now.strftime('%Y-%m-%d')}.md")
        shutil.copy2(memory_file, backup_file)
        print(f"✔ Zálohováno: MEMORY.md → {backup_file}")

    # Zálohovat daily notes (memory/YYYY-MM-DD.md)
    memory_dir = os.path.join(WORKSPACE, "memory")
    if os.path.exists(memory_dir):
        for filename in os.listdir(memory_dir):
            if filename.endswith(".md"):
                src = os.path.join(memory_dir, filename)
                dst = os.path.join(backup_dir, f"{os.path.splitext(filename)[0]}-{now.strftime('%Y-%m-%d')}.md")
                shutil.copy2(src, dst)
                print(f"✔ Zálohováno: {filename} → {dst}")

    print("✅ Denní záloha paměti dokončena.")

if __name__ == "__main__":
    backup_memory()
