// useAvatarMood — derives the avatar mood from the combined runtime state.
//
// Priority order (highest first):
//   1. consent pending           -> judge
//   2. tool running               -> judge
//   3. TTS playing                -> speak
//   4. PTT recording / listening  -> listen
//   5. assistant streaming         -> think
//   6. user typing / user msg      -> look
//   7. connected but idle          -> idle (or sleep after a while)

import { useMemo } from "react";
import type { AvatarMood } from "./AvatarStates";
import { useStage } from "./StageProvider";

export function useAvatarMood(typing: boolean): AvatarMood {
  const { chat, tts, ptt } = useStage();

  return useMemo<AvatarMood>(() => {
    if (chat.consentRequest) return "judge";
    if (chat.toolEvents.some((e) => e.status === "running")) return "judge";
    if (tts.playing) return "speak";
    if (ptt.state === "recording" || ptt.state === "listening") return "listen";
    if (chat.messages.some((m) => m.streaming)) return "think";
    if (typing) return "look";
    // No messages yet → sleeping cat.
    if (chat.messages.length === 0) return "sleep";
    return "idle";
  }, [chat.consentRequest, chat.toolEvents, chat.messages, tts.playing, ptt.state, typing]);
}