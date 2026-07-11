import { getSidecarPort } from "../sidecar";

export async function apiBase(): Promise<string> {
  const port = await getSidecarPort();
  const host = window.location.hostname;
  return `http://${host}:${port}`;
}

export async function fetchWithRetry(
  url: string,
  opts?: RequestInit,
  tries: number = 5,
  baseDelay: number = 400,
): Promise<Response | null> {
  for (let attempt = 1; attempt <= tries; attempt++) {
    try {
      const resp = await fetch(url, opts);
      return resp;
    } catch (err) {
      if (attempt >= tries) return null;
      await new Promise((r) => setTimeout(r, baseDelay * 2 ** (attempt - 1)));
    }
  }
  return null;
}