#!/usr/bin/env python3
"""
Fetch Lidl letak - direct approach
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def fetch_lidl_letak():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to Lidl letak with shorter timeout
            await page.goto('https://www.lidl.cz/c/akcni-letak/s10008644',
                wait_until='load',
                timeout=15000
            )
            
            # Small wait for JS
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            await page.screenshot(path='/Users/otto/.openclaw/workspace/lidl-letak.png')
            
            # Get page content
            content = await page.content()
            
            # Save raw HTML
            with open('/Users/otto/.openclaw/workspace/lidl-letak.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Saved lidl-letak.png and lidl-letak.html")
            print(f"Content length: {len(content)} chars")
            
            # Look for price patterns in content
            prices = re.findall(r'(\d+[,]\d+)\s*Kč', content)
            print(f"Found {len(prices)} prices in HTML")
            
            if len(prices) > 0:
                print("Sample prices:", prices[:10])
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_lidl_letak())
