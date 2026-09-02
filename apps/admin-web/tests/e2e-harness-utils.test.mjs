import assert from "node:assert/strict";
import test from "node:test";
import { isAllowedConsoleError } from "../e2e-harness-utils.cjs";

test("allows refresh 401 messages", () => {
  const message =
    "Failed to load resource: the server responded with a status of 401 (Unauthorized) [url=http://127.0.0.1:3002/api/v1/auth/refresh]";
  assert.equal(isAllowedConsoleError(message), true);
});

test("allows benign pre-auth 401 on portal login pages", () => {
  const message =
    "Failed to load resource: the server responded with a status of 401 (Unauthorized) [url=http://127.0.0.1:3002/login?portal=student]";
  assert.equal(isAllowedConsoleError(message), true);
});

test("blocks non-refresh API 401 messages", () => {
  const message =
    "Failed to load resource: the server responded with a status of 401 (Unauthorized) [url=http://127.0.0.1:3002/api/v1/users/me]";
  assert.equal(isAllowedConsoleError(message), false);
});

test("blocks CORS errors", () => {
  const message = "Access to fetch has been blocked by CORS policy";
  assert.equal(isAllowedConsoleError(message), false);
});
