import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Search, Server, Cloud } from "lucide-react";
import { Modal } from "../../ui/Modal";
import { testConnection } from "../../../lib/api/connections";
import type { ConnectionSummary } from "../../../lib/protocol";

interface Props {
  open: boolean;
  onClose: () => void;
  gameConnectionId: string | undefined;
  gameModel: string;
  connections: ConnectionSummary[];
  activeConnectionId: string | null;
  activeConnectionModel: string | null;
  onSave: (gameConnectionId: string, gameModel: string) => void;
}

type Step = "connection" | "model";

export function GameConnectionPicker({
  open,
  onClose,
  gameConnectionId,
  gameModel,
  connections,
  activeConnectionId,
  activeConnectionModel,
  onSave,
}: Props) {
  const { t } = useTranslation();

  const [step, setStep] = useState<Step>("connection");
  const [selectedConnId, setSelectedConnId] = useState<string>(gameConnectionId ?? "active");
  const [selectedModel, setSelectedModel] = useState<string>(gameModel);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [modelQuery, setModelQuery] = useState("");

  const selectedConn = connections.find((c) => c.id === selectedConnId);

  useEffect(() => {
    if (!open) return;
    setStep("connection");
    setSelectedConnId(gameConnectionId ?? "active");
    setSelectedModel(gameModel);
    setAvailableModels([]);
    setProbeError(null);
    setModelQuery("");
  }, [open, gameConnectionId, gameModel]);

  const handleConnSelect = async (connId: string) => {
    setSelectedConnId(connId);

    if (connId === "active") {
      setAvailableModels([]);
      setSelectedModel(activeConnectionModel ?? "");
      return;
    }

    const conn = connections.find((c) => c.id === connId);
    if (!conn) return;

    if (conn.model_count === 1 && conn.active_model) {
      setAvailableModels([conn.active_model]);
      setSelectedModel(conn.active_model);
      return;
    }

    setLoadingModels(true);
    setProbeError(null);
    try {
      const result = await testConnection(conn.api_url, "");
      if (result.ok) {
        setAvailableModels(result.models);
        setSelectedModel(selectedModel && result.models.includes(selectedModel) ? selectedModel : (result.models[0] ?? ""));
      } else {
        setProbeError(result.detail || t("connections.test_failed", { reason: "?" }));
        setAvailableModels([]);
      }
    } catch (err) {
      setProbeError((err as Error).message);
      setAvailableModels([]);
    } finally {
      setLoadingModels(false);
    }

    if (conn.model_count > 1 || (conn.model_count === 0 && !conn.active_model)) {
      setStep("model");
    }
  };

  const handleConfirmModel = () => {
    onSave(selectedConnId, selectedModel);
    onClose();
  };

  const handleBack = () => {
    setStep("connection");
    setProbeError(null);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={step === "connection" ? t("settings.game_ai_title") : selectedConn?.name}
      size="md"
      bare={step === "model"}
    >
      {step === "connection" ? (
        <ConnectionStep
          connections={connections}
          activeConnectionId={activeConnectionId}
          gameConnectionId={gameConnectionId}
          selectedConnId={selectedConnId}
          onSelect={handleConnSelect}
          activeConnectionModel={activeConnectionModel}
        />
      ) : (
        <ModelStep
          conn={selectedConn}
          selectedModel={selectedModel}
          availableModels={availableModels}
          loadingModels={loadingModels}
          probeError={probeError}
          modelQuery={modelQuery}
          onModelQueryChange={setModelQuery}
          onBack={handleBack}
          onConfirm={handleConfirmModel}
        />
      )}
    </Modal>
  );
}

function ConnectionStep({
  connections,
  activeConnectionId,
  gameConnectionId,
  selectedConnId,
  onSelect,
  activeConnectionModel,
}: {
  connections: ConnectionSummary[];
  activeConnectionId: string | null;
  gameConnectionId: string | undefined;
  selectedConnId: string;
  onSelect: (id: string) => void;
  activeConnectionModel: string | null;
}) {
  const { t } = useTranslation();

  const local = connections.filter((c) => c.kind === "local");
  const cloud = connections.filter((c) => c.kind === "cloud");

  const activeConnName = connections.find((c) => c.id === activeConnectionId)?.name ?? "Unknown";

  return (
    <div className="flex flex-col gap-1">
      <ConnectionRadio
        id="active"
        label={t("settings.game_ai_using_active")}
        sublabel={`${activeConnName}${activeConnectionModel ? ` → ${activeConnectionModel}` : ""}`}
        selected={selectedConnId === "active"}
        onSelect={onSelect}
      />

      <div className="h-px bg-border my-2" />

      {local.map((conn) => (
        <ConnectionRadio
          key={conn.id}
          id={conn.id}
          label={conn.name}
          sublabel={conn.api_url}
          kind={conn.kind}
          selected={selectedConnId === conn.id}
          isActive={conn.id === activeConnectionId}
          isGame={conn.id === gameConnectionId}
          onSelect={onSelect}
        />
      ))}

      {cloud.map((conn) => (
        <ConnectionRadio
          key={conn.id}
          id={conn.id}
          label={conn.name}
          sublabel={conn.api_url}
          kind={conn.kind}
          selected={selectedConnId === conn.id}
          isActive={conn.id === activeConnectionId}
          isGame={conn.id === gameConnectionId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function ConnectionRadio({
  id,
  label,
  sublabel,
  kind,
  selected,
  isActive,
  isGame,
  onSelect,
}: {
  id: string;
  label: string;
  sublabel: string;
  kind?: "local" | "cloud";
  selected: boolean;
  isActive?: boolean;
  isGame?: boolean;
  onSelect: (id: string) => void;
}) {
  const { t } = useTranslation();
  const Icon = kind === "cloud" ? Cloud : Server;

  return (
    <button
      onClick={() => onSelect(id)}
      className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg border transition-colors text-left w-full ${
        selected
          ? "border-accent/40 bg-accent/5"
          : "border-transparent hover:border-border"
      }`}
    >
      <div className={`mt-0.5 w-4 h-4 rounded-full border-2 shrink-0 flex items-center justify-center ${
        selected ? "border-accent" : "border-muted"
      }`}>
        {selected && <div className="w-2 h-2 rounded-full bg-accent" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {kind && <Icon size={12} className="text-muted shrink-0" />}
          <span className="text-xs font-medium text-foreground truncate">{label}</span>
          {isActive && (
            <span className="text-[10px] font-mono bg-ok/20 text-ok rounded px-1.5 py-0.5 shrink-0">
              {t("connections.active_badge")}
            </span>
          )}
          {isGame && (
            <span className="text-[10px] font-mono bg-accent/20 text-accent rounded px-1.5 py-0.5 shrink-0">
              {t("connections.games_badge")}
            </span>
          )}
        </div>
        <div className="text-[10px] text-muted font-mono mt-0.5 truncate">{sublabel}</div>
      </div>
    </button>
  );
}

function ModelStep({
  conn,
  selectedModel,
  availableModels,
  loadingModels,
  probeError,
  modelQuery,
  onModelQueryChange,
  onBack,
  onConfirm,
}: {
  conn: ConnectionSummary | undefined;
  selectedModel: string;
  availableModels: string[];
  loadingModels: boolean;
  probeError: string | null;
  modelQuery: string;
  onModelQueryChange: (q: string) => void;
  onBack: () => void;
  onConfirm: () => void;
}) {
  const { t } = useTranslation();

  const filteredModels = useMemo(() => {
    if (!modelQuery.trim()) return availableModels;
    const q = modelQuery.toLowerCase();
    return availableModels.filter((m: string) => m.toLowerCase().includes(q));
  }, [availableModels, modelQuery]);

  return (
    <div className="flex flex-col gap-4">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors self-start"
      >
        <ArrowLeft size={13} />
        {conn?.name ?? t("settings.game_ai_title")}
      </button>

      {conn && (
        <div className="px-3 py-2 rounded-lg bg-surface border border-border">
          <div className="text-xs text-foreground font-medium">{conn.name}</div>
          <div className="text-[10px] text-muted font-mono mt-0.5">{conn.api_url}</div>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <label className="text-[10px] text-muted uppercase tracking-wide">
          {t("settings.game_ai_select_model")}
        </label>

        {loadingModels && (
          <p className="text-xs text-muted py-3 text-center">{t("ai.loading_models")}</p>
        )}

        {probeError && (
          <p className="text-xs text-err py-2">{probeError}</p>
        )}

        {!loadingModels && !probeError && availableModels.length > 0 && (
          <>
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="text"
                value={modelQuery}
                onChange={(e) => onModelQueryChange(e.target.value)}
                placeholder={t("connections.search_models", { defaultValue: "Search models…" })}
                className="w-full bg-surface text-foreground border border-border rounded-md pl-7 pr-2.5 py-1.5 text-xs outline-none focus:border-accent-dim"
              />
            </div>

            <div className="flex flex-col gap-1 max-h-56 overflow-y-auto stage-scroll">
              {filteredModels.map((m) => {
                const isSelected = selectedModel === m;
                return (
                  <button
                    key={m}
                    onClick={() => onModelQueryChange(m)}
                    className={`flex items-center gap-2 px-2.5 py-2 rounded-md border text-left transition-colors ${
                      isSelected
                        ? "border-accent/40 bg-accent/10"
                        : "border-border bg-surface hover:border-accent/30"
                    }`}
                  >
                    <div className={`w-3.5 h-3.5 rounded-full border-2 shrink-0 flex items-center justify-center ${
                      isSelected ? "border-accent" : "border-muted"
                    }`}>
                      {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-accent" />}
                    </div>
                    <span className="text-[11px] font-mono text-foreground truncate">{m}</span>
                  </button>
                );
              })}
              {filteredModels.length === 0 && (
                <p className="text-[10px] text-muted/60 text-center py-3">
                  {t("connections.no_models_match")}
                </p>
              )}
            </div>
          </>
        )}

        {!loadingModels && !probeError && availableModels.length === 0 && (
          <p className="text-xs text-muted py-2">{t("connections.test_ok_no_models")}</p>
        )}
      </div>

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
        <button
          onClick={onBack}
          className="px-3 py-1.5 rounded-md text-xs text-muted hover:text-foreground hover:bg-white/5 transition-colors"
        >
          {t("connections.cancel")}
        </button>
        <button
          onClick={onConfirm}
          disabled={!selectedModel || loadingModels}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-accent bg-accent/15 text-accent text-xs font-medium hover:bg-accent/25 transition-colors disabled:opacity-50"
        >
          {t("settings.game_ai_confirm")}
        </button>
      </div>
    </div>
  );
}
