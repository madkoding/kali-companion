// KaliAvatar — animated calico cat presence for the Stage.
//
// The reference direction is a friendly seated calico: large green eyes,
// visible red collar with bell, soft cream fur, orange and black patches,
// curled tail, and a calm silhouette that reacts to the assistant state.

import { useEffect, useId, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MOODS, type AvatarMood, type MoodConfig } from "./AvatarStates";

interface Props {
  mood: AvatarMood;
  audioLevel?: number; // 0..1, drives mouth while speaking
  size?: number; // px (width and height)
}

interface EyeProps {
  cx: number;
  cy: number;
  open: number;
  pupilDx: number;
  pupilDy: number;
  side: "left" | "right";
  mood: AvatarMood;
  reduceMotion: boolean;
  eyeIris: string;
  eyeIrisEdge: string;
  eyePupil: string;
  eyeShine: string;
}

function Eye({
  cx,
  cy,
  open,
  pupilDx,
  pupilDy,
  side,
  mood,
  reduceMotion,
  eyeIris,
  eyeIrisEdge,
  eyePupil,
  eyeShine,
}: EyeProps) {
  const pupilBaseX = cx + pupilDx * 5.5;
  const pupilBaseY = cy + pupilDy * 4.2;
  const wanderX = side === "left" ? [0, 0.7, -0.35, 0] : [0, -0.55, 0.4, 0];
  const wanderY = side === "left" ? [0, -0.22, 0.18, 0] : [0, 0.18, -0.12, 0];
  const wanderDuration =
    mood === "look" ? 3.4 :
    mood === "listen" ? 4.2 :
    mood === "think" ? 5.4 :
    mood === "speak" ? 4.6 :
    5.0;

  return (
    <g>
      <motion.ellipse
        cx={cx}
        cy={cy}
        rx={15}
        animate={{ ry: 11.5 * Math.max(open, 0.08), cy: cy + (1 - open) * 1.2 }}
        transition={{ duration: 0.12, ease: "easeOut" }}
        fill="#fffdf8"
        stroke="#c8b9a9"
        strokeWidth="1.2"
      />
      <motion.g
        animate={reduceMotion ? { x: 0, y: 0 } : { x: wanderX, y: wanderY }}
        transition={
          reduceMotion
            ? { duration: 0 }
            : {
                duration: wanderDuration,
                repeat: Infinity,
                repeatType: "mirror",
                ease: "easeInOut",
              }
        }
      >
        <circle cx={pupilBaseX} cy={pupilBaseY} r={8.8} fill={eyeIris} stroke={eyeIrisEdge} strokeWidth="1" />
        <circle cx={pupilBaseX + 1.2} cy={pupilBaseY + 0.8} r={4.1} fill={eyePupil} />
        <circle cx={pupilBaseX - 3.0} cy={pupilBaseY - 3.0} r={1.9} fill={eyeShine} opacity="0.95" />
        <circle cx={pupilBaseX + 3.3} cy={pupilBaseY - 1.8} r={0.9} fill={eyeShine} opacity="0.75" />
      </motion.g>
      <path
        d={`M${cx - 10} ${cy - 11} Q${cx} ${cy - 15} ${cx + 10} ${cy - 11}`}
        fill="none"
        stroke="#dfd4c7"
        strokeWidth="1.2"
        strokeLinecap="round"
        opacity="0.55"
      />
    </g>
  );
}

export function KaliAvatar({ mood, audioLevel = 0, size = 180 }: Props) {
  const cfg: MoodConfig = MOODS[mood];
  const reduceMotion = useReducedMotion() ?? false;
  const [blinking, setBlinking] = useState(false);
  const blinkTimer = useRef<number | null>(null);
  const uid = useId().replace(/:/g, "");

  useEffect(() => {
    if (blinkTimer.current) {
      clearTimeout(blinkTimer.current);
      blinkTimer.current = null;
    }
    if (!cfg.blink || cfg.blinkInterval === 0) {
      setBlinking(false);
      return;
    }

    let cancelled = false;
    const schedule = () => {
      const jitter = 0.85 + Math.random() * 0.3;
      blinkTimer.current = window.setTimeout(() => {
        if (cancelled) return;
        setBlinking(true);
        blinkTimer.current = window.setTimeout(() => {
          if (cancelled) return;
          setBlinking(false);
          schedule();
        }, reduceMotion ? 90 : 120);
      }, Math.max(1800, cfg.blinkInterval * jitter));
    };

    schedule();

    return () => {
      cancelled = true;
      if (blinkTimer.current) clearTimeout(blinkTimer.current);
    };
  }, [cfg.blink, cfg.blinkInterval, reduceMotion, mood]);

  const eyeOpen = blinking ? 0.06 : cfg.eyeOpen;
  const mouthOpen = mood === "speak" ? Math.min(1, 0.18 + audioLevel * 1.4) : cfg.mouthOpen;

  const bodyFloatY = reduceMotion ? 0 : 2 + cfg.breatheScale * 2.5;
  const bodyFloatScale = reduceMotion ? 1 : 1 + cfg.breatheScale * 0.012;
  const bodyFloatDuration =
    mood === "speak" ? 1.8 :
    mood === "listen" ? 2.4 :
    mood === "think" ? 3.4 :
    mood === "look" ? 2.8 :
    mood === "judge" ? 3.8 :
    4.5;

  const tailDuration =
    mood === "speak" ? 2.8 :
    mood === "listen" ? 2.2 :
    mood === "look" ? 2.6 :
    mood === "think" ? 3.4 :
    4.4;

  const bellDuration =
    mood === "speak" ? 1.8 :
    mood === "listen" ? 2.0 :
    mood === "look" ? 2.5 :
    3.6;

  const earDuration =
    mood === "listen" ? 1.6 :
    mood === "look" ? 1.9 :
    mood === "speak" ? 2.4 :
    3.0;

  const headWobbleDuration =
    mood === "speak" ? 1.9 :
    mood === "listen" ? 2.6 :
    mood === "think" ? 3.6 :
    4.2;

  const glowOpacity = cfg.glow;
  const haloRef = `url(#${uid}-halo)`;
  const creamRef = `url(#${uid}-cream)`;
  const orangeRef = `url(#${uid}-orange)`;
  const blackRef = `url(#${uid}-black)`;
  const tailRef = `url(#${uid}-tail)`;
  const collarRef = `url(#${uid}-collar)`;
  const bellRef = `url(#${uid}-bell)`;
  const irisRef = `url(#${uid}-iris)`;

  const shimmerEnabled = !reduceMotion && mood !== "judge";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <motion.div
        className="presence-glow absolute inset-0 rounded-full"
        animate={
          shimmerEnabled
            ? {
                opacity: [Math.max(0.03, glowOpacity * 0.5), glowOpacity, Math.max(0.03, glowOpacity * 0.65)],
                scale: [0.96, 1.08, 0.98],
              }
            : {
                opacity: glowOpacity,
                scale: 1,
              }
        }
        transition={
          shimmerEnabled
            ? { duration: bodyFloatDuration, repeat: Infinity, ease: "easeInOut" }
            : { duration: 0.3, ease: "easeOut" }
        }
      />

      <motion.svg
        viewBox="0 0 240 260"
        width={size}
        height={size}
        style={{ position: "relative", zIndex: 1 }}
      >
        <defs>
          <radialGradient id={`${uid}-halo`} cx="50%" cy="42%" r="68%">
            <stop offset="0%" stopColor="#fffdf6" stopOpacity="0.95" />
            <stop offset="70%" stopColor="#d6f7ea" stopOpacity="0.36" />
            <stop offset="100%" stopColor="#9ee7d8" stopOpacity="0.08" />
          </radialGradient>
          <linearGradient id={`${uid}-cream`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fff8ec" />
            <stop offset="100%" stopColor="#f1e2cf" />
          </linearGradient>
          <linearGradient id={`${uid}-shadow`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#d8ddea" />
            <stop offset="100%" stopColor="#bbc6d8" />
          </linearGradient>
          <linearGradient id={`${uid}-orange`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5b065" />
            <stop offset="100%" stopColor="#d97b2c" />
          </linearGradient>
          <linearGradient id={`${uid}-black`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#433c36" />
            <stop offset="100%" stopColor="#171412" />
          </linearGradient>
          <linearGradient id={`${uid}-collar`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#ad2b36" />
            <stop offset="100%" stopColor="#d64949" />
          </linearGradient>
          <radialGradient id={`${uid}-bell`} cx="40%" cy="35%" r="70%">
            <stop offset="0%" stopColor="#fff5b2" />
            <stop offset="55%" stopColor="#f8c64f" />
            <stop offset="100%" stopColor="#c58216" />
          </radialGradient>
          <radialGradient id={`${uid}-iris`} cx="35%" cy="30%" r="72%">
            <stop offset="0%" stopColor="#f2ffbd" />
            <stop offset="55%" stopColor="#86be35" />
            <stop offset="100%" stopColor="#3d6f14" />
          </radialGradient>
          <linearGradient id={`${uid}-tail`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5ad5f" />
            <stop offset="100%" stopColor="#db7d2d" />
          </linearGradient>
        </defs>

        <motion.circle
          cx="120"
          cy="118"
          r="103"
          fill="none"
          stroke={haloRef}
          strokeWidth="8"
          animate={
            shimmerEnabled
              ? {
                  opacity: [0.58, 0.92, 0.68],
                  scale: [0.99, 1.02, 1],
                }
              : { opacity: 0.7, scale: 1 }
          }
          transition={
            shimmerEnabled
              ? { duration: bodyFloatDuration + 0.8, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.2 }
          }
        />

        <ellipse cx="120" cy="232" rx="66" ry="15" fill="#6e8a87" opacity="0.16" />

        <motion.g
          style={{ transformBox: "fill-box", transformOrigin: "170px 182px" }}
          animate={
            reduceMotion || !cfg.tailSway
              ? { rotate: 0, y: 0 }
              : { rotate: [0, 6, 0, -5, 0], y: [0, -0.8, 0] }
          }
          transition={
            reduceMotion || !cfg.tailSway
              ? { duration: 0 }
              : {
                  duration: tailDuration,
                  repeat: Infinity,
                  ease: "easeInOut",
                }
          }
        >
          <path
            d="M168 178 C196 181, 210 200, 204 216 C199 228, 187 235, 173 235 C182 226, 184 213, 179 203 C174 193, 167 186, 157 183"
            fill="none"
            stroke={tailRef}
            strokeWidth="18"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M171 178 C190 181, 200 192, 198 205 C196 215, 189 223, 179 226"
            fill="none"
            stroke="#c86f26"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.7"
          />
          <path
            d="M197 219 C202 223, 205 229, 204 235"
            fill="none"
            stroke="#f5c58f"
            strokeWidth="3"
            strokeLinecap="round"
            opacity="0.45"
          />
        </motion.g>

        <motion.g
          animate={
            reduceMotion
              ? { y: 0, scaleY: 1 }
              : { y: [0, -bodyFloatY, 0], scaleY: [1, bodyFloatScale, 1] }
          }
          transition={
            reduceMotion
              ? { duration: 0 }
              : {
                  duration: bodyFloatDuration,
                  repeat: Infinity,
                  ease: "easeInOut",
                }
          }
        >
          <ellipse cx="120" cy="174" rx="69" ry="62" fill={creamRef} />
          <path
            d="M69 150 C52 170, 52 205, 74 221 C89 231, 110 228, 116 213 C97 204, 89 190, 89 172 C89 160, 93 151, 100 144 C92 142, 80 144, 69 150 Z"
            fill={blackRef}
            opacity="0.96"
          />
          <path
            d="M153 143 C177 146, 189 160, 191 182 C192 201, 183 216, 167 225 C157 230, 145 230, 139 225 C150 216, 157 205, 159 192 C161 177, 158 162, 153 143 Z"
            fill={orangeRef}
            opacity="0.94"
          />
          <path
            d="M103 144 C116 136, 133 136, 146 144 C156 151, 161 165, 160 183 C159 207, 149 221, 135 228 C126 232, 113 232, 104 228 C88 221, 79 208, 79 187 C79 167, 86 151, 103 144 Z"
            fill="#fffaf1"
            opacity="0.92"
          />
          <ellipse cx="120" cy="191" rx="45" ry="48" fill="#fffef9" />
          <path
            d="M82 156 C90 149, 101 145, 110 147 C102 158, 98 169, 98 183 C98 196, 102 208, 110 219 C97 222, 86 219, 77 211 C68 203, 65 191, 65 180 C65 170, 70 162, 82 156 Z"
            fill={blackRef}
            opacity="0.92"
          />
          <path
            d="M156 160 C166 163, 174 169, 177 179 C180 190, 178 202, 171 212 C165 220, 155 225, 144 226 C150 217, 154 206, 154 194 C154 181, 153 170, 156 160 Z"
            fill={orangeRef}
            opacity="0.92"
          />
          <rect x="92" y="190" width="18" height="43" rx="9" fill="#fbfbf6" />
          <rect x="122" y="189" width="18" height="44" rx="9" fill="#fbfbf6" />
          <ellipse cx="101" cy="228" rx="12" ry="7.5" fill="#f4efe6" />
          <ellipse cx="131" cy="228" rx="12" ry="7.5" fill="#f4efe6" />
          <ellipse cx="84" cy="227" rx="10" ry="6.8" fill="#babfd2" opacity="0.45" />
        </motion.g>

        <motion.g
          animate={
            reduceMotion
              ? { rotate: 0 }
              : {
                  rotate: cfg.earTwitch ? [0, -4, 0, 3, 0] : 0,
                }
          }
          transition={
            reduceMotion
              ? { duration: 0 }
              : {
                  duration: earDuration,
                  repeat: cfg.earTwitch ? Infinity : 0,
                  repeatDelay: cfg.earTwitch ? 0.9 : 0,
                  ease: "easeInOut",
                }
          }
          style={{ transformBox: "fill-box", transformOrigin: "120px 76px" }}
        >
          <path d="M62 71 L41 38 L69 49 L79 79 Z" fill={orangeRef} stroke="#bc742d" strokeWidth="1.3" />
          <path d="M66 67 L53 47 L68 53 L73 70 Z" fill="#f8ccaa" opacity="0.88" />
          <path d="M176 70 L198 39 L170 49 L160 79 Z" fill={creamRef} stroke="#bea88b" strokeWidth="1.3" />
          <path d="M172 66 L185 47 L170 53 L165 69 Z" fill="#ead1b6" opacity="0.88" />
        </motion.g>

        <motion.g
          style={{ transformBox: "fill-box", transformOrigin: "120px 122px" }}
          animate={
            reduceMotion
              ? { rotate: cfg.headTilt, y: 0 }
              : {
                  rotate: cfg.headTilt,
                  y: [0, -0.8, 0],
                }
          }
          transition={
            reduceMotion
              ? { duration: 0.3, ease: "easeOut" }
              : {
                  duration: headWobbleDuration,
                  repeat: Infinity,
                  ease: "easeInOut",
                }
          }
        >
          <ellipse cx="120" cy="103" rx="66" ry="57" fill={creamRef} stroke="#bca98c" strokeWidth="1.3" />
          <path
            d="M76 77 C64 92, 65 113, 80 124 C90 132, 105 135, 118 128 C113 117, 112 101, 115 90 C108 87, 97 80, 76 77 Z"
            fill={orangeRef}
            opacity="0.95"
          />
          <path
            d="M122 65 C137 58, 156 61, 166 75 C174 85, 174 101, 169 112 C164 122, 154 128, 144 128 C148 115, 147 102, 143 92 C138 81, 130 72, 122 65 Z"
            fill={blackRef}
            opacity="0.96"
          />
          <path
            d="M101 54 C108 49, 119 49, 126 55 C130 58, 133 67, 129 74 C124 72, 117 71, 111 73 C108 68, 104 62, 101 54 Z"
            fill={orangeRef}
            opacity="0.9"
          />
          <path
            d="M95 103 C101 88, 110 78, 120 74 C131 78, 139 89, 145 102 C147 113, 146 123, 139 131 C132 137, 109 137, 102 131 C95 124, 92 114, 95 103 Z"
            fill="#fffaf1"
            opacity="0.94"
          />

          <Eye
            cx={93}
            cy={99}
            open={eyeOpen}
            pupilDx={cfg.pupilDx}
            pupilDy={cfg.pupilDy}
            side="left"
            mood={mood}
            reduceMotion={reduceMotion}
            eyeIris={irisRef}
            eyeIrisEdge="#4b7b1a"
            eyePupil="#121212"
            eyeShine="#ffffff"
          />
          <Eye
            cx={147}
            cy={99}
            open={eyeOpen}
            pupilDx={cfg.pupilDx}
            pupilDy={cfg.pupilDy}
            side="right"
            mood={mood}
            reduceMotion={reduceMotion}
            eyeIris={irisRef}
            eyeIrisEdge="#4b7b1a"
            eyePupil="#121212"
            eyeShine="#ffffff"
          />

          <path
            d="M118 124 L124 132 L118 138 L112 132 Z"
            fill="#241d19"
          />
          <path
            d="M120 136 C114 137, 109 141, 106 145"
            stroke="#755b4c"
            strokeWidth="1.5"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M120 136 C126 137, 131 141, 134 145"
            stroke="#755b4c"
            strokeWidth="1.5"
            strokeLinecap="round"
            fill="none"
          />
          {mouthOpen > 0.14 && (
            <motion.ellipse
              cx="120"
              cy={141 + mouthOpen * 4}
              rx={4 + mouthOpen * 3.5}
              ry={mouthOpen * 4.4}
              fill="#7d3b3b"
              opacity={0.72}
              animate={{ cy: 141 + mouthOpen * 4.4, rx: 4 + mouthOpen * 3.5, ry: mouthOpen * 4.4 }}
              transition={{ duration: 0.1 }}
            />
          )}

          <motion.g
            animate={
              reduceMotion || !cfg.whiskersForward
                ? { x: 0 }
                : { x: [0, 1.8, 0] }
            }
            transition={
              reduceMotion || !cfg.whiskersForward
                ? { duration: 0 }
                : { duration: 2.8, repeat: Infinity, ease: "easeInOut" }
            }
          >
            <g stroke="#f3e8d7" strokeWidth="1.2" strokeLinecap="round" opacity="0.95">
              <line x1="56" y1="118" x2="30" y2="112" />
              <line x1="54" y1="126" x2="25" y2="128" />
              <line x1="57" y1="133" x2="31" y2="144" />
              <line x1="184" y1="118" x2="210" y2="112" />
              <line x1="186" y1="126" x2="215" y2="128" />
              <line x1="183" y1="133" x2="209" y2="144" />
            </g>
          </motion.g>

          <motion.g
            animate={
              reduceMotion
                ? { rotate: 0 }
                : {
                    rotate:
                      mood === "speak" ? [0, -6, 0, 5, 0] :
                      mood === "listen" ? [0, -4, 0, 4, 0] :
                      [0, -2, 0, 2, 0],
                  }
            }
            transition={
              reduceMotion
                ? { duration: 0 }
                : {
                    duration: bellDuration,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }
            }
            style={{ transformBox: "fill-box", transformOrigin: "120px 132px" }}
          >
            <path
              d="M89 130 C104 123, 136 123, 151 130"
              stroke={collarRef}
              strokeWidth="13"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M91 129 C107 123, 133 123, 149 129"
              stroke="#ff6a73"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
              opacity="0.45"
            />
            <motion.g
              animate={
                reduceMotion
                  ? { y: 0 }
                  : { y: [0, 1.1, 0] }
              }
              transition={
                reduceMotion
                  ? { duration: 0 }
                  : {
                      duration: bellDuration,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }
              }
            >
              <circle cx="120" cy="140" r="8.8" fill={bellRef} stroke="#9f6b10" strokeWidth="1" />
              <path d="M117 139 h6" stroke="#8b5a0d" strokeWidth="1.3" strokeLinecap="round" />
              <circle cx="123" cy="137" r="1.6" fill="#fff7d2" opacity="0.9" />
            </motion.g>
          </motion.g>
        </motion.g>

        {shimmerEnabled && (
          <motion.path
            d="M186 223 l5 5 l-5 5 l-5 -5 z"
            fill="#fff7dc"
            opacity="0.75"
            animate={{ scale: [1, 1.25, 1], opacity: [0.65, 1, 0.65] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
      </motion.svg>
    </div>
  );
}
