// KaliToysSection — game session persistence and game-specific AI settings.

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Gamepad2 } from "lucide-react";
import type { StatusEvent } from "../../lib/protocol";
import { useStage } from "../../stage/StageProvider";
import { SelectField, SliderField, TextField, ToggleField } from "./fields";

interface Props {
  systemStatus: StatusEvent | null;
  onUpdate: (patch: Record<string, unknown>) => void;
}

const DEFAULT_TIMEOUTS = [12_000, 3_000, 2_000];
const DEFAULT_MAX_RETRIES = 2;
const DEFAULT_TEMPERATURE = 0.7;
const DEFAULT_MAX_TOKENS = 256;

export function KaliToysSection({ systemStatus, onUpdate }: Props) {
  const { t } = useTranslation();
  const { connections } = useStage();
  const [advanced, setAdvanced] = useState(false);

  const gameSessionPath = systemStatus?.game_session_path ?? "";
  const gameAiGlobalTimeoutMs = systemStatus?.game_ai_global_timeout_ms ?? 20_000;
  const gameConnectionId = systemStatus?.game_connection_id ?? "active";
  const gameModel = systemStatus?.game_model ?? "";
  const gameTemperature = systemStatus?.game_temperature ?? DEFAULT_TEMPERATURE;
  const gameMaxTokens = systemStatus?.game_max_tokens ?? DEFAULT_MAX_TOKENS;
  const timeout1 = systemStatus?.game_retry_timeout_1_ms ?? DEFAULT_TIMEOUTS[0];
  const timeout2 = systemStatus?.game_retry_timeout_2_ms ?? DEFAULT_TIMEOUTS[1];
  const timeout3 = systemStatus?.game_retry_timeout_3_ms ?? DEFAULT_TIMEOUTS[2];
  const gameMaxRetries = systemStatus?.game_max_retries ?? DEFAULT_MAX_RETRIES;

  const activeLabel = t("settings.game_connection_active");
  const connectionOptions = [
    { id: "active", label: activeLabel },
    ...connections.map((c) => ({
      id: c.id,
      label: `${c.kind === "local" ? "Local" : "Cloud"}: ${c.api_url}`,
    })),
  ];

  const selectedConnection = connections.find((c) => c.id === gameConnectionId);
  const showModelSelector = gameConnectionId !== "active" && (selectedConnection?.model_count ?? 0) > 1;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 pb-1 border-b border-border">
        <Gamepad2 size={15} className="text-accent" />
        <span className="text-sm font-semibold text-foreground">
          {t("settings.section.kali_toys")}
        </span>
      </div>

      <TextField
        label={t("settings.game_session_path")}
        value={gameSessionPath}
        onChange={(v) => onUpdate({ game_session_path: v })}
        placeholder="~/.kali/game-sessions"
        helperText={t("settings.game_session_path_hint")}
      />

      <SliderField
        label={t("settings.game_ai_global_timeout_ms")}
        value={gameAiGlobalTimeoutMs / 1000}
        min={5}
        max={120}
        step={5}
        onChange={(v) => onUpdate({ game_ai_global_timeout_ms: Math.round(v * 1000) })}
        displayValue={`${(gameAiGlobalTimeoutMs / 1000).toFixed(0)}${t("common.seconds_abbrev")}`}
        helperText={t("settings.game_ai_global_timeout_ms_hint")}
      />

      <SelectField
        label={t("settings.game_connection_id")}
        value={gameConnectionId}
        onChange={(v) => {
          const patch: Record<string, unknown> = { game_connection_id: v, game_model: "" };
          onUpdate(patch);
        }}
      >
        {connectionOptions.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </SelectField>

      {showModelSelector && (
        <SelectField
          label={t("settings.game_model")}
          value={gameModel || selectedConnection?.active_model || ""}
          onChange={(v) => onUpdate({ game_model: v })}
        >
          {selectedConnection?.active_model && (
            <option key={selectedConnection.active_model} value={selectedConnection.active_model}>
              {selectedConnection.active_model}
            </option>
          )}
        </SelectField>
      )}

      <ToggleField
        label={t("settings.advanced_configuration")}
        checked={advanced}
        onChange={setAdvanced}
      />

      {advanced && (
        <div className="flex flex-col gap-4 pl-3 border-l-2 border-border">
          <SliderField
            label={t("settings.game_temperature")}
            value={gameTemperature}
            min={0}
            max={1.5}
            step={0.1}
            onChange={(v) => onUpdate({ game_temperature: v })}
            displayValue={gameTemperature.toFixed(1)}
          />

          <SliderField
            label={t("settings.game_max_tokens")}
            value={gameMaxTokens}
            min={16}
            max={4096}
            step={16}
            onChange={(v) => onUpdate({ game_max_tokens: Math.round(v) })}
            displayValue={String(gameMaxTokens)}
          />

          <SliderField
            label={t("settings.game_retry_timeout_1_ms")}
            value={timeout1}
            min={1000}
            max={60_000}
            step={1000}
            onChange={(v) => onUpdate({ game_retry_timeout_1_ms: Math.round(v) })}
            displayValue={`${timeout1}ms`}
          />

          <SliderField
            label={t("settings.game_retry_timeout_2_ms")}
            value={timeout2}
            min={1000}
            max={30_000}
            step={1000}
            onChange={(v) => onUpdate({ game_retry_timeout_2_ms: Math.round(v) })}
            displayValue={`${timeout2}ms`}
          />

          <SliderField
            label={t("settings.game_retry_timeout_3_ms")}
            value={timeout3}
            min={1000}
            max={20_000}
            step={1000}
            onChange={(v) => onUpdate({ game_retry_timeout_3_ms: Math.round(v) })}
            displayValue={`${timeout3}ms`}
          />

          <SliderField
            label={t("settings.game_max_retries")}
            value={gameMaxRetries}
            min={1}
            max={5}
            step={1}
            onChange={(v) => onUpdate({ game_max_retries: Math.round(v) })}
            displayValue={String(gameMaxRetries)}
          />
        </div>
      )}
    </div>
  );
}
