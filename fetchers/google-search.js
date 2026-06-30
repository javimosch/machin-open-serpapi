// Fetcher plugin (layer 1): google organic.
//   node google-search.js "<query>"   ->  rendered SERP HTML on stdout
//
// Google's server-side HTML is consent/JS-walled, so we render with a real
// browser. open-serpapi then parses the HTML into SerpApi organic_results.
//
// Needs puppeteer + a Chrome. Reuses the install under ~/ai/google-maps-scraper:
//   NODE_PATH=~/ai/google-maps-scraper/node_modules \
//   PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome \
//   node fetchers/google-search.js "machin programming language"
const puppeteer = require('puppeteer');

(async () => {
  const query = process.argv[2];
  if (!query) { console.error('usage: google-search.js "<query>"'); process.exit(2); }
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    await page.setCookie({ name: 'CONSENT', value: 'YES+', domain: '.google.com', path: '/', expires: Date.now() + 31536000000 });
    const url = 'https://www.google.com/search?q=' + encodeURIComponent(query) + '&num=10&hl=en&gl=us';
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
    // Dismiss a consent dialog if one still appears.
    try {
      const btn = await page.$('button[aria-label="Accept all"], #L2AGLb');
      if (btn) { await btn.click(); await page.waitForNetworkIdle({ timeout: 5000 }).catch(() => {}); }
    } catch (e) {}
    process.stdout.write(await page.content());
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
