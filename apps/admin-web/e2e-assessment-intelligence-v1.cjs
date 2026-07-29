/* eslint-disable @typescript-eslint/no-require-imports */
/**
 * Assessment Intelligence v1.0 Batch G browser proof.
 *
 * This harness proves the supported teacher assessment workflow without
 * changing product behavior. It requires Reference tenant fixture data; if the
 * expected supported-scope paper/exam data is missing, the run fails honestly
 * as a proof-prerequisite blocker.
 *
 * Reproducible prerequisite:
 *   cd ../api
 *   python scripts/seed_reference_school.py
 *   python scripts/seed_assessment_browser_proof_fixture.py
 *
 * Needs both servers up:
 *   API:  E2E_API_URL=http://127.0.0.1:8000
 *   Web:  E2E_BASE_URL=http://127.0.0.1:3000
 *
 * Recommended production-style local run:
 *   npm run build
 *   npx next start -p 3002
 *   set E2E_BASE_URL=http://127.0.0.1:3002
 *   npm run e2e-assessment-v1
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const {
  REFERENCE_TENANT,
  requireReferenceTenant,
  attachConsoleGuard,
  attachApiFailureTracker,
  attachTenantTracker,
  reportConsoleErrors,
} = require("./e2e-harness-utils.cjs");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8000";
const TENANT =
  process.env.E2E_TENANT_SLUG || process.env.NEXT_PUBLIC_TENANT_SLUG || REFERENCE_TENANT;
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-assessment-v1");
const PRIMARY_SCOPE = {
  board: "SSC",
  curriculum: "Telangana reference material",
  grade: "6",
  subject: "Science",
  paperType: "Unit Test",
  language: "English",
};
const FIXTURE_REPAIR_HINT =
  "missing - run: cd apps/api && python scripts/seed_assessment_browser_proof_fixture.py";

requireReferenceTenant(TENANT);

const results = [];

function record(ok, label, note = "") {
  results.push([Boolean(ok), label, note]);
  return Boolean(ok);
}

function asItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

function text(value) {
  return String(value ?? "").toLowerCase();
}

function matchesGrade(row, grade) {
  return text(row.grade).includes(String(grade).toLowerCase());
}

function matchesSubject(row, subject) {
  return text(row.name || row.subject_name || row.title).includes(subject.toLowerCase());
}

async function shot(page, name) {
  try {
    await page.screenshot({
      path: path.join(SHOTS, `${name}.png`),
      fullPage: true,
      timeout: 10000,
    });
  } catch (e) {
    record(true, `screenshot skipped: ${name}`, e.message);
  }
}

async function waitForPageReady(page) {
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page
    .waitForFunction(
      () => {
        const visibleSpinner = Array.from(document.querySelectorAll(".spinner")).some((spinner) => {
          const style = window.getComputedStyle(spinner);
          const box = spinner.getBoundingClientRect();
          return (
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            box.width > 0 &&
            box.height > 0
          );
        });
        const body = document.body?.innerText || "";
        return !visibleSpinner && body.length > 180;
      },
      { timeout: 20000 }
    )
    .catch(() => {});
  await page.waitForTimeout(300);
}

async function loginViaApi(page, username, password) {
  const loginResp = await page.request.post(`${API}/api/v1/auth/login`, {
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Slug": TENANT,
    },
    data: { username, password },
  });
  if (!loginResp.ok()) {
    const body = await loginResp.text();
    throw new Error(`API login failed (${loginResp.status()}): ${body.slice(0, 240)}`);
  }
  const { access_token: accessToken } = await loginResp.json();
  return accessToken;
}

async function installSession(page, accessToken) {
  await page.context().addInitScript(
    ({ token, tenant }) => {
      sessionStorage.setItem("sn_access_token", token);
      sessionStorage.setItem("sn_prospect_tenant_slug", tenant);
    },
    { token: accessToken, tenant: TENANT }
  );
}

async function apiGet(page, accessToken, endpoint) {
  const resp = await page.request.get(`${API}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "X-Tenant-Slug": TENANT,
    },
  });
  if (!resp.ok()) {
    const body = await resp.text();
    throw new Error(`GET ${endpoint} failed (${resp.status()}): ${body.slice(0, 240)}`);
  }
  return resp.json();
}

async function assertNotLoginScreen(page, label) {
  const body = await page.locator("body").innerText();
  if (body.includes("Welcome back") && body.includes("Username & password")) {
    throw new Error(`${label} redirected to login`);
  }
  return body;
}

async function authenticateStaff(page) {
  const accessToken = await loginViaApi(page, "principal", "Demo@1234");
  await installSession(page, accessToken);
  await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded" });
  await waitForPageReady(page);
  await assertNotLoginScreen(page, "dashboard");
  return accessToken;
}

async function resolveSupportedScope(page, accessToken) {
  const classes = asItems(await apiGet(page, accessToken, "/api/v1/academic/classes?page_size=100"));
  const klass = classes.find((row) => matchesGrade(row, PRIMARY_SCOPE.grade));
  record(Boolean(klass), "reference data: Grade 6 class", klass?.id || "missing");
  if (!klass) return null;

  const subjects = asItems(
    await apiGet(page, accessToken, `/api/v1/academic/subjects?class_id=${klass.id}`)
  );
  const subject = subjects.find((row) => matchesSubject(row, PRIMARY_SCOPE.subject));
  record(Boolean(subject), "reference data: Science subject", subject?.id || "missing");
  if (!subject) return { klass, subject: null, papers: [], exams: [] };

  const paperPayload = await apiGet(page, accessToken, "/api/v1/ai/question-papers");
  const papers = asItems(paperPayload);
  const supportedPaper = papers.find((paper) => {
    const status = text(paper.status);
    const gradeOk = text(paper.grade).includes(PRIMARY_SCOPE.grade);
    const subjectOk = text(paper.subject_name).includes(PRIMARY_SCOPE.subject.toLowerCase());
    return gradeOk && subjectOk && ["approved", "submitted", "draft"].some((s) => status.includes(s));
  });
  record(
    Boolean(supportedPaper),
    "reference data: supported-scope question paper",
    supportedPaper ? `${supportedPaper.title || supportedPaper.id} (${supportedPaper.status})` : FIXTURE_REPAIR_HINT
  );

  const exams = asItems(await apiGet(page, accessToken, `/api/v1/exams?class_id=${klass.id}`));
  const linkedExam = exams.find((exam) => {
    const subjectOk = !exam.subject_id || exam.subject_id === subject.id;
    return subjectOk && (exam.can_evaluate_sheets || exam.has_question_schema);
  });
  record(
    Boolean(linkedExam),
    "reference data: linked/evaluable exam",
    linkedExam ? `${linkedExam.title || linkedExam.id}` : FIXTURE_REPAIR_HINT
  );

  return { klass, subject, papers, supportedPaper, exams, linkedExam };
}

function assertNoUnsupportedClaims(body, label) {
  const lower = body.toLowerCase();
  const badClaims = [
    "universal multilingual assessment supported",
    "automatic question-paper translation supported",
    "automatic rubric translation supported",
    "autonomous language grading",
    "autonomous paper approval",
  ].filter((claim) => lower.includes(claim));
  record(badClaims.length === 0, `${label}: no unsupported language/product claims`, badClaims.join(", "));
}

async function verifyAiPapers(page) {
  await page.goto(`${BASE}/dashboard/teaching/ai-papers`, { waitUntil: "domcontentloaded" });
  await waitForPageReady(page);
  const body = await assertNotLoginScreen(page, "AI Papers");
  record(
    body.includes("Question Paper") || body.includes("Generate"),
    "AI Papers route renders",
    "expected question paper/generate anchor"
  );
  record(
    body.includes("approval") || body.includes("Approve") || body.includes("Draft"),
    "AI Papers teacher authority posture visible/verifiable",
    "approval/draft posture anchor"
  );
  record(
    body.includes("Configuration") && body.includes("Template") && body.includes("Blueprint"),
    "Question Paper Studio constraint-first workflow visible",
    "configuration/template/blueprint anchors"
  );
  record(
    body.includes("Assessment type") && body.includes("Approved curriculum pack"),
    "Question Paper Studio governed assessment type and curriculum posture visible",
    "assessment-type/approved-pack anchors"
  );
  assertNoUnsupportedClaims(body, "AI Papers");
  await shot(page, "assessment-01-ai-papers");
}

async function selectSupportedClass(page, context) {
  if (!context?.klass?.id) return;
  const linkedTitle = context.linkedExam?.title || "";
  const body = await page.locator("body").innerText().catch(() => "");
  if (linkedTitle && body.includes(linkedTitle)) return;

  await page.getByRole("button", { name: /select class and section/i }).click();
  await page
    .locator('[role="option"]')
    .filter({ hasText: new RegExp(PRIMARY_SCOPE.grade) })
    .first()
    .click();
  await waitForPageReady(page);
  if (linkedTitle) {
    await page
      .waitForFunction((title) => document.body.innerText.includes(title), linkedTitle, {
        timeout: 10000,
      })
      .catch(() => {});
  }
}

async function verifyExams(page, context) {
  await page.goto(`${BASE}/dashboard/teaching/exams`, { waitUntil: "domcontentloaded" });
  await waitForPageReady(page);
  await selectSupportedClass(page, context);
  const body = await assertNotLoginScreen(page, "Exams");
  record(body.includes("Exams") || body.includes("Marks"), "Exams route renders");
  record(body.includes("Questions") || body.includes("Enter marks"), "Exam schema/marks actions visible");
  assertNoUnsupportedClaims(body, "Exams");
  await shot(page, "assessment-02-exams");
}

async function verifyEvaluation(page, linkedExam) {
  if (!linkedExam?.id) {
    record(false, "Evaluation route proof", "missing linked/evaluable exam prerequisite");
    return;
  }
  await page.goto(`${BASE}/dashboard/teaching/exams/${linkedExam.id}/evaluate`, {
    waitUntil: "domcontentloaded",
  });
  await waitForPageReady(page);
  const body = await assertNotLoginScreen(page, "Evaluation");
  record(
    body.includes("Evaluate") || body.includes("Evaluation") || body.includes("answer"),
    "Evaluation route renders",
    linkedExam.title || linkedExam.id
  );
  record(
    body.includes("Approve") ||
      body.includes("approved") ||
      body.includes("Teacher") ||
      body.includes("Manual review") ||
      body.includes("Review AI-suggested marks before publishing"),
    "Evaluation teacher authority visible/verifiable",
    "approval/manual review anchor"
  );
  record(
    body.includes("AI") || body.includes("AEI") || body.includes("trust") || body.includes("confidence"),
    "AEI/evaluation assist path visible/verifiable",
    "AI/AEI/trust/confidence anchor"
  );
  assertNoUnsupportedClaims(body, "Evaluation");
  await shot(page, "assessment-03-evaluation");
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleBuckets = { all: [], disallowed: [], apiFailures: [] };
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);
  attachApiFailureTracker(page, consoleBuckets);

  let accessToken = "";
  let context = null;

  try {
    accessToken = await authenticateStaff(page);
    record(true, "login -> dashboard", "principal via API token");
    await shot(page, "assessment-00-dashboard");
  } catch (e) {
    record(false, "login", e.message);
    await finish(browser, consoleBuckets, tenantTracker);
    return;
  }

  try {
    context = await resolveSupportedScope(page, accessToken);
  } catch (e) {
    record(false, "reference data discovery", e.message);
  }

  try {
    await verifyAiPapers(page);
  } catch (e) {
    record(false, "AI Papers route proof", e.message);
    await shot(page, "assessment-01-ai-papers-FAIL");
  }

  try {
    await verifyExams(page, context);
  } catch (e) {
    record(false, "Exams route proof", e.message);
    await shot(page, "assessment-02-exams-FAIL");
  }

  try {
    await verifyEvaluation(page, context?.linkedExam);
  } catch (e) {
    record(false, "Evaluation route proof", e.message);
    await shot(page, "assessment-03-evaluation-FAIL");
  }

  results.push(tenantTracker.assert("tenant reference"));
  await finish(browser, consoleBuckets, tenantTracker);
})();

async function finish(browser, consoleBuckets) {
  await browser.close();
  console.log("\n" + "=".repeat(78));
  console.log(`Assessment Intelligence v1.0 browser proof`);
  console.log(`tenant=${TENANT} base=${BASE} api=${API}`);
  console.log(`primary_scope=${JSON.stringify(PRIMARY_SCOPE)}`);
  let fails = 0;
  for (const [ok, label, note] of results) {
    if (!ok) fails += 1;
    console.log(`${ok ? "OK  " : "FAIL"}  ${String(label).padEnd(58)} ${note || ""}`);
  }
  console.log("=".repeat(78));
  const disallowedCount = reportConsoleErrors(consoleBuckets);
  if (disallowedCount > 0) fails += 1;
  console.log(
    `${fails === 0 ? "ALL GREEN" : `${fails} FAILED`} (${results.length} checks` +
      `${disallowedCount ? ` + ${disallowedCount} console/API error(s)` : ", 0 disallowed console/API errors"})` +
      ` shots: ${SHOTS}`
  );
  process.exit(fails ? 1 : 0);
}
