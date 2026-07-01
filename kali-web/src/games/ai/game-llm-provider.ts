import type { StatusEvent } from "../../lib/protocol";

export interface GameLLMProvider {
  complete(prompt: string): Promise<string>;
}

/**
 * Build a lightweight LLM provider for in-game AI slots from the current
 * system status. Returns null when no LLM is configured, allowing the UI to
 * disable Kali-as-opponent modes gracefully.
 */
export function createGameLLMProvider(systemStatus: StatusEvent | null): GameLLMProvider | null {
  if (!systemStatus) return null;
  const url = systemStatus.llm_api_url?.trim();
  const model = systemStatus.llm_model?.trim();
  if (!url || !model) return null;

  return {
    async complete(prompt: string): Promise<string> {
      const endpoint = url.endsWith("/") ? `${url}v1/chat/completions` : `${url}/v1/chat/completions`;
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (systemStatus.llm_api_key_set) {
        // Key is managed by the sidecar; this placeholder signals that auth is
        // present but keeps the provider stateless.
        headers["Authorization"] = "Bearer present";
      }

      const body = {
        model,
        messages: [
          { role: "system", content: "Eres un jugador de Ta-Te-Ti. Responde SOLO con JSON valido: {\"row\":0|1|2,\"col\":0|1|2}." },
          { role: "user", content: prompt },
        ],
        temperature: 0.3,
        max_tokens: 64,
      };

      const res = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`LLM request failed: ${res.status} ${res.statusText}`);
      }

      const json = (await res.json()) as { choices?: { message?: { content?: string } }[] };
      const content = json.choices?.[0]?.message?.content ?? "";
      return content;
    },
  };
}

export function hasLLMIntegration(systemStatus: StatusEvent | null): boolean {
  if (!systemStatus) return false;
  return Boolean(systemStatus.llm_provider && systemStatus.llm_api_url && systemStatus.llm_model);
}
