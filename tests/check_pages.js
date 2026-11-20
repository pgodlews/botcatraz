// Opens a sample build in a headless browser and checks that the front page, a
// cells page and a yard run without errors and show every robot type.
//
//   ./build.py --sample
//   npm install --no-save playwright && npx playwright install chromium
//   node tests/check_pages.js [WWW_DIR]          (default: www)
//
// PW_CHANNEL=chrome uses an installed Google Chrome instead of Playwright's Chromium.
"use strict";
const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const www = path.resolve(process.argv[2] || path.join(root, "www"));
const types = fs.readdirSync(path.join(root, "yard/art/robots")).filter(f => /^robot-\d+\.png$/.test(f)).length;
const MIME = { ".html": "text/html", ".json": "application/json", ".js": "text/javascript", ".png": "image/png" };

const server = http.createServer((req, res) => {
  let file = path.join(www, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!file.startsWith(www)) { res.writeHead(403).end(); return; }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
  fs.readFile(file, (err, body) => {
    if (err) { res.writeHead(404).end(); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" }).end(body);
  });
});

let failures = 0;
function check(ok, what) {
  console.log(`${ok ? "ok  " : "FAIL"} ${what}`);
  if (!ok) failures++;
}

async function open(context, base, url) {
  const page = await context.newPage();
  const problems = [];
  page.on("pageerror", e => problems.push(`page error: ${e.message}`));
  // Failed loads are reported once, with their address, by the response handler.
  page.on("console", m => { if (m.type() === "error" && !m.text().startsWith("Failed to load resource")) problems.push(`console: ${m.text()}`); });
  page.on("response", r => {
    const u = new URL(r.url());
    if (r.url().startsWith(base) && r.status() >= 400 && u.pathname !== "/favicon.ico") problems.push(`${r.status()} ${u.pathname}`);
  });
  await page.goto(base + url, { waitUntil: "load" });
  return { page, problems };
}

const brokenImages = page => page.evaluate(() => [...document.images].filter(i => i.complete && !i.naturalWidth).length);

(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {});
  // One context, so the pages share localStorage as they would in one browser.
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light" });
  try {
    {
      const { page, problems } = await open(context, base, "/");
      const links = await page.evaluate(() => [...document.querySelectorAll("a")].map(a => a.getAttribute("href")));
      check(["sample1", "sample2"].every(s => links.some(h => h && h.includes(s))), "front page links to both sample servers");
      check(problems.length === 0, `front page without errors ${problems.join("; ")}`);
      await page.close();
    }
    {
      const { page, problems } = await open(context, base, "/sample1/");
      await page.waitForTimeout(1000);
      check(await page.evaluate(() => MUGS && MUGS.front.length) === types, `cells page has ${types} booking photos`);
      check(await brokenImages(page) === 0, "cells page has no broken images");
      check(problems.length === 0, `cells page without errors ${problems.join("; ")}`);
      await page.close();
    }
    {
      const { page, problems } = await open(context, base, "/sample1/yard.html");
      await page.waitForFunction(n => sheets.filter(s => s && s.complete && s.naturalWidth).length === n, types, { timeout: 15000 })
        .then(() => check(true, `yard loaded all ${types} robot sheets`), () => check(false, `yard loaded all ${types} robot sheets`));
      await page.waitForTimeout(2000);
      const inside = await page.evaluate(() => (robots instanceof Map ? robots.size : Object.keys(robots).length));
      check(inside > 0, `yard has robots (${inside})`);
      await page.getByRole("button", { name: /replay last arrival/i }).click();
      await page.waitForTimeout(3000);
      check(problems.length === 0, `yard and replay without errors ${problems.join("; ")}`);
      await page.close();
    }
    {
      // Lights out on one page switches the theme there, is remembered for the other
      // pages, and reaches a page that is already open.
      const theme = page => page.evaluate(() => [document.documentElement.dataset.theme || "", document.getElementById("lights").textContent]);
      const front = await open(context, base, "/");
      const yard = await open(context, base, "/sample1/yard.html");
      check(JSON.stringify(await theme(front.page)) === JSON.stringify(["", "Lights out"]), "front page follows the system theme at first");
      await front.page.click("#lights");
      check(JSON.stringify(await theme(front.page)) === JSON.stringify(["dark", "Day shift"]), "Lights out turns the front page dark");
      await yard.page.waitForTimeout(300);
      check(JSON.stringify(await theme(yard.page)) === JSON.stringify(["dark", "Day shift"]), "an open yard turns dark with it");
      const cells = await open(context, base, "/sample2/");
      check(JSON.stringify(await theme(cells.page)) === JSON.stringify(["dark", "Day shift"]), "a cells page opened later starts dark");
      await cells.page.click("#lights");
      await front.page.waitForTimeout(300);
      check(JSON.stringify(await theme(front.page)) === JSON.stringify(["light", "Lights out"]), "Day shift on the cells page lights the front page again");
      const problems = [...front.problems, ...yard.problems, ...cells.problems];
      check(problems.length === 0, `theme switching without errors ${problems.join("; ")}`);
      for (const o of [front, yard, cells]) await o.page.close();
    }
  } finally {
    await browser.close();
    server.close();
  }
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
