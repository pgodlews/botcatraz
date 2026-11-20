// Takes the README screenshots (docs/front.png, cells.png, yard.png) from a running
// site, with the dates and times of day blanked out and only the first half of every
// address left: 203.0.•.• and 2001:db8:0:0:•:•:•:•.
//
//   node docs/take_screenshots.js BASE_URL SERVER_ID
//   node docs/take_screenshots.js http://127.0.0.1:8850 sample2
//
// Needs Playwright (npm install --no-save playwright && npx playwright install chromium).
// PW_CHANNEL=chrome uses an installed Google Chrome instead.
//
// The blanking covers text only. Read every picture before you commit it: network
// names, countries, user names tried and request paths stay as they are.
"use strict";
const path = require("path");
const { chromium } = require("playwright");

const [base, server] = process.argv.slice(2);
if (!base || !server) {
  console.error("usage: node docs/take_screenshots.js BASE_URL SERVER_ID");
  process.exit(2);
}
const out = __dirname;

// Runs in the page: rewrites every text node, including the SVG placards.
function mask() {
  const month = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*";
  const rules = [
    [/\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?/g, "••••-••-•• ••:••:••"],
    [/\b\d{4}-\d{2}-\d{2}\b/g, "••••-••-••"],
    [new RegExp("\\b\\d{1,2} " + month + "\\b", "gi"), "•• •••"],
    [new RegExp("\\b" + month + " \\d{1,2}\\b", "gi"), "••• ••"],
    [/\b\d{1,2}:\d{2}(?::\d{2})?\b/g, "••:••"],
    [/\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b/g, "$1.$2.•.•"],
  ];
  const v6 = t => {
    if ((t.match(/:/g) || []).length < 2) return null;
    try { new URL("http://[" + t + "]"); } catch (e) { return null; }
    const [a, b] = t.split("::");
    const head = a ? a.split(":") : [], tail = b ? b.split(":") : [];
    const full = b === undefined ? head : [...head, ...Array(8 - head.length - tail.length).fill("0"), ...tail];
    return full.slice(0, 4).join(":") + ":•:•:•:•";
  };
  const fix = s => {
    for (const [re, to] of rules) s = s.replace(re, to);
    return s.replace(/(?<![\w:])[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4}){2,7}(?![\w:])/g, t => v6(t) ?? t);
  };
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node; (node = walk.nextNode());) {
    const t = fix(node.nodeValue);
    if (t !== node.nodeValue) node.nodeValue = t;
  }
}

(async () => {
  const browser = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {});
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light" });
  async function shot(url, file, height, prepare) {
    const page = await context.newPage();
    await page.goto(base + url, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    if (prepare) await prepare(page);
    await page.evaluate(mask);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(out, file), fullPage: true, clip: { x: 0, y: 0, width: 1280, height } });
    console.log("wrote docs/" + file);
    await page.close();
  }
  try {
    await shot("/", "front.png", 560);
    await shot(`/${server}/`, "cells.png", 1250, async page => {
      await page.waitForTimeout(1500);
      await page.locator(".cell .door").first().click();   // open the first rap sheet
      await page.waitForTimeout(1500);
    });
    await shot(`/${server}/yard.html`, "yard.png", 1120, page => page.waitForTimeout(8000));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
