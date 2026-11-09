#!/usr/bin/env node
/**
 * Fails when a built admin-web bundle contains shared demo credentials.
 * Run after `next build` (and `opennextjs-cloudflare build` if used):  npm run check:bundle
 * Extra literals to forbid can be supplied via BUNDLE_FORBIDDEN_LITERALS (comma-separated).
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const TARGETS = [".next", ".open-next"].map((d) => path.join(ROOT, d)).filter((d) => fs.existsSync(d));
const SCANNED_EXT = new Set([".js", ".mjs", ".cjs", ".json", ".html", ".txt", ".map", ".rsc"]);

// Built from parts so this script itself never contains the literal it hunts for.
const FORBIDDEN = [["Demo", "@", "1234"].join("")].concat(
  (process.env.BUNDLE_FORBIDDEN_LITERALS || "").split(",").map((s) => s.trim()).filter(Boolean)
);
const PATTERNS = [
  /\bpassword\s*:\s*"[^"]{4,}"/, // an inlined password string literal in an object
];
const SKIP_DIRS = new Set(["cache", "node_modules"]);

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) yield* walk(full);
    } else if (SCANNED_EXT.has(path.extname(entry.name))) {
      yield full;
    }
  }
}

if (!TARGETS.length) {
  console.error("check-bundle-secrets: no build output found (.next/.open-next). Run `next build` first.");
  process.exit(2);
}

const hits = [];
let files = 0;
for (const target of TARGETS) {
  for (const file of walk(target)) {
    files += 1;
    const text = fs.readFileSync(file, "utf8");
    for (const lit of FORBIDDEN) {
      if (text.includes(lit)) hits.push(`${path.relative(ROOT, file)}: forbidden literal`);
    }
    for (const re of PATTERNS) {
      const m = text.match(re);
      if (m) hits.push(`${path.relative(ROOT, file)}: ${m[0].slice(0, 40)}…`);
    }
  }
}

if (hits.length) {
  console.error(`check-bundle-secrets: FAIL (${hits.length} finding(s) in ${files} files)`);
  for (const h of [...new Set(hits)].slice(0, 40)) console.error(`  - ${h}`);
  process.exit(1);
}
console.log(`check-bundle-secrets: OK (${files} files scanned, 0 findings)`);
