#!/usr/bin/env node
/* Renders og.png (1200x630) from scripts/og/og.html, which draws the same scene as the page (assets/scene.js).
   Needs playwright and a Chromium:  node scripts/make_og.js
   The light theme is forced so the card does not depend on the machine that renders it. */
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, colorScheme: 'light', deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'og/og.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.resolve(__dirname, '..', 'og.png') });
  await browser.close();
  console.log('wrote og.png');
})();
