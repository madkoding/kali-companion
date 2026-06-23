// Stage — the root reactive surface.
//
// A mostly-empty surface where Kali (the calico cat) rests at the centre.
// Content materialises as the conversation flows. Layout:
//
//   ┌──────────────────────────────────────────────┐
//   │  HUD (corners)                                │
//   │                                               │
//   │            [avatar / presence]                │
//   │                                               │
//   │            MomentStream (flow)                │
//   │                                               │
//   │                  [Dock]                       │
//   └──────────────────────────────────────────────┘
//
// The avatar sits behind the stream when there is content; when the stage is
// empty it is the sole focal point.

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { useStage } from "./StageProvider";
import { useAvatarMood } from "./useAvatarMood";
import { KaliAvatar } from "./KaliAvatar";
import { HUD } from "./HUD";
import { MomentStream } from "./MomentStream";
import { PresenceLayer } from "./PresenceLayer";
import { Dock } from "./Dock";
import { SessionDrawer } from "./SessionDrawer";
import { SettingsModal } from "../components/SettingsModal";
import { ConsentModal } from "../components/ConsentModal";
import { JobsPanel } from "../components/JobsPanel";
import { useBreakpoint } from "../hooks/useBreakpoint";

interface Props {
  theme: string;
  onThemeChange: (t: string) => void;
  canvasAutoExpand: boolean;
  onCanvasAutoExpandChange: (v: boolean) => void;
}

export function Stage({ theme, onThemeChange, canvasAutoExpand, onCanvasAutoExpandChange }: Props) {
  const { i18n } = useTranslation();
  const { chat, tts, ptt, voices } = useStage();
  const { isMobile } = useBreakpoint();
  const [typing, setTyping] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [jobsOpen, setJobsOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const mood = useAvatarMood(typing);

  // Drive the avatar mouth from the TTS analyser while speaking.
  const rafRef = useRef<number | null>(null);
  useEffect(() => {
    if (!tts.playing || !tts.analyser) {
      setAudioLevel(0);
      return;
    }
    const an = tts.analyser;
    const data = new Uint8Array(an.frequencyBinCount);
    const tick = () => {
      an.getByteFrequencyData(data);
      let sum = 0;
      for (let i = 0; i < 16; i++) sum += data[i];
      setAudioLevel(Math.min(1, sum / (16 * 255)));
      rafRef.current = requestAnimationFrame(tick);
    };
    tick();
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [tts.playing, tts.analyser]);

  // Auto-adaptive input: any printable keypress on the stage reveals the
  // text field. Ignore when a modal/input is already focused.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (typing) return;
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT" || target.isContentEditable)) return;
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        setTyping(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [typing]);

  const newSession = useCallback(() => {
    setHistoryOpen(false);
    chat.newSession();
    window.location.hash = "#/";
  }, [chat]);

  const onLanguageChange = useCallback((lang: string) => {
    void i18n.changeLanguage(lang);
    localStorage.setItem("kali.lang", lang);
  }, [i18n]);

  const empty = chat.messages.length === 0;

  return (
    <div className="relative h-full w-full overflow-hidden stage-surface stage-grain">
      {/* Avatar — centered; recedes behind content when there are messages */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center z-0">
        <AnimatePresence>
          {empty && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85, y: -20 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col items-center gap-4"
            >
              <KaliAvatar mood={mood} audioLevel={audioLevel} size={isMobile ? 140 : 200} />
            </motion.div>
          )}
        </AnimatePresence>
        {/* Compact avatar when there is content — top-centre, subtle */}
        <AnimatePresence>
          {!empty && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 0.55, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="absolute top-20"
            >
              <KaliAvatar mood={mood} audioLevel={audioLevel} size={84} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <HUD
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenJobs={() => { chat.listJobs(); setJobsOpen(true); }}
        onOpenHistory={() => setHistoryOpen(true)}
        onNewSession={newSession}
        onLanguageChange={onLanguageChange}
        currentLanguage={i18n.language}
      />

      <PresenceLayer />

      <main className="relative z-10 h-full flex flex-col">
        <MomentStream
          messages={chat.messages}
          imageReadyKeys={chat.imageReadyKeys}
          onRequestImage={chat.requestImage}
        />
      </main>

      <Dock typing={typing} onTypingChange={setTyping} />

      {/* Error toasts */}
      <AnimatePresence>
        {chat.error && (
          <motion.div
            className="fixed top-16 left-1/2 -translate-x-1/2 bg-err text-white px-4 py-2 rounded-md text-sm z-50 max-w-[90vw]"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {chat.error}
          </motion.div>
        )}
        {ptt.error && (
          <motion.div
            className="fixed top-16 left-1/2 -translate-x-1/2 bg-err text-white px-4 py-2 rounded-md text-sm z-50 max-w-[90vw]"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {ptt.error}
          </motion.div>
        )}
      </AnimatePresence>

      <SessionDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        sessions={chat.sessions}
        activeSessionId={chat.sessionId}
        onNewSession={newSession}
      />

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        systemStatus={chat.systemStatus}
        voices={voices}
        onUpdate={chat.updateSettings}
        theme={theme}
        onThemeChange={onThemeChange}
        canvasAutoExpand={canvasAutoExpand}
        onCanvasAutoExpandChange={onCanvasAutoExpandChange}
      />

      <ConsentModal request={chat.consentRequest} onRespond={chat.respondConsent} />

      <JobsPanel
        open={jobsOpen}
        onClose={() => setJobsOpen(false)}
        jobs={chat.jobs}
        onCancelJob={chat.cancelJob}
        onGetLogs={chat.getJobLogs}
      />
    </div>
  );
}