import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Star, Search, Pencil } from "lucide-react";
import { Modal } from "../../ui/Modal";
import { testConnection } from "../../../lib/api/connections";
import type { ConnectionSummary } from "../../../lib/protocol";

interface Props {
  conn: ConnectionSummary | null;
  onClose: () => void;
  onActivate: (id: string, model: string) => Promise<void> | void;
}

export function ActivateModal({ conn, onClose, onActivate }: Props) {
  const { t } = useTranslation();
  const [models, setModels] = useState<string[]>([]);
  const [vendor, setVendor] = useState<string>("");
  const [loadingModels, setLoadingModels] = useState(false);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [model, setModel] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!conn) return;
    setModel("");
    setQuery("");
    setProbeError(null);
    setLoadingModels(true);
    void (async () => {
      try {
        const result = await testConnection(conn.api_url, "");
        if (result.ok) {
          setModels(result.models);
          setVendor(result.vendor);
          if (result.models.length > 0) {
            setModel((curr) => curr || result.models[0]);
          }
        } else {
          setProbeError(result.detail || t("connections.test_failed", { reason: "?" }));
        }
      } catch (err) {
        setProbeError((err as Error).message);
      } finally {
        setLoadingModels(false);
      }
    })();
  }, [conn, t]);

  const filteredModels = useMemo(() => {
    if (!query.trim()) return models;
    const q = query.toLowerCase();
    return models.filter((m) => m.toLowerCase().includes(q));
  }, [models, query]);

  if (!conn) return null;

  const handleSubmit = async () => {
    if (!model.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onActivate(conn.id, model.trim());
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const isChangeModel = conn.is_active;

  return (
    <Modal open onClose={onClose} size="md" title={isChangeModel ? t("connections.change_model_title") : t("connections.activate_title")}>
      <div className="flex flex-col gap-4">
        <div className="px-3 py-2.5 rounded-lg bg-surface border border-border">
          <div className="text-xs text-foreground font-medium">{conn.name}</div>
          <div className="text-[10px] text-muted font-mono mt-0.5">{conn.api_url}</div>
        </div>

        {isChangeModel ? (
          <p className="text-[11px] text-muted/80">{t("connections.change_model_subtitle")}</p>
        ) : (
          <p className="text-[11px] text-muted/80">{t("connections.activate_subtitle")}</p>
        )}

        {loadingModels && (
          <p className="text-[11px] text-muted">{t("ai.loading_models")}</p>
        )}

        {probeError && (
          <p className="text-[11px] text-err">{probeError}</p>
        )}

        {!loadingModels && !probeError && models.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("connections.search_models", { defaultValue: "Search models…" })}
                className="w-full bg-surface text-foreground border border-border rounded-md pl-7 pr-2.5 py-1.5 text-xs outline-none focus:border-accent-dim"
              />
            </div>

            <div className="flex flex-col gap-1 max-h-56 overflow-y-auto stage-scroll">
              {filteredModels.map((m) => {
                const selected = model === m;
                return (
                  <button
                    key={m}
                    onClick={() => setModel(m)}
                    className={`flex items-center justify-between gap-2 px-2.5 py-2 rounded-md border text-left transition-colors ${
                      selected
                        ? "border-accent/40 bg-accent/10"
                        : "border-border bg-surface hover:border-accent/30"
                    }`}
                  >
                    <span className="text-[11px] font-mono text-foreground truncate">{m}</span>
                  </button>
                );
              })}
              {filteredModels.length === 0 && (
                <p className="text-[10px] text-muted/60 text-center py-3">
                  {t("provider.no_models_match")}
                </p>
              )}
            </div>

            {vendor && (
              <p className="text-[10px] text-muted/60">
                {t("connections.vendor_detected", { vendor })}
              </p>
            )}
          </div>
        )}

        {!loadingModels && !probeError && models.length === 0 && (
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-muted">{t("ai.model")}</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder={t("ai.model_placeholder") as string}
              className="bg-surface text-foreground border border-border rounded-md px-2.5 py-2 text-sm outline-none focus:border-accent-dim"
            />
            <p className="text-[10px] text-muted/60">
              {t("connections.test_ok_no_models")}
            </p>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-md text-xs text-muted hover:text-foreground hover:bg-white/5 transition-colors"
          >
            {t("connections.cancel")}
          </button>
          <button
            onClick={handleSubmit}
            disabled={!model.trim() || submitting || loadingModels}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-accent bg-accent/15 text-accent text-xs font-medium hover:bg-accent/25 transition-colors disabled:opacity-50"
          >
            {isChangeModel ? <Pencil size={12} /> : <Star size={12} />}
            {isChangeModel ? t("connections.change_model_btn") : t("connections.set_active")}
          </button>
        </div>
      </div>
    </Modal>
  );
}
