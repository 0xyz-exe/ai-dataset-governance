const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function run() {
  const outDir = path.resolve(__dirname, '../docs/screenshots');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  console.log('Navigating to app...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // 1. Overview
  await page.screenshot({ path: path.join(outDir, 'overview.png') });
  console.log('Captured overview.png');

  // Helper function to click sidebar tab
  async function clickNav(text) {
    const btn = page.locator(`button:has-text("${text}")`).first();
    await btn.click();
    await page.waitForTimeout(800);
  }

  // 2. Datasets
  await clickNav('Dataset Registry');
  await page.screenshot({ path: path.join(outDir, 'datasets.png') });
  console.log('Captured datasets.png');

  // 3. Detail / Explorer
  await clickNav('Dataset Explorer');
  await page.screenshot({ path: path.join(outDir, 'explorer.png') });
  console.log('Captured explorer.png');

  // Subtab: Quality
  const qSub = page.locator('button:has-text("Quality Checks")').first();
  if (await qSub.count() > 0) {
    await qSub.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: path.join(outDir, 'quality.png') });
    console.log('Captured quality.png');
  }

  // Subtab: Provenance
  const pSub = page.locator('button:has-text("Lineage Graph")').first();
  if (await pSub.count() > 0) {
    await pSub.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: path.join(outDir, 'lineage.png') });
    console.log('Captured lineage.png');
  }

  // 4. Compare
  await clickNav('Version Comparison');
  const runCompareBtn = page.locator('button:has-text("Run Differential Comparison")').first();
  if (await runCompareBtn.count() > 0) {
    await runCompareBtn.click();
    await page.waitForTimeout(800);
  }
  await page.screenshot({ path: path.join(outDir, 'compare.png') });
  console.log('Captured compare.png');

  // 5. ML Experiments
  await clickNav('ML Experiments');
  await page.screenshot({ path: path.join(outDir, 'experiments.png') });
  console.log('Captured experiments.png');

  // 6. Governance & Audit
  await clickNav('Governance & Audit');
  await page.screenshot({ path: path.join(outDir, 'governance.png') });
  console.log('Captured governance.png');

  await browser.close();
  console.log('All screenshots captured successfully.');
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
