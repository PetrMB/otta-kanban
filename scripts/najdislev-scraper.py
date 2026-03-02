#!/usr/bin/env python3
"""
Fetch Lidl letak via najdislevu.cz - direct scraping
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def extract_lidl_from_najdislevu():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to najdislevu lidl letak
            await page.goto('https://letaky.najdislevu.cz/lidl/letaksh/48165/1/',
                wait_until='load',
                timeout=15000
            )
            
            # Wait for JS
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            await page.screenshot(path='/Users/otto/.openclaw/workspace/najdislev-lidl.png')
            
            # Get page text
            page_text = await page.evaluate('() => document.body.innerText')
            
            print("Body text preview:", page_text[:2000])
            
            # Look for price patterns
            prices = re.findall(r'(\d+[,]\d+)\s*Kč', page_text)
            print(f"\nFound {len(prices)} prices")
            
            if len(prices) > 0:
                print("Sample prices:", prices[:20])
            
            # Look for product names with prices
            # Pattern: name - price or name followed by price
            # Try different patterns
            patterns = [
                r'([A-Z][a-zA-ZÁÉÍÓÚÝČĎŇŘŠŤŽůúýžčďňřšťž\s,.-]{5,50})\s*[-:]\s*(\d+[,]\d+)\s*Kč',
                r'(.{10,50})\s*(\d+[,]\d+)\s*Kč.*?(\d+\.\d+\.\d+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                if len(matches) > 0:
                    print(f"\nPattern found {len(matches)} matches")
                    for m in matches[:10]:
                        print(f"  - {m}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_lidl_from_najdislevu())
