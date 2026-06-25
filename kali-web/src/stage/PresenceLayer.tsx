// PresenceLayer — ephemeral overlay showing tool activity and reasoning.
//
// This layer sits above the MomentStream and shows transient status: the
// currently-running tool (a small pill near the avatar) and the latest
// reasoning snippet (ThoughtCloud, draggable around the avatar). Also shows a "Thinking…" indicator
// during the gap between send and first token.

import { AnimatePresence, motion } from "framer-motion";
import { Cog, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { useStage } from "./StageProvider";
import { ThoughtCloud } from "../components/ThoughtCloud";

export function PresenceLayer() {
  const { t } = useTranslation();
  const { chat } = useStage();

  const runningTools = chat.toolEvents.filter((e) => e.status === "running");
  const lastTool = runningTools[runningTools.length - 1];

  // Latest message with reasoning (streaming OR finished).
  // This keeps the cloud visible after streaming ends, dimmed instead of hidden.
  const lastMsgWithReasoning = [...chat.messages].reverse().find((m) => m.reasoning);
  const reasoning = lastMsgWithReasoning?.reasoning ?? null;
  const isCurrentlyStreaming = lastMsgWithReasoning?.streaming === true;

  // Dismissal: user can close the cloud; resets when a new stream starts.
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    if (isCurrentlyStreaming) setDismissed(false);
  }, [isCurrentlyStreaming]);

  // Thinking indicator: active between turn_start and first token/tool.
  const showThinking = chat.isThinking && !lastTool && !reasoning;
  const showCloud = reasoning && !dismissed;

  return (
    <div className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center">
      {/* Thinking pill — visible during initial gap */}
      <AnimatePresence>
        {showThinking && (
          <motion.div
            key="thinking-pill"
            className="hud-pill"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            style={{ marginTop: "calc(50vh + (140px * var(--mul-avatar)))" }}
          >
            <Sparkles size={11} className="animate-pulse text-accent" />
            {t("stage.thinking")}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tool pill — floats above the avatar */}
      <AnimatePresence>
        {lastTool && (
          <motion.div
            key="tool-pill"
            className="hud-pill"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            style={{ marginTop: "calc(50vh + (140px * var(--mul-avatar)))" }}
          >
            <Cog size={11} className="animate-spin text-accent" />
            {lastTool.params?.command
              ? t("tool.running_command", { command: (lastTool.params.command as string).split(" ")[0] })
              : t("tool.running", { tool: lastTool.tool })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reasoning — ThoughtCloud orbitando el avatar (draggable, anclada al avatar center).
          Permanece visible (dimmed) tras el streaming hasta que el usuario la cierre. */}
      <AnimatePresence>
        {showCloud && (
          <ThoughtCloud
            key="thought-cloud"
            reasoning={reasoning ?? ""}
            isStreaming={isCurrentlyStreaming}
            dimmed={!isCurrentlyStreaming}
            onDismiss={() => setDismissed(true)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
