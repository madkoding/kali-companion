// Dock — bottom-centre input affordance.
//
//   - mic button always visible
//   - text field emerges automatically when the user starts typing
//   - stop button replaces mic while the assistant is streaming
//   - audio visualizer + mute button appear while TTS plays
//
// "Auto-adaptive": a single keypress anywhere on the Stage reveals the text
// field. The Dock tracks a `typing` flag that the Stage sets on keystroke.

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { Mic, Send, Square, X, VolumeX } from "lucide-react";
import { useStage } from "./StageProvider";
import { AudioVisualizer } from "../components/AudioVisualizer";

interface Props {
  typing: boolean;
  onTypingChange: (typing: boolean) => void;
}

export function Dock({ typing, onTypingChange }: Props) {
  const { t } = useTranslation();
  const { chat, tts, ptt } = useStage();
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const textOpen = typing || text.length > 0;

  const isStreaming = chat.messages.some((m) => m.streaming);

  // Focus the input when it opens.
  useEffect(() => {
    if (textOpen) inputRef.current?.focus();
  }, [textOpen]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    chat.send(trimmed);
    setText("");
    onTypingChange(false);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
    if (e.key === "Escape") {
      setText("");
      onTypingChange(false);
    }
  };

  // While recording, show the live transcript + send/cancel.
  if (ptt.state === "recording") {
    return (
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-[min(620px,90vw)] flex gap-2 items-center">
        <div className="dock-input flex-1 italic text-muted min-h-[48px] flex items-center">
          {ptt.partialText || "…"}
        </div>
        <button className="dock-btn danger w-12 h-12" onClick={ptt.cancel} aria-label={t("chat.cancel")}>
          <X size={18} />
        </button>
        <button className="dock-btn accent w-12 h-12" onClick={ptt.stop} aria-label={t("chat.send")}>
          <Send size={18} />
        </button>
      </div>
    );
  }

  if (ptt.state === "processing") {
    return (
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30">
        <button className="dock-btn w-12 h-12 opacity-60 cursor-not-allowed" disabled>
          <Mic size={20} className="animate-pulse" />
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex flex-col items-center gap-2 w-[min(680px,92vw)]">
      {/* TTS controls + visualizer */}
      <AnimatePresence>
        {tts.playing && (
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
          >
            <AudioVisualizer analyser={tts.analyser} active={tts.playing} />
            <button
              className="dock-btn w-9 h-9"
              onClick={tts.stop}
              aria-label="Mute TTS"
              title="Mute TTS"
            >
              <VolumeX size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex gap-2 items-end w-full justify-center">
        {/* Text input — emerges when typing or has text */}
        <AnimatePresence>
          {textOpen && (
            <motion.textarea
              ref={inputRef}
              className="dock-input flex-1 resize-none max-h-[120px] min-h-[48px]"
              placeholder={t("chat.placeholder")}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              disabled={isStreaming}
              initial={{ opacity: 0, width: 0, paddingTop: 0, paddingBottom: 0 }}
              animate={{ opacity: 1, width: "auto", paddingTop: 14, paddingBottom: 14 }}
              exit={{ opacity: 0, width: 0, paddingTop: 0, paddingBottom: 0 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            />
          )}
        </AnimatePresence>

        {/* Send button — only when there is text */}
        <AnimatePresence>
          {text.trim() && !isStreaming && (
            <motion.button
              className="dock-btn accent w-12 h-12"
              onClick={submit}
              aria-label={t("chat.send")}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <Send size={18} />
            </motion.button>
          )}
        </AnimatePresence>

        {/* Mic or Stop */}
        {isStreaming ? (
          <button
            className="dock-btn danger w-12 h-12"
            onClick={() => { chat.stop(); tts.stop(); }}
            aria-label="Stop"
          >
            <Square size={16} />
          </button>
        ) : (
          <button
            className="dock-btn w-12 h-12"
            onClick={() => void ptt.start()}
            aria-label={t("voice.ptt.hint")}
            title={t("voice.ptt.hint")}
          >
            <Mic size={20} />
          </button>
        )}
      </div>
    </div>
  );
}