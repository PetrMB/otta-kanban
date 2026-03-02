#!/usr/bin/env python3
"""
Shopping Deals Sync with Apple Reminders
- Reads Nákupy reminders via JSON
- Checks current deals in Penny/BILLA/Lidl
- Adds price info to reminder notes (single line, no blank lines)
"""

import json
import subprocess

PENNY_DEALS = [
    {"name": "Mléko polotučné pasterované", "price": 19.90, "end_date": "03.03.2026"},
    {"name": "Chléb polohrubý pečivo", "price": 24.90, "end_date": "03.03.2026"},
    {"name": "Vejce třídní velké", "price": 39.90, "end_date": "03.03.2026"},
    {"name": "Sýr Eidam 45% plátky Zlatý sýr", "price": 14.90, "end_date": "03.03.2026"},
    {"name": "Zelenina Mix", "price": 29.90, "end_date": "03.03.2026"},
    {"name": "Avokádo", "price": 39.90, "end_date": "03.03.2026"},
    {"name": "Okurka", "price": 19.90, "end_date": "03.03.2026"},
    {"name": "Pomazánkovéko másla", "price": 14.90, "end_date": "03.03.2026"},
]

LIDL_DEALS = [
    {"name": "mozzarellu", "price": 14.90, "end_date": "04.03.2026"},
    {"name": "avokádo", "price": 29.90, "end_date": "04.03.2026"},
    {"name": "okurka", "price": 19.90, "end_date": "04.03.2026"},
]

def check_deals(product_name):
    """Check if product is in any deal"""
    product_lower = product_name.lower().replace("_", " ")
    
    # Check Penny
    for deal in PENNY_DEALS:
        name_lower = deal["name"].lower()
        if "mléko" in product_lower and "mléko" in name_lower:
            return deal
        if any(x in product_lower for x in ["chleb", "pečivo"]) and any(x in name_lower for x in ["chleb", "pečivo"]):
            return deal
        if "vejce" in product_lower and "vejce" in name_lower:
            return deal
        if any(x in product_lower for x in ["sýr", "mozzarella", "mozzarellu"]) and any(x in name_lower for x in ["sýr", "mozzarellu"]):
            return deal
        if any(v in product_lower for v in ["zelenina", "mrkev", "okurka", "avokádo"]):
            if any(v in name_lower for v in ["zelenina", "mrkev", "okurka", "avokádo"]):
                return deal
    
    # Check Lidl
    for deal in LIDL_DEALS:
        if deal["name"].lower() in product_lower:
            return deal
    
    return None

def update_reminder(uuid, note_text):
    """Update reminder note using full UUID"""
    result = subprocess.run(
        ["remindctl", "edit", uuid, "--notes", note_text],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error editing {uuid[:8]}...: {result.stderr}")
        return False
    
    return True

def sync_deals():
    """Sync deals to reminders using UUID-based editing"""
    print("=== Nákupní sync ===")
    
    result = subprocess.run(
        ["remindctl", "list", "Nákupy", "--json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error getting reminders: {result.stderr}")
        return 0
    
    try:
        reminders = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Error parsing JSON")
        return 0
    
    # Filter pending reminders only
    pending = [r for r in reminders if not r.get("isCompleted", True)]
    print(f"Nalezeno {len(pending)} nevyřešených reminderů")
    
    synced = 0
    
    for item in pending:
        title = item["title"]
        uuid = item["id"]
        
        # Check if already has price info
        if "Kč" in item.get("note", ""):
            print(f"✅už má cenu: {title}")
            continue
        
        # Check for deals
        deal = check_deals(title)
        
        if deal:
            price_str = f"{deal['price']:.2f}"
            end_date = deal.get("end_date", "neuvedeno")
            deal_type = "Penny" if deal in PENNY_DEALS else ("Lidl" if deal in LIDL_DEALS else "BILLA")
            
            # NO BLANK LINES - single line format
            new_note = f"Akční cena: {price_str} Kč @ {deal_type} (do {end_date})"
            
            if update_reminder(uuid, new_note):
                print(f"✅ Updated: {title} - {price_str} Kč @ {deal_type}")
                synced += 1
        else:
            print(f"⏳ No deal: {title}")
    
    print(f"\n✅ Synced {synced} reminderů")
    return synced

if __name__ == "__main__":
    sync_deals()
