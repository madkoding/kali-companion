import DOMPurify from "dompurify";
import { marked } from "marked";

export function renderMarkdown(text: string): string {
  const raw = marked.parse(text, { async: false }) as string;
  return DOMPurify.sanitize(raw, {
    USE_PROFILES: { html: true },
    FORBID_ATTR: ["style", "srcset"],
    FORBID_TAGS: ["style", "iframe", "object", "embed", "form", "input", "button"],
  });
}
