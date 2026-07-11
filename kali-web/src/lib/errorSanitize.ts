export type ErrorCategory =
  | "auth"
  | "billing"
  | "rate_limit"
  | "not_found"
  | "bad_request"
  | "content_filter"
  | "server"
  | "network"
  | "tool"
  | "config"
  | "internal";

// Each entry: [pattern, replacement]. Order matters — more specific
// patterns first so they fire before the generic sk- mask.
const SECRET_PATTERNS: Array<[RegExp, string]> = [
  [/sk-or-v1-[A-Za-z0-9_-]+/g, "sk-or-v1-…"],
  [/Bearer\s+[A-Za-z0-9._\-]+/g, "Bearer …"],
  // Generic sk- prefix (OpenAI, Anthropic, etc.) — must be LAST among
  // sk- variants so it doesn't shadow the more specific ones above.
  // Matches sk-your-****here too because the * chars are non-alphanumeric
  // but allowed by the character class, and the {8,} length is satisfied.
  [/sk-[A-Za-z0-9*_\-]{8,}/g, "sk-…"],
];

const ANSI_ESCAPE = /\x1b\[[0-9;]*[a-zA-Z]/g;

const MAX_DETAIL_LENGTH = 500;

export function sanitizeErrorString(s: string | null | undefined): string {
  if (!s) return "";
  let out = s;
  out = ANSI_ESCAPE.test(out) ? out.replace(ANSI_ESCAPE, "") : out;
  for (const [pattern, repl] of SECRET_PATTERNS) {
    out = out.replace(pattern, repl);
  }
  if (out.length > MAX_DETAIL_LENGTH) {
    out = out.slice(0, MAX_DETAIL_LENGTH) + "…";
  }
  return out;
}

export function isRetryableCategory(c: ErrorCategory): boolean {
  return c === "rate_limit" || c === "server" || c === "network";
}

export function showOpenSettingsForCategory(c: ErrorCategory): boolean {
  return c === "auth" || c === "billing" || c === "config";
}
