// Moment — a single conversational turn rendered as flowing prose (no bubble).
//
//   - user message    -> faint italic "echo" (left border accent)
//   - assistant text  -> serif prose, markdown rendered, streaming cursor
//   - tool events     -> compact ephemeral line (icon + label)
//   - reasoning       -> collapsible italic panel (kept, but subtle)
//   - inline artifacts -> rendered via ArtifactSlot (expandable)
//
// When `recaded` is true, the whole moment is dimmed and shrunk (history mode).

import { useMemo } from "react";
import { marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";
import { useTranslation } from "react-i18next";
import "highlight.js/styles/github-dark.css";
import { Loader2, CheckCircle2, XCircle, Cog } from "lucide-react";
import type { ToolEvent } from "../lib/protocol";
import type { ChatMessage } from "../hooks/useChat";
import { ArtifactSlot } from "./ArtifactSlot";

marked.use(markedHighlight({
  langPrefix: "hljs language-",
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : "plaintext";
    return hljs.highlight(code, { language }).value;
  },
}));
marked.setOptions({ breaks: true, gfm: true });

interface Props {
  message: ChatMessage;
  recaded?: boolean;
  expandedArtifactId: string | null;
  onExpandArtifact: (id: string | null) => void;
  imageReadyKeys?: Set<string>;
  onRequestImage?: (key: string) => void;
}

function ToolLine({ ev }: { ev: ToolEvent }) {
  const { t } = useTranslation();
  const icon =
    ev.status === "running" ? <Cog size={13} className="animate-spin text-accent" /> :
    ev.status === "success" ? <CheckCircle2 size={13} className="text-ok" /> :
    <XCircle size={13} className="text-err" />;
  const key = ev.status === "running" ? "tool.running" : ev.status === "success" ? "tool.success" : "tool.error";
  return (
    <div className="flex items-center gap-2 py-1 text-xs text-muted">
      {icon}
      <span className="ephemeral-text">{t(key, { tool: ev.tool })}</span>
    </div>
  );
}

export function Moment({
  message,
  recaded = false,
  expandedArtifactId,
  onExpandArtifact,
  imageReadyKeys,
  onRequestImage,
}: Props) {
  const { t } = useTranslation();

  const html = useMemo(() => {
    if (message.role === "user" || message.toolEvent) return null;
    return marked.parse(message.content, { async: false }) as string;
  }, [message.content, message.role, message.toolEvent]);

  // Tool event: compact ephemeral line.
  if (message.toolEvent) {
    return (
      <div className={recaded ? "moment-recaded" : ""}>
        <ToolLine ev={message.toolEvent} />
        {message.inlineArtifacts && message.inlineArtifacts.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.inlineArtifacts.map((art) => (
              <ArtifactSlot
                key={art.id}
                artifact={art}
                expanded={expandedArtifactId === art.id}
                onToggle={() => onExpandArtifact(expandedArtifactId === art.id ? null : art.id)}
                imageReadyKeys={imageReadyKeys}
                onRequestImage={onRequestImage}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // User echo.
  if (message.role === "user") {
    return (
      <div className={`max-w-[680px] ${recaded ? "moment-recaded" : ""}`}>
        <p className="moment-echo">
          <span className="text-muted text-[11px] not-italic uppercase tracking-wide mr-1.5 opacity-70">{t("stage.you_said")}</span>
          {message.content}
        </p>
      </div>
    );
  }

  // Assistant prose.
  return (
    <div className={`max-w-[680px] stage-prose ${recaded ? "moment-recaded" : ""}`}>
      {message.reasoning && (
        <details className="reasoning-panel mb-2">
          <summary>{t("reasoning.thinking")}</summary>
          <div className="reasoning-text">{message.reasoning}</div>
        </details>
      )}
      {html ? (
        <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
      ) : message.streaming ? (
        <span className="inline-flex items-center gap-2 text-muted text-sm">
          <Loader2 size={14} className="animate-spin" />
          {t("stage.thinking")}
        </span>
      ) : (
        <span className="msg-empty" />
      )}
      {message.inlineArtifacts && message.inlineArtifacts.length > 0 && (
        <div className="mt-3 space-y-3">
          {message.inlineArtifacts.map((art) => (
            <ArtifactSlot
              key={art.id}
              artifact={art}
              expanded={expandedArtifactId === art.id}
              onToggle={() => onExpandArtifact(expandedArtifactId === art.id ? null : art.id)}
              imageReadyKeys={imageReadyKeys}
              onRequestImage={onRequestImage}
            />
          ))}
        </div>
      )}
      {message.streaming && html && <span className="streaming-cursor" />}
    </div>
  );
}