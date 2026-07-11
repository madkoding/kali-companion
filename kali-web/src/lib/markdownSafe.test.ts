/**
 * Contract tests for the markdownSafe helper (F0-5).
 *
 * Pins the XSS guarantee: any HTML produced by `renderMarkdown` is safe
 * to inject via dangerouslySetInnerHTML. If a future refactor drops
 * DOMPurify, these tests fail loudly.
 */

import { describe, it, expect } from "vitest";
import { renderMarkdown } from "./markdownSafe";

describe("renderMarkdown — XSS sanitization", () => {
  it("renders plain text as a paragraph", () => {
    const html = renderMarkdown("hello world");
    expect(html).toContain("hello world");
  });

  it("renders basic markdown (bold, italic, code)", () => {
    const html = renderMarkdown("**bold** and *italic* and `code`");
    expect(html).toContain("<strong>bold</strong>");
    expect(html).toContain("<em>italic</em>");
    expect(html).toContain("<code>code</code>");
  });

  it("strips <script> tags from the input", () => {
    const html = renderMarkdown("hello <script>alert('xss')</script> world");
    expect(html).not.toContain("<script>");
    expect(html).not.toContain("alert(");
  });

  it("strips inline event handlers (onerror, onload, onclick)", () => {
    const html = renderMarkdown('<img src="x" onerror="alert(1)">');
    expect(html).not.toContain("onerror");
    expect(html).not.toContain("alert(1)");
  });

  it("strips javascript: URLs from links", () => {
    const html = renderMarkdown("[click](javascript:alert(1))");
    expect(html).not.toContain("javascript:");
  });

  it("strips iframes", () => {
    const html = renderMarkdown("<iframe src='https://evil.com'></iframe>");
    expect(html).not.toContain("<iframe");
  });

  it("strips data: URLs from images", () => {
    const html = renderMarkdown(
      '<img src="data:text/html,<script>alert(1)</script>">',
    );
    expect(html).not.toContain("data:text/html");
    expect(html).not.toContain("alert(");
  });

  it("preserves safe HTML (b, i, code, pre, a with https)", () => {
    const html = renderMarkdown(
      "**bold** and [external](https://example.com)",
    );
    expect(html).toContain("<strong>bold</strong>");
    expect(html).toContain('href="https://example.com"');
  });

  it("handles empty input", () => {
    expect(renderMarkdown("")).toBe("");
  });

  it("strips style attributes that could exfiltrate data", () => {
    const html = renderMarkdown(
      '<div style="background:url(javascript:alert(1))">x</div>',
    );
    expect(html).not.toContain("javascript:");
  });

  it("strips object and embed tags", () => {
    const html = renderMarkdown(
      '<object data="evil.swf"></object><embed src="evil.swf">',
    );
    expect(html).not.toContain("<object");
    expect(html).not.toContain("<embed");
  });
});
