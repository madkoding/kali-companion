import { useTranslation } from "react-i18next";
import { Heart } from "lucide-react";

export function AboutSection() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-1 h-5 bg-accent rounded-full" />
        <h2 className="text-sm font-bold m-0">{t("about.title")}</h2>
      </div>

      {/* App info */}
      <div className="bg-white/5 p-5 rounded-2xl border border-white/10 space-y-4">
        <Row label={t("about.author")} value={t("about.author_name")} />
        <Row label={t("about.version")} value="0.1.0" />
      </div>

      {/* Engine */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1 h-4 bg-accent rounded-full" />
          <h3 className="text-xs font-bold uppercase tracking-wider m-0">{t("about.engine_label")}</h3>
        </div>
        <div className="bg-white/5 p-4 rounded-2xl border border-white/10 space-y-3">
          <p className="text-xs text-muted leading-relaxed">
            {t("about.engine_desc")}
          </p>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted">{t("about.engine_repo")}:</span>
            <a
              href="https://github.com/ServeurpersoCom/qwentts.cpp"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline font-mono truncate"
            >
              github.com/ServeurpersoCom/qwentts.cpp
            </a>
          </div>
        </div>
      </div>

      {/* Other Engines */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1 h-4 bg-accent rounded-full" />
          <h3 className="text-xs font-bold uppercase tracking-wider m-0">{t("about.other_engines")}</h3>
        </div>
        <div className="bg-white/5 rounded-2xl border border-white/10 divide-y divide-white/5">
          <EngineRow name="Piper" description={t("about.engine_piper")} />
          <EngineRow name="Vosk" description={t("about.engine_vosk")} />
          <EngineRow name="Qwen3-ASR" description={t("about.engine_qwen3asr")} />
        </div>
      </div>

      {/* Icons attribution */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1 h-4 bg-accent rounded-full" />
          <h3 className="text-xs font-bold uppercase tracking-wider m-0">{t("about.icons")}</h3>
        </div>
        <p className="text-xs text-muted leading-relaxed bg-white/5 p-4 rounded-2xl border border-white/10">
          {t("about.icons_prefix")}{" "}
          <a
            href="https://www.svgrepo.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            SVG Repo
          </a>
          . {t("about.icons_suffix")}
        </p>
      </div>

      {/* Made with love */}
      <div className="flex items-center justify-center gap-1.5 pt-2 text-[10px] text-muted">
        <span>{t("about.made_with")}</span>
        <Heart size={10} className="text-red-400 fill-red-400" />
        <span>{t("about.made_by")}</span>
      </div>
    </div>
  );
}

function EngineRow({ name, description }: { name: string; description: string }) {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <span className="text-xs font-bold text-fg whitespace-nowrap mt-0.5">{name}</span>
      <span className="text-xs text-muted leading-relaxed">{description}</span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-xs font-mono font-bold text-fg">{value}</span>
    </div>
  );
}
