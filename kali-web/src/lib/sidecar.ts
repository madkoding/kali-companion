export async function getSidecarPort(): Promise<number> {
  const w = window as unknown as { kali?: { getSidecarPort?: () => Promise<number> } };
  if (w.kali?.getSidecarPort) {
    try {
      const port = await w.kali.getSidecarPort();
      if (typeof port === "number" && port > 0) return port;
    } catch {
      // not running under Electron
    }
  }
  const envPort = import.meta.env.VITE_KALI_PORT;
  if (envPort) return Number(envPort);
  try {
    const resp = await fetch("/api/sidecar-port");
    if (resp.ok) {
      const data = await resp.json();
      if (data.port) return data.port;
    }
  } catch {
    // no sidecar-port endpoint
  }
  return 8900;
}
