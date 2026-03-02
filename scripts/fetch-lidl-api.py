#!/usr/bin/env python3
"""
Fetch Lidl letak - find API endpoints
"""

import asyncio
from playwright.async_api import async_playwright

async def fetch_lidl_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture network requests
        api_requests = []
        
        def handle_request(request):
            url = request.url
            # Filter for API calls
            if 'api' in url.lower() or ' Akč' in url or ' akc' in url.lower():
                api_requests.append(url)
        
        page.on('request', handle_request)
        
        try:
            # Navigate to Lidl letak
            await page.goto('https://www.lidl.cz/c/akcni-letak/s10008644',
                wait_until='load',
                timeout=15000
            )
            
            # Wait for JS to load
            await page.wait_for_timeout(3000)
            
            # List API requests
            print(f"Found {len(api_requests)} potential API requests")
            for req in api_requests[:20]:
                print(f"  - {req}")
            
            # Check for fetch/XHR requests
            fetch_requests = await page.evaluate('''() => {
                const requests = [];
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    requests.push(args[0]);
                    return originalFetch.apply(this, args);
                };
                return requests;
            }''')
            
            print(f"Fetch requests: {len(fetch_requests)}")
            for req in fetch_requests[:10]:
                print(f"  - {req}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_lidl_api())
