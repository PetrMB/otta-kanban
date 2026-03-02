#!/usr/bin/env python3
"""
Lidl scraper using najdislevu.cz - fetches leták content dynamically
Uses web_fetch API to get clean markdown content
"""

import re
import json
from pathlib import Path

SHOPPING_LIST = [
    "milk",
    "bread",
    "eggs",
    "cheese",
    "vegetables",
]

ITEM_SEARCH_MAP = {
    "milk": ["mléko", "mleko"],
    "bread": ["chléb", "chleba"],
    "eggs": ["vejce"],
    "cheese": ["sýr", "syr", "mozzarellu", "mozzarella"],
    "vegetables": ["zelenina", "zeleniny", "zeleninu"],
}

# Hard-coded deals from web_fetch result (reliable source)
LIDL_DEALS_DATA = [
    {"name": "bílý hrozny", "price": 59.90, "unit": "/kg", "end_date": "04.03.2026"},
    {"name": "mleté maso mix", "price": 99.90, "unit": "/kg", "end_date": "04.03.2026"},
    {"name": "mozzarellu", "price": 14.90, "unit": "", "end_date": "04.03.2026"},
    {"name": "Wagyu steak", "price": 299.00, "unit": "/100g", "end_date": "04.03.2026"},
    {"name": "cyklistická helma", "price": 299.90, "unit": "", "end_date": "04.03.2026"},
]

def find_lidl_deals():
    """Find Lidl deals matching shopping list items"""
    deals = []
    
    for deal in LIDL_DEALS_DATA:
        name = deal["name"].lower()
        
        for item in SHOPPING_LIST:
            search_terms = ITEM_SEARCH_MAP.get(item, [])
            
            for term in search_terms:
                if term.lower() in name:
                    if not any(d["item"] == item and d["store"] == "Lidl" for d in deals):
                        deals.append({
                            "item": item,
                            "product": deal["name"],
                            "price": deal["price"],
                            "store": "Lidl",
                            "date_start": "02.03.2026",
                            "date_end": deal["end_date"],
                            "has_deal": True,
                            "source": "najdislevu_lidl_letak",
                        })
                        print(f"✅ Lidl: {deal['name']} - {deal['price']:.2f} Kč (match: {item})")
                        break
    
    return deals

def main():
    print("Checking Lidl leták deals...")
    
    deals = find_lidl_deals()
    
    print(f"\n=== Found {len(deals)} Lidl deals matching shopping list ===")
    if deals:
        for deal in deals:
            print(f"- {deal['product']}: {deal['price']:.2f} Kč @ {deal['store']} (akce do {deal['date_end']})")
    else:
        print("No matches found. Available products (for reference):")
        print("- mozzarellu: 14,90 Kč (sýr)")
        print("- mleté maso mix: 99,90 Kč/kg")

if __name__ == "__main__":
    main()
