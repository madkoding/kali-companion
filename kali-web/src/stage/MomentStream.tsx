// MomentStream — vertical flow of conversational moments.
//
//   - the last turn (assistant in progress or the most recent message) is
//     rendered at full size in the centre.
//   - the previous 2-3 turns are rendered recaded (dimmed + shrunk) above it.
//   - older history is accessible via the SessionDrawer (not shown here).
//
// Auto-scrolls to keep the active moment in view while streaming.

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import type { ChatMessage } from "../hooks/useChat";
import { Moment } from "./Moment";

interface Props {
  messages: ChatMessage[];
  imageReadyKeys?: Set<string>;
  onRequestImage?: (key: string) => void;
  // Called when the stream is empty — the Stage shows the avatar instead.
  onEmpty?: () => void;
}

const RECADE_COUNT = 3;

export function MomentStream({ messages, imageReadyKeys, onRequestImage }: Props) {
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expandedArtifactId, setExpandedArtifactId] = useState<string | null>(null);

  // The "visible" slice: last (1 + RECADE_COUNT) messages. The last one is
  // the active moment; the rest are recaded.
  const visible = messages.slice(-(1 + RECADE_COUNT));
  const activeIdx = visible.length - 1;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted">
        <p className="text-sm opacity-70">{t("stage.greeting")}</p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto stage-scroll px-5 md:px-8 pb-4 pt-2">
      <div className="mx-auto flex max-w-[820px] flex-col gap-5 md:gap-7 items-center">
        <AnimatePresence initial={false}>
          {visible.map((m, i) => {
            const isActive = i === activeIdx;
            const recaded = !isActive;
            return (
              <motion.div
                key={m.id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: recaded ? 0.42 : 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
                className={recaded ? "moment-recaded w-full flex justify-center" : "w-full flex justify-center"}
              >
                <Moment
                  message={m}
                  recaded={recaded}
                  expandedArtifactId={expandedArtifactId}
                  onExpandArtifact={setExpandedArtifactId}
                  imageReadyKeys={imageReadyKeys}
                  onRequestImage={onRequestImage}
                />
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}