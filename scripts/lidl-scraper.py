#!/usr/bin/env python3
"""
Lidl Czech Republic Leták Scraper
Uses Playwright to scrape current deals from Lidl leták
"""

import asyncio
from playwright.async_api import async_playwright
import re
import json

# Czech mapping of items to common search terms
ITEM_SEARCH_MAP = {
    "milk": ["mléko", "mleko"],
    "bread": ["chléb", "chleba"],
    "eggs": ["vejce"],
    "cheese": ["sýr", "syr"],
    "vegetables": ["zelenina"],
}

SHOPPING_LIST = [
    "milk",
    "bread",
    "eggs",
    "cheese",
    "vegetables",
]

async def scrape_lidl():
    """Scrape Lidl Czech Republic leták for deals"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to Lidl letak
            await page.goto('https://www.lidl.cz/c/akcni-letak/s10008644', 
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(3000)
            
            # Get page HTML
            content = await page.content()
            
            # Extract product prices using regex
            # Pattern: product name -> price
            pattern = r'([A-Z][a-zA-ZÁÉÍÓÚÝČĎŇŘŠŤŽůúýžčďňřšťž]+[^<]*?)\s*(\d+[,]\d+)\s*Kč'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            deals = []
            for name, price in matches[:20]:  # Limit to first 20
                name = name.strip()
                price_val = float(price.replace(",", "."))
                
                # Check if matches shopping list
                for item in SHOPPING_LIST:
                    if any(search_term.lower() in name.lower() for search_term in ITEM_SEARCH_MAP.get(item, [])):
                        deals.append({
                            "item": item,
                            "product": name,
                            "price": price_val,
                            "store": "Lidl",
                            "date_start": "02.03.2026",
                            "date_end": "08.03.2026",
                            "has_deal": True,
                            "source": "lidl_letak",
                        })
                        break
            
            await browser.close()
            return deals
            
        except Exception as e:
            print(f"Error: {e}")
            await browser.close()
            return []

def main():
    """Main function"""
    deals = asyncio.run(scrape_lidl())
    
    if deals:
        print(f"✅ Found {len(deals)} deals in Lidl:")
        for deal in deals:
            print(f"- {deal['product']}: {deal['price']:.2f} Kč")
    else:
        print("❌ No deals found or scraping failed")
    
    # Write to JSON
    with open('/Users/otto/.openclaw/workspace/scripts/lidl-deals-output.json', 'w', encoding='utf-8') as f:
        json.dump({"deals": deals, "has_any_deals": len(deals) > 0}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
