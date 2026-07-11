/**
 * Contract tests for the errorSanitize helper (Fase 0).
 */

import { describe, it, expect } from "vitest";
import {
  isRetryableCategory,
  sanitizeErrorString,
  showOpenSettingsForCategory,
} from "./errorSanitize";

describe("sanitizeErrorString — XSS and secret redaction", () => {
  it("masks sk- prefix", () => {
    const out = sanitizeErrorString("Invalid key sk-proj-abc123def456ghi789");
    expect(out).not.toContain("sk-proj-abc");
    expect(out).toContain("sk-…");
  });

  it("masks OpenRouter sk-or-v1 prefix", () => {
    const out = sanitizeErrorString("auth: sk-or-v1-abc123def456");
    expect(out).toContain("sk-or-v1-…");
  });

  it("masks Bearer token", () => {
    const out = sanitizeErrorString("Authorization: Bearer abc123def456ghi789");
    expect(out).toContain("Bearer …");
  });

  it("does not mask short sk- strings", () => {
    expect(sanitizeErrorString("sk-test")).toBe("sk-test");
  });

  it("strips ANSI escape codes", () => {
    const out = sanitizeErrorString("\x1b[31mError\x1b[0m");
    expect(out).toBe("Error");
  });

  it("truncates strings longer than 500 chars", () => {
    const long = "x".repeat(600);
    const out = sanitizeErrorString(long);
    expect(out.length).toBe(501);
    expect(out.endsWith("…")).toBe(true);
  });

  it("handles empty/null/undefined", () => {
    expect(sanitizeErrorString("")).toBe("");
    expect(sanitizeErrorString(null)).toBe("");
    expect(sanitizeErrorString(undefined)).toBe("");
  });

  it("realistic OpenAI error from the user's complaint", () => {
    const raw =
      "Error code: 401 - {'error': {'message': 'Incorrect API key provided: " +
      "sk-your-****here. You can find your API key at " +
      "https://platform.openai.com/account/api-keys.', " +
      "'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, " +
      "'status': 401}";
    const out = sanitizeErrorString(raw);
    expect(out).not.toContain("sk-your-****here");
    expect(out).toContain("https://platform.openai.com");
  });
});

describe("isRetryableCategory", () => {
  it("returns true for retryable categories", () => {
    expect(isRetryableCategory("rate_limit")).toBe(true);
    expect(isRetryableCategory("server")).toBe(true);
    expect(isRetryableCategory("network")).toBe(true);
  });

  it("returns false for non-retryable categories", () => {
    expect(isRetryableCategory("auth")).toBe(false);
    expect(isRetryableCategory("billing")).toBe(false);
    expect(isRetryableCategory("internal")).toBe(false);
  });
});

describe("showOpenSettingsForCategory", () => {
  it("returns true for categories where settings is useful", () => {
    expect(showOpenSettingsForCategory("auth")).toBe(true);
    expect(showOpenSettingsForCategory("billing")).toBe(true);
    expect(showOpenSettingsForCategory("config")).toBe(true);
  });

  it("returns false for other categories", () => {
    expect(showOpenSettingsForCategory("network")).toBe(false);
    expect(showOpenSettingsForCategory("rate_limit")).toBe(false);
    expect(showOpenSettingsForCategory("internal")).toBe(false);
  });
});
