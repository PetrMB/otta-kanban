const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Navigate to Lidl letak with shorter timeout
  await page.goto('https://www.lidl.cz/c/akcni-letak/s10008644', { 
    waitUntil: 'domcontentloaded',
    timeout: 15000
  });
  
  // Get page HTML
  const html = await page.content();
  console.log('HTML length:', html.length);
  console.log(html.substring(0, 3000));
  
  await browser.close();
})();
