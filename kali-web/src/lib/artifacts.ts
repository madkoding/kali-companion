// lib/artifacts.ts — REST client for fetching artifact content on demand.
//
// Closed artifacts keep only metadata (id, type, title, preview) in memory.
// When the user reopens one, the frontend fetches the full content via the
// REST endpoint GET /sessions/{sid}/artifacts/{aid} exposed by kali-core.
//
// The base URL is discovered the same way as the WS connection (Electron
// sidecar port via window.kali, or the Vite proxy in browser dev).

import type { ArtifactEvent } from "./protocol";
import { getSidecarPort } from "./sidecar";

/** Response shape of GET /sessions/{sid}/artifacts/{aid}. */
interface ArtifactResponse {
  id: string;
  type: ArtifactEvent["type"];
  windowType: string;
  title: string;
  content: string;
  language?: string;
}

let baseUrlCache: string | null = null;

async function baseUrl(): Promise<string> {
  if (baseUrlCache) return baseUrlCache;
  const port = await getSidecarPort();
  // In Electron the port is dynamic; in browser dev Vite proxies everything.
  if (port !== 8900) {
    baseUrlCache = `http://127.0.0.1:${port}`;
    return baseUrlCache;
  }
  baseUrlCache = "";
  return baseUrlCache;
}

/**
 * Fetch the full content of a single artifact by id.
 * Returns an `ArtifactEvent` (with content) ready to be stored in the
 * chat.artifacts Map and rendered in a window.
 */
export async function fetchArtifact(
  sessionId: string,
  artifactId: string,
  signal?: AbortSignal,
): Promise<ArtifactResponse> {
  const base = await baseUrl();
  const res = await fetch(`${base}/sessions/${encodeURIComponent(sessionId)}/artifacts/${encodeURIComponent(artifactId)}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!res.ok) {
    throw new Error(`fetchArtifact ${res.status}`);
  }
  return (await res.json()) as ArtifactResponse;
}