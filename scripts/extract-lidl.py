#!/usr/bin/env python3
"""
Fetch Lidl letak - extract products via DOM
"""

import asyncio
from playwright.async_api import async_playwright

async def extract_lidl_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate
            await page.goto('https://www.lidl.cz/c/akcni-letak/s10008644',
                wait_until='load',
                timeout=15000
            )
            
            # Wait
            await page.wait_for_timeout(2000)
            
            # Try to get product elements via various selectors
            selectors = [
                'a[href*="/products/"]',
                '[class*="product"]',
                '[class*="card"]',
                '.card',
                '.product',
            ]
            
            products = []
            
            for sel in selectors:
                elements = await page.query_selector_all(sel)
                print(f"Selector '{sel}': {len(elements)} elements")
                
                if len(elements) > 0:
                    for elem in elements[:5]:
                        text = await elem.inner_text()
                        if text and len(text) > 0 and len(text) < 200:
                            products.append(text)
            
            print(f"\nFound {len(products)} potential product strings")
            for p in products[:20]:
                print(f"  - {p[:100]}")
            
            # Also get all visible text from page
            page_text = await page.evaluate('() => document.body.innerText')
            
            # Try to find product-price pairs
            import re
            # Common pattern: name followed by price
            pattern = r'([A-Z][a-zA-ZÁÉÍÓÚÝČĎŇŘŠŤŽůúýžčďňřšťž\s,.-]+?)\s*(\d+[,]\d+)\s*Kč'
            matches = re.findall(pattern, page_text)
            
            print(f"\nPrice patterns found: {len(matches)}")
            for name, price in matches[:15]:
                print(f"  - {name.strip()}: {price} Kč")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_lidl_products())
