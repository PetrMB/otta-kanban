#!/usr/bin/env python3
"""
Test Lidl scraper with Playwright - simplified version
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_lidl():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to Lidl letak - simpler, shorter timeout
            await page.goto('https://www.lidl.cz/', 
                wait_until='domcontentloaded',
                timeout=15000
            )
            
            # Take a screenshot to verify it worked
            await page.screenshot(path='/Users/otto/.openclaw/workspace/lidl-screenshot.png')
            
            print("✅ Browser works! Screenshot saved.")
            print(f"Page title: {await page.title()}")
            
            # Check if we can find price patterns
            content = await page.content()
            
            # Look for price patterns
            prices = re.findall(r'(\d+[,]\d+)\s*Kč', content)
            print(f"Found {len(prices)} price patterns on homepage")
            
            if prices:
                print("Sample prices:", prices[:10])
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_lidl())
