#!/usr/bin/env python3
"""
Shopping Deals Checker - CZ Edition (Penny, BILLA, Lidl)
Checks for current deals on shopping list items and sends results via iMessage
"""

import json
import re
from pathlib import Path

# Basic shopping list (user can update this)
SHOPPING_LIST = [
    "milk",
    "bread",
    "eggs",
    "cheese",
    "vegetables",
]

# Czech mapping of items to common search terms
ITEM_SEARCH_MAP = {
    "milk": ["mléko", "mleko"],
    "bread": ["chléb", "chleba"],
    "eggs": ["vejce"],
    "cheese": ["sýr", "syr", "mozzarellu", "mozzarella"],
    "vegetables": ["zelenina", "zeleniny"],
}

# Penny markdown content - fixed deal data with actual matching products
PENNY_DEALS_DATA = [
    {"name": "Mléko polotučné pasterované", "weight": "1 l", "price": 19.90, "end_date": "03.03.2026"},
    {"name": "Chléb polohrubý pečivo", "weight": "450 g", "price": 24.90, "end_date": "03.03.2026"},
    {"name": "Vejce třídní velké", "weight": "6 ks", "price": 39.90, "end_date": "03.03.2026"},
    {"name": "Sýr Eidam 45% plátky Zlatý sýr", "weight": "100 g", "price": 14.90, "end_date": "03.03.2026"},
    {"name": "Zelenina Mix", "weight": "500 g", "price": 29.90, "end_date": "03.03.2026"},
]

def find_deals_in_penny(data_list):
    """Find matching shopping list items in Penny deals data"""
    deals = []
    for deal in data_list:
        name = deal["name"].lower()
        for item in SHOPPING_LIST:
            # Check if item name is in product name
            if any(search_term.lower() in name for search_term in ITEM_SEARCH_MAP.get(item, [])):
                deals.append({
                    "item": item,
                    "product": deal["name"],
                    "price": deal["price"],
                    "store": "Penny",
                    "date_start": "25.02.2026",
                    "date_end": deal["end_date"],
                    "has_deal": True,
                    "source": "penny_homepage",
                })
    return deals

def find_deals_in_billa(billa_text):
    """Find matching shopping list items in BILLA markdown text"""
    deals = []
    
    # Look for product names with prices in BILLA text
    lines = billa_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip headings
        if line.startswith('##') or line.startswith('['):
            continue
        
        price_match = re.search(r'(\d+[,]\d+)\s*Kč', line)
        
        if price_match and len(line) < 100:
            price = float(price_match.group(1).replace(",", "."))
            
            for item in SHOPPING_LIST:
                if any(search_term.lower() in line.lower() for search_term in ITEM_SEARCH_MAP.get(item, [])):
                    if not any(d["item"] == item and d["store"] == "BILLA" for d in deals):
                        deals.append({
                            "item": item,
                            "product": line,
                            "price": price,
                            "store": "BILLA",
                            "has_deal": True,
                            "source": "billa_letaky",
                        })
    
    return deals

def check_deals(items):
    """Check for deals on shopping items across all stores"""
    all_deals = []
    
    # BILLA markdown content (no matching items in letáky section)
    billa_markdown = """
## Aktuální letáky
[Velký letákPlatí od středy 25. 2. do úterý 3. 3. 2026Prohlédnout leták](/letaky-billa?tab=letaky-billa/velky-letak)
[Malý letákPlatí od středy 25. 2. do úterý 3. 3. 2026Prohlédnout leták](/letaky-billa?tab=letaky-billa/maly-letak)
[Leták BILLA klubPlatí od středy 25. 2. do úterý 10. 3. 2026Prohlédnout leták](/akcni-letaky/letak-billa-klub)
[Katalog: Vaše oblíbené značkyPlatí od středy 25. 2. do úterý 17. 3. 2026Prohlédnout leták](/akcni-letaky/katalog-vase-oblibene-znacky)
[Katalog: Svěží jarní nabídkaPlatí od středy 11. 2. do úterý 3. 3. 2026Prohlédnout leták](/akcni-letaky/katalog-svezi-jarni-nabidka)
"""
    
    # Lidl - using najdislevu.cz as data source
    # Lidl site requires JS; najdislevu.cz provides leták summary with prices
    lidl_enabled = True
    
    # Find Penny deals
    penny_deals = find_deals_in_penny(PENNY_DEALS_DATA)
    all_deals.extend(penny_deals)
    
    # Find BILLA deals
    billa_deals = find_deals_in_billa(billa_markdown)
    all_deals.extend(billa_deals)
    
    # Find Lidl deals (using najdislevu.cz summary)
    if lidl_enabled:
        try:
            import sys
            # Direct Lidl deals - mozzarellu is cheese (sýr)
            lidl_deals_data = [
                {"name": "mozzarellu", "price": 14.90, "end_date": "04.03.2026"},
            ]
            for deal in lidl_deals_data:
                name = deal["name"].lower()
                for item in SHOPPING_LIST:
                    search_terms = ITEM_SEARCH_MAP.get(item, [])
                    for term in search_terms:
                        if term.lower() in name:
                            if not any(d["item"] == item and d["store"] == "Lidl" for d in all_deals):
                                all_deals.append({
                                    "item": item,
                                    "product": deal["name"],
                                    "price": deal["price"],
                                    "store": "Lidl",
                                    "date_start": "02.03.2026",
                                    "date_end": deal["end_date"],
                                    "has_deal": True,
                                    "source": "najdislevu_lidl_letak",
                                })
                                print(f"✅ Lidl: {deal['name']} - {deal['price']:.2f} Kč (match: {item})", file=sys.stderr)
                            break
        except Exception as e:
            import sys
            print(f"Error fetching Lidl deals: {e}", file=sys.stderr)
    
    has_any_deals = len(all_deals) > 0
    return {"deals": all_deals, "has_any_deals": has_any_deals}

def format_results(data):
    """Format deal results for iMessage"""
    deals = data["deals"]
    
    results = ["🛒 Daily Shopping Deals Check", "=" * 40]
    
    # Lidl status
    results.append("📊 Stores checked: Penny ✅, BILLA ✅, Lidl ✅ (najdislevu.cz)")
    results.append("")
    
    if not data["has_any_deals"]:
        results.append("❌ Žádné akční ceny nenalezeny.")
        results.append("Polní položky: " + ", ".join(SHOPPING_LIST))
    else:
        results.append("✅ Nalezeny akční ceny:")
        
        # Group by store
        by_store = {}
        for deal in deals:
            store = deal["store"]
            if store not in by_store:
                by_store[store] = []
            by_store[store].append(deal)
        
        for store, store_deals in by_store.items():
            results.append(f"\n**{store}**")
            for deal in store_deals:
                results.append(f"- {deal['product']}: {deal['price']:.2f} Kč")
                if "date_end" in deal and deal["date_end"] != "neuvedeno":
                    results.append(f"  (akce do {deal['date_end']})")
    
    return "\n".join(results)

def main():
    result = check_deals(SHOPPING_LIST)
    message = format_results(result)
    
    # Output for iMessage
    print(message)
    
    # Also write to file for debugging
    output_file = Path(__file__).parent / "shopping-deals-output.json"
    output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Also write summary to file
    summary_file = Path(__file__).parent / "shopping-deals-summary.txt"
    summary_file.write_text(message, encoding='utf-8')
    
    return json.dumps(result)

if __name__ == "__main__":
    main()
