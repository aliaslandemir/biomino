/* Browser regression checks. Tile requests are mocked unless SCREENSHOT is set. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const records = JSON.parse(fs.readFileSync(path.join(root, 'data/occurrences.json'), 'utf8'));
const server = http.createServer((request,response) => {
  const pathname = new URL(request.url, 'http://localhost').pathname;
  const file = pathname === '/docs/index.html' ? 'docs/index.html' : pathname === '/BiomiNO_map.html' || pathname === '/' ? 'BiomiNO_map.html' : null;
  if (!file) { response.writeHead(404); response.end(); return; }
  response.writeHead(200, {'Content-Type':'text/html; charset=utf-8'});
  fs.createReadStream(path.join(root,file)).pipe(response);
});
const countText = count => count.toLocaleString('en-GB');
(async () => {
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({headless:true,args:['--no-sandbox']});
    const context = await browser.newContext({viewport:{width:1440,height:960},deviceScaleFactor:1});
    if (!process.env.SCREENSHOT) {
      const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64');
      await context.route(/tile\.openstreetmap\.org/,route=>route.fulfill({contentType:'image/png',body:png}));
    }
    const errors = [];
    context.on('page', page=>page.on('pageerror', error=>errors.push(error.message)));
    const page = await context.newPage();
    await page.goto(`${base}/BiomiNO_map.html`);
    await page.waitForFunction(() => document.querySelector('#result-count').textContent !== '—');
    assert.equal(await page.locator('#result-count').innerText(),countText(records.length));
    assert.ok(await page.locator('.cluster-bubble').count()>0,'markers are clustered');
    if (process.env.SCREENSHOT) {
      await page.waitForFunction(()=>document.querySelectorAll('.leaflet-tile-loaded').length >= 8);
      await page.waitForTimeout(1500);
      assert.ok(await page.locator('#tile-warning').isHidden(),'screenshot basemap loaded');
      await page.screenshot({path:path.join(root,process.env.SCREENSHOT),fullPage:true});
    }
    await page.locator('#species').selectOption('Mytilus edulis');
    assert.equal(await page.locator('#result-count').innerText(),countText(records.filter(r=>r.species==='Mytilus edulis').length));
    await page.locator('#since').selectOption('2020');
    await page.locator('#precision').selectOption('1000');
    const expected = records.filter(r=>r.species==='Mytilus edulis' && r.year>=2020 && r.uncertainty_m != null && r.uncertainty_m<=1000);
    assert.equal(await page.locator('#result-count').innerText(),countText(expected.length));
    await page.reload();
    assert.equal(await page.locator('#result-count').innerText(),countText(expected.length),'URL preserves filters');
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export').click();
    const download = await downloadPromise;
    const geojson = JSON.parse(fs.readFileSync(await download.path(),'utf8'));
    assert.equal(geojson.features.length,expected.length);
    assert.ok(geojson.features.every(f=>f.properties.source && f.properties.license && f.properties.citation),'export keeps attribution');
    assert.deepEqual(geojson.features[0].geometry.coordinates,[expected[0].lon,expected[0].lat]);
    await page.locator('#results .record-row').first().click();
    await page.locator('.leaflet-popup-content .source-link').waitFor();
    assert.ok((await page.locator('.source-link').getAttribute('href')).startsWith('https://www.gbif.org/occurrence/'));
    await page.locator('.leaflet-popup-close-button').click();
    await page.locator('#view-grid').click();
    assert.equal(await page.locator('#view-grid').getAttribute('aria-pressed'),'true');
    assert.ok(await page.locator('.leaflet-overlay-pane path').count()===0,'grid uses canvas');
    assert.ok(await page.locator('.leaflet-overlay-pane canvas').count()>0);
    await page.locator('#reset').click();
    await page.locator('#search').fill('no-such-species-12345');
    await page.waitForFunction(()=>document.querySelector('#result-count').textContent==='0');
    assert.ok(await page.locator('#export').isDisabled());
    assert.match(await page.locator('.empty').innerText(),/No records/);
    await page.locator('#reset').click();
    await page.locator('#group-filters input').evaluateAll(inputs=>inputs.forEach(input=>{input.checked=false;input.dispatchEvent(new Event('change',{bubbles:true}));}));
    assert.equal(await page.locator('#result-count').innerText(),'0');
    await page.reload();
    assert.equal(await page.locator('#result-count').innerText(),'0','empty group selection survives reload');
    await page.locator('#reset').click();
    await page.locator('#search').fill('Bergen');
    const bergen = records.filter(r=>[r.species,r.common_name,r.locality,r.dataset,r.recorded_by].join(' ').toLowerCase().includes('bergen'));
    await page.waitForFunction(count=>document.querySelector('#result-count').textContent===count,countText(bergen.length));
    await page.locator('#about-open').click();
    assert.ok(await page.locator('#about').isVisible());
    await page.keyboard.press('Escape');
    assert.ok(await page.locator('#about').isHidden());
    const mobile = await context.newPage();
    await mobile.setViewportSize({width:390,height:844});
    await mobile.goto(`${base}/docs/index.html`);
    assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile has no horizontal overflow');
    assert.ok(await mobile.locator('#sidebar').isHidden());
    await mobile.locator('#mobile-filters').click();
    assert.equal(await mobile.locator('#mobile-filters').getAttribute('aria-expanded'),'true');
    await mobile.locator('#species').selectOption('Magallana gigas');
    await mobile.locator('#results .record-row').first().click();
    await mobile.locator('.source-link').waitFor();
    assert.ok(await mobile.locator('#sidebar').isHidden(),'record selection closes drawer');
    await mobile.locator('.leaflet-popup-close-button').click();
    await mobile.locator('#view-grid').click();
    await mobile.waitForFunction(()=>!document.querySelector('.leaflet-popup'));
    if (process.env.SCREENSHOT) await mobile.screenshot({path:'/tmp/biomino-mobile.png',fullPage:true});
    assert.deepEqual(errors,[],'no browser exceptions');
    console.log(`Browser checks passed: ${records.length} records; filters, permalink, export, popups, grid, empty state, mobile.`);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
