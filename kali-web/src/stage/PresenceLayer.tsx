// PresenceLayer — ephemeral overlay showing tool activity and reasoning.
//
// This layer sits above the MomentStream and shows transient status: the
// currently-running tool (a small pill near the avatar) and the latest
// reasoning snippet (fades in/out). These complement the in-flow rendering
// in Moment but give the Stage its "alive" feel.

import { AnimatePresence, motion } from "framer-motion";
import { Cog } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useStage } from "./StageProvider";

export function PresenceLayer() {
  const { t } = useTranslation();
  const { chat } = useStage();

  const runningTools = chat.toolEvents.filter((e) => e.status === "running");
  const lastTool = runningTools[runningTools.length - 1];

  // Latest reasoning from the streaming message.
  const streamingMsg = chat.messages.find((m) => m.streaming && m.reasoning);
  const reasoning = streamingMsg?.reasoning ?? null;

  return (
    <div className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center">
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
            style={{ marginTop: "calc(50vh + 140px)" }}
          >
            <Cog size={11} className="animate-spin text-accent" />
            {t("tool.running", { tool: lastTool.tool })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reasoning — fades near the avatar */}
      <AnimatePresence>
        {reasoning && (
          <motion.p
            key="reasoning"
            className="ephemeral-text text-center max-w-[480px] px-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.55 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            style={{ marginTop: "calc(50vh - 200px)" }}
          >
            {reasoning.slice(-240)}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}