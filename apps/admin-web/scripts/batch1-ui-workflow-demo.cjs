/**
 * Batch 1 — full 11-step Admin UI workflow (merged curriculum UI).
 * Requires API :8000 and admin-web (E2E_BASE_URL, default :3005).
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://localhost:3003";
const OUT = path.join(__dirname, "..", "..", "..", "docs", "product", "batch1-ui-demo");
const stamp = Date.now();
const results = [];

function pass(step, note = "") {
  results.push({ step, ok: true, note });
  console.log(`✓ Step ${step}: ${note || "OK"}`);
}
function fail(step, note) {
  results.push({ step, ok: false, note });
  console.log(`✗ Step ${step}: ${note}`);
}

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function login(page) {
  await page.goto(`${BASE}/login?portal=staff`, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForTimeout(1500);
  try {
    await page.waitForSelector("#username-input", { timeout: 20000 });
  } catch {
    await page.getByRole("button", { name: /Username & password/i }).click({ force: true });
    await page.waitForSelector("#username-input", { timeout: 30000 });
  }
  await page.fill("#username-input", "principal");
  await page.fill("#password-input", "Demo@1234");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL("**/dashboard**", { timeout: 90000, waitUntil: "commit" });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));

  try {
    // 1 Login
    await login(page);
    await shot(page, "01-login");
    pass(1, "Logged in as principal");

    // 2 Curriculum — create pack (merged or legacy UI)
    await page.goto(`${BASE}/dashboard/teaching/curriculum`, { waitUntil: "domcontentloaded" });
    await page.getByText(/Curriculum management|Curriculum packs/i).first().waitFor({ timeout: 60000 });
    if (await page.getByText("Something went wrong").isVisible().catch(() => false)) {
      fail(2, `Curriculum page error: ${errors.join("; ")}`);
    } else {
      const bookTitle = `Batch1 Demo ${stamp}`;
      const toggleBtn = page.getByRole("button", { name: /New draft pack|Create draft pack|Hide create form/i }).first();
      if (await toggleBtn.isVisible().catch(() => false)) {
        const label = await toggleBtn.innerText().catch(() => "");
        if (!/hide/i.test(label)) await toggleBtn.click();
      }
      const bookInput = page.locator("#pack-book, #edit-book").or(page.getByLabel("Book title")).first();
      await bookInput.waitFor({ timeout: 30000 });
      await bookInput.fill(bookTitle);
      if (await page.getByRole("button", { name: /Save draft pack/i }).isVisible().catch(() => false)) {
        await page.getByRole("button", { name: /Save draft pack/i }).click();
      } else {
        await page.getByRole("button", { name: /New draft pack/i }).click();
      }
      await page.getByText(/Add content|Add chapter/i).first().waitFor({ timeout: 60000 });
      await shot(page, "02-pack-created");
      pass(2, `Created draft pack ${bookTitle}`);
    }

    // 3 Add chapter
    const chTitle = `Algebra ${stamp}`;
    const chapterTitle = page.locator("#chapter-title").or(page.getByPlaceholder("e.g. Algebra")).first();
    await chapterTitle.waitFor({ timeout: 30000 });
    await chapterTitle.fill(chTitle);
    await page.getByRole("button", { name: "Add chapter", exact: true }).click();
    await page.waitForTimeout(1500);
    await shot(page, "03-chapter-added");
    pass(3, `Added chapter ${chTitle}`);

    // 4 Add topic
    const topicTitle = "Linear Equations";
    await page.getByPlaceholder("e.g. Linear Equations").fill(topicTitle);
    await page.getByRole("button", { name: "Add topic", exact: true }).click();
    await page.waitForTimeout(1500);
    await shot(page, "04-topic-added");
    pass(4, `Added topic ${topicTitle}`);

    // 5 Add learning outcome
    await page.getByPlaceholder("LO-1").fill("LO-1");
    await page.getByPlaceholder("Student can…").fill("Solve linear equations in one variable");
    await page.getByRole("button", { name: /Add learning outcome/i }).click();
    await page.waitForTimeout(1500);
    await shot(page, "05-learning-outcome-added");
    pass(5, "Added learning outcome");

    // 6 Save draft metadata
    await page.getByRole("button", { name: /Save draft/i }).click();
    await page.waitForTimeout(1500);
    await shot(page, "06-draft-saved");
    pass(6, "Saved draft metadata");

    // 7 Edit draft — change topic title inline
    const topicInput = page.locator('input[aria-label^="Topic Linear"]').first();
    if (await topicInput.count()) {
      await topicInput.fill("Linear Equations (edited)");
      await topicInput.blur();
      await page.waitForTimeout(1500);
      await shot(page, "07-draft-edited");
      pass(7, "Edited topic title on blur");
    } else {
      fail(7, "Topic edit input not found");
    }

    // 8 Approve pack
    await page.getByRole("button", { name: /Approve pack/i }).click();
    await page.waitForTimeout(2500);
    await shot(page, "08-pack-approved");
    pass(8, "Approved pack");

    // 9 Audit trail
    await page.waitForTimeout(500);
    const auditText = await page.locator("body").innerText();
    if (auditText.includes("Pack approved") || auditText.includes("Chapter added")) {
      await shot(page, "09-audit-trail");
      pass(9, "Audit trail visible");
    } else {
      fail(9, "Audit events not visible");
    }

    // 10 Lesson plan with pack (template + grounding default)
    await page.goto(`${BASE}/dashboard/teaching/lesson-plans`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    await page.getByPlaceholder("e.g. Linear Equations").fill("Linear Equations (edited)");
    await page.getByRole("button", { name: /^Generate$/i }).click();
    await page.waitForTimeout(12000);
    const lpBody = await page.locator("body").innerText();
    if (lpBody.includes("Curriculum grounding") && lpBody.includes("Grounded")) {
      await shot(page, "10-lesson-plan-grounded");
      pass(10, "Lesson plan shows grounding badge");
    } else {
      await shot(page, "10-lesson-plan-FAIL");
      fail(10, "Lesson plan missing grounding badge");
    }

    // 11 Question paper with grounding toggle
    await page.goto(`${BASE}/dashboard/teaching/ai-papers`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    const groundingSelect = page.getByLabel(/Grounding|Approved syllabus/i).first();
    if (await groundingSelect.isVisible().catch(() => false)) {
      await groundingSelect.selectOption?.({ label: /Grounded|Approved/i }).catch(() => {});
    }
    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: /Generate paper/i }).click();
    await page.waitForTimeout(90000);
    const qpBody = await page.locator("body").innerText();
    if (qpBody.includes("Curriculum grounding") || qpBody.includes("Grounded")) {
      await shot(page, "11-question-paper-grounded");
      pass(11, "Question paper shows grounding badge");
    } else {
      await shot(page, "11-question-paper-FAIL");
      fail(11, "QP missing grounding — may need AI credits or LLM");
    }
  } catch (e) {
    fail("?", e.message);
    await shot(page, "99-error");
  }

  fs.writeFileSync(path.join(OUT, "workflow-results.json"), JSON.stringify({ results, errors }, null, 2));
  console.log("\nResults:", JSON.stringify(results, null, 2));
  await browser.close();
  const failed = results.filter((r) => !r.ok);
  process.exit(failed.length ? 1 : 0);
})();
