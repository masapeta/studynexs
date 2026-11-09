/**
 * Targeted POC-parity checks (A5, A7, A8, A9, A15, A20) for rows not yet browser-evidenced.
 * Disposable e2e tenant only; API must run with AI_DEFAULT_PROVIDER=e2e_scripted.
 *   node e2e-p2-parity-gaps.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3010";
const FX = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), "studynexs_e2e_fixture.json"), "utf8"));
if (!/^e2e-/.test(FX.tenant_slug)) throw new Error("Refusing: fixture tenant must start with e2e-");
const OUT = process.env.E2E_OUT || path.join(os.tmpdir(), `sn-parity-${Date.now()}`);
fs.mkdirSync(OUT, { recursive: true });

const results = [];
const errors = [];
function record(row, check, ok, detail = "") {
  results.push({ row, check, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"} [${row}] ${check}${detail ? ` — ${detail}` : ""}`);
}
async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(400);
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript((slug) => sessionStorage.setItem("sn_prospect_tenant_slug", slug), FX.tenant_slug);
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  const p = FX.personas.principal;
  await page.goto(`${BASE}/login?portal=staff`, { waitUntil: "domcontentloaded" });
  await page.locator("#username-input").waitFor({ timeout: 15000 }).catch(async () => {
    await page.getByRole("button", { name: /Username & password/i }).click();
  });
  await page.fill("#username-input", p.username);
  await page.fill("#password-input", p.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 45000 });

  // A8 + A15: auto-title from first message; "Open {page}" carries ?from.
  await page.goto(`${BASE}/dashboard/assistant`, { waitUntil: "domcontentloaded" });
  await settle(page);
  const box = page.getByLabel("Message StudyNexs");
  await box.fill("fee collection");
  await box.press("Enter");
  await page.getByRole("button", { name: "Open finance" }).waitFor({ timeout: 45000 });
  const sid = (/\/assistant\/c\/([0-9a-f-]{36})/.exec(page.url()) || [])[1];
  await page.getByRole("button", { name: "Open finance" }).click();
  await page.waitForURL(/\/dashboard\/finance\/fees/, { timeout: 20000 }).catch(() => {});
  await settle(page);
  record("A15", "\"Open finance\" lands on Fees keeping ?from=c/{id}",
         /\/finance\/fees\?from=c%2F[0-9a-f-]{36}/.test(page.url()), page.url().replace(BASE, ""));
  const back = page.getByTestId("back-to-conversation");
  record("A15", "\"Back to conversation\" chip on the landed page", await back.isVisible({ timeout: 10000 }).catch(() => false));
  await page.screenshot({ path: path.join(OUT, "a15-open-finance.png"), fullPage: true });
  await back.click();
  await page.waitForURL(new RegExp(`/assistant/c/${sid}`), { timeout: 20000 });
  await settle(page);

  // A9: context bar chips + Clear.
  const bar = page.getByRole("group", { name: "Conversation context" });
  const barVisible = await bar.isVisible().catch(() => false);
  record("A9", "context bar shows chips for the conversation", barVisible, barVisible ? (await bar.innerText()).replace(/\s+/g, " ").slice(0, 80) : "no chips");

  // A5 + A7 + A8: list, date group, search, rename, archive/restore.
  await page.getByRole("button", { name: "Conversations" }).click();
  const list = page.getByRole("dialog", { name: "Conversations" });
  await list.waitFor({ timeout: 10000 });
  await list.getByText("fee collection").first().waitFor({ timeout: 10000 }).catch(() => {});
  record("A8", "conversation auto-titled from the first message", await list.getByText("fee collection").first().isVisible().catch(() => false));
  record("A7", "date group heading \"Today\"", await list.getByText("Today", { exact: true }).isVisible().catch(() => false));
  record("A5", "conversation list opens with current conversation marked", (await list.locator("[aria-current='page']").count()) >= 1);
  const search = list.getByRole("textbox", { name: "Search conversations" });
  await search.fill("zzz-no-match");
  record("A7", "search filters conversations", await list.getByText(/No conversations match/).isVisible().catch(() => false));
  await search.fill("fee");
  await list.getByRole("button", { name: /^Rename fee collection/ }).first().click();
  const title = list.getByRole("textbox", { name: "Conversation title" });
  await title.fill("Fees this term");
  await list.getByRole("button", { name: "Save" }).click();
  await list.getByText("Fees this term").first().waitFor({ timeout: 10000 }).catch(() => {});
  record("A7", "rename persists", await list.getByText("Fees this term").first().isVisible().catch(() => false));
  await page.screenshot({ path: path.join(OUT, "a5-a7-conversations.png"), fullPage: true });
  record("A7", "pin control", (await list.getByRole("button", { name: /^Pin / }).count()) > 0, "not implemented");
  await page.keyboard.press("Escape");

  // A20: ⌘K / Ctrl+K opens search; finds classes and conversations.
  await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.keyboard.press("Control+K");
  const combo = page.getByRole("combobox");
  const opened = await combo.isVisible({ timeout: 5000 }).catch(() => false);
  record("A20", "Ctrl+K opens global search", opened);
  if (opened) {
    await combo.fill("7-A");
    await page.getByRole("option").first().waitFor({ timeout: 10000 }).catch(() => {});
    const classHit = await page.getByRole("option", { name: /7 - A/ }).first().isVisible().catch(() => false);
    record("A20", "search returns the class", classHit);
    await combo.fill("Fees this");
    await page.getByRole("option", { name: /Fees this term/ }).first().waitFor({ timeout: 10000 }).catch(() => {});
    record("A20", "search returns the conversation", await page.getByRole("option", { name: /Fees this term/ }).first().isVisible().catch(() => false));
    await combo.fill("Ravi");
    await page.getByRole("option", { name: /Ravi Student/ }).first().waitFor({ timeout: 10000 }).catch(() => {});
    record("A20", "search returns a student (principal scope)", await page.getByRole("option", { name: /Ravi Student/ }).first().isVisible().catch(() => false));
    await page.screenshot({ path: path.join(OUT, "a20-search.png"), fullPage: true });
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 2));
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} parity checks passed; console/page errors=${errors.length}; evidence: ${OUT}`);
  for (const e of errors.slice(0, 10)) console.log(`  ERR ${e.slice(0, 160)}`);
  process.exit(0);
})().catch((e) => {
  console.error("HARNESS ERROR:", e);
  process.exit(2);
});
