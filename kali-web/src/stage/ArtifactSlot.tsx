// ArtifactSlot — expandable wrapper that renders an artifact by type.
//
// Inline (default): rendered inside the moment flow with a header (title +
// expand button). Expanded: a near-fullscreen overlay with a backdrop.
//
// Reuses the existing artifact renderers (HtmlArtifact, MarkdownArtifact,
// DiffArtifact, WidgetGrid) unchanged.

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Maximize2, Minimize2, X } from "lucide-react";
import type { ArtifactEvent } from "../lib/protocol";
import { HtmlArtifact } from "../components/artifacts/HtmlArtifact";
import { MarkdownArtifact } from "../components/artifacts/MarkdownArtifact";
import { DiffArtifact } from "../components/artifacts/DiffArtifact";
import { WidgetGrid } from "../components/artifacts/WidgetGrid";

interface Props {
  artifact: ArtifactEvent;
  expanded: boolean;
  onToggle: () => void;
  imageReadyKeys?: Set<string>;
  onRequestImage?: (key: string) => void;
}

function ArtifactBody({ artifact, imageReadyKeys, onRequestImage }: Omit<Props, "expanded" | "onToggle">) {
  switch (artifact.type) {
    case "html":
      return <HtmlArtifact content={artifact.content} />;
    case "markdown":
      return <MarkdownArtifact content={artifact.content} />;
    case "diff":
      return <DiffArtifact content={artifact.content} />;
    case "widget":
      return <WidgetGrid content={artifact.content} imageReadyKeys={imageReadyKeys} onRequestImage={onRequestImage} />;
    default:
      return <div className="p-4 text-sm text-muted">Unsupported artifact type</div>;
  }
}

export function ArtifactSlot({ artifact, expanded, onToggle, imageReadyKeys, onRequestImage }: Props) {
  // Lock body scroll while expanded.
  useEffect(() => {
    if (!expanded) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, [expanded]);

  return (
    <>
      {/* Inline form */}
      <div className="artifact-slot">
        <div className="artifact-slot-header">
          <span className="artifact-slot-title">{artifact.title}</span>
          <button className="artifact-expand-btn" onClick={onToggle} aria-label="Expand">
            <Maximize2 size={14} />
          </button>
        </div>
        <div className="max-h-[420px] overflow-auto stage-scroll">
          <ArtifactBody artifact={artifact} imageReadyKeys={imageReadyKeys} onRequestImage={onRequestImage} />
        </div>
      </div>

      {/* Expanded overlay */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 md:p-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
          >
            <motion.div
              className="bg-elevated border border-border rounded-xl w-full max-w-5xl h-full max-h-[88vh] flex flex-col overflow-hidden"
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="artifact-slot-header">
                <span className="artifact-slot-title">{artifact.title}</span>
                <button className="artifact-expand-btn" onClick={onToggle} aria-label="Collapse">
                  <Minimize2 size={14} />
                </button>
                <button className="artifact-expand-btn" onClick={onToggle} aria-label="Close">
                  <X size={14} />
                </button>
              </div>
              <div className="flex-1 overflow-auto stage-scroll">
                <ArtifactBody artifact={artifact} imageReadyKeys={imageReadyKeys} onRequestImage={onRequestImage} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}