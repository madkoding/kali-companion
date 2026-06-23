// AvatarStates — maps the combined runtime state to a single avatar mood.
//
// The avatar drives a small state machine derived from the chat + PTT + TTS
// hooks. Each mood corresponds to a set of SVG animation parameters consumed
// by KaliAvatar.

export type AvatarMood =
  | "sleep"      // idle for a while / no messages
  | "idle"       // connected, resting, eyes half-open
  | "listen"     // PTT/wake-word listening or recording
  | "think"     // assistant streaming / reasoning
  | "speak"     // TTS playing
  | "look"       // user typing / new input arrived
  | "judge";     // tool running / consent pending (the classic cat stare)

export interface MoodConfig {
  // Eyes
  eyeOpen: number;        // 0..1 (1 = fully open, 0 = closed)
  pupilDx: number;        // -1..1 horizontal gaze
  pupilDy: number;        // -1..1 vertical gaze
  blink: boolean;         // periodic blink animation
  blinkInterval: number;  // ms between blinks (0 = no blink)
  // Ears
  earTwitch: boolean;     // periodic ear twitch
  // Mouth / muzzle
  mouthOpen: number;      // 0..1 (for speaking)
  whiskersForward: boolean;
  // Head
  headTilt: number;       // degrees
  breatheScale: number;   // breathing amplitude
  // Tail
  tailSway: boolean;
  // Aura
  glow: number;           // 0..1 aura opacity
}

export const MOODS: Record<AvatarMood, MoodConfig> = {
  sleep: {
    eyeOpen: 0.05,
    pupilDx: 0, pupilDy: 0,
    blink: false, blinkInterval: 0,
    earTwitch: false,
    mouthOpen: 0,
    whiskersForward: false,
    headTilt: -2,
    breatheScale: 0.45,
    tailSway: false,
    glow: 0.04,
  },
  idle: {
    eyeOpen: 0.72,
    pupilDx: 0, pupilDy: 0.08,
    blink: true, blinkInterval: 4600,
    earTwitch: false,
    mouthOpen: 0,
    whiskersForward: false,
    headTilt: 0,
    breatheScale: 0.68,
    tailSway: true,
    glow: 0.1,
  },
  listen: {
    eyeOpen: 0.98,
    pupilDx: 0, pupilDy: 0,
    blink: true, blinkInterval: 2200,
    earTwitch: true,
    mouthOpen: 0,
    whiskersForward: true,
    headTilt: 2,
    breatheScale: 0.56,
    tailSway: true,
    glow: 0.34,
  },
  think: {
    eyeOpen: 0.58,
    pupilDx: -0.2, pupilDy: -0.22,
    blink: true, blinkInterval: 4300,
    earTwitch: false,
    mouthOpen: 0,
    whiskersForward: true,
    headTilt: -5,
    breatheScale: 0.58,
    tailSway: true,
    glow: 0.22,
  },
  speak: {
    eyeOpen: 0.9,
    pupilDx: 0, pupilDy: 0,
    blink: true, blinkInterval: 2800,
    earTwitch: false,
    mouthOpen: 0.25,
    whiskersForward: false,
    headTilt: 0,
    breatheScale: 0.54,
    tailSway: true,
    glow: 0.4,
  },
  look: {
    eyeOpen: 1,
    pupilDx: 0.25, pupilDy: -0.02,
    blink: true, blinkInterval: 2100,
    earTwitch: true,
    mouthOpen: 0,
    whiskersForward: false,
    headTilt: 3,
    breatheScale: 0.62,
    tailSway: true,
    glow: 0.18,
  },
  judge: {
    eyeOpen: 0.24,
    pupilDx: 0, pupilDy: -0.08,
    blink: false, blinkInterval: 0,
    earTwitch: false,
    mouthOpen: 0,
    whiskersForward: true,
    headTilt: -1,
    breatheScale: 0.42,
    tailSway: false,
    glow: 0.28,
  },
};
