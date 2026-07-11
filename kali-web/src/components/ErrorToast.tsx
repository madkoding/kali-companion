import {
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Clock,
  Search,
  ShieldOff,
  ServerCrash,
  WifiOff,
  Wrench,
  Settings as SettingsIcon,
  HelpCircle,
  X,
  RefreshCw,
  Copy,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { useState } from "react";
import type { ErrorCategory } from "../lib/errorSanitize";

export interface ToastError {
  code: string;
  category: ErrorCategory;
  i18n_key: string;
  params?: Record<string, string>;
  detail: string;
  retryable: boolean;
  correlation_id: string;
}

interface Props {
  error: ToastError;
  onDismiss: () => void;
  onRetry?: () => void;
  onOpenSettings?: () => void;
}

const ICON: Record<ErrorCategory, React.ComponentType<{ className?: string }>> = {
  auth: AlertOctagon,
  billing: AlertCircle,
  rate_limit: Clock,
  not_found: Search,
  bad_request: AlertTriangle,
  content_filter: ShieldOff,
  server: ServerCrash,
  network: WifiOff,
  tool: Wrench,
  config: SettingsIcon,
  internal: HelpCircle,
};

const COLORS: Record<ErrorCategory, string> = {
  auth: "bg-red-900/80 border-red-500/60 text-red-50",
  billing: "bg-red-900/80 border-red-500/60 text-red-50",
  rate_limit: "bg-amber-900/80 border-amber-500/60 text-amber-50",
  not_found: "bg-amber-900/80 border-amber-500/60 text-amber-50",
  bad_request: "bg-amber-900/80 border-amber-500/60 text-amber-50",
  content_filter: "bg-amber-900/80 border-amber-500/60 text-amber-50",
  server: "bg-red-900/80 border-red-500/60 text-red-50",
  network: "bg-slate-900/80 border-slate-500/60 text-slate-50",
  tool: "bg-slate-900/80 border-slate-500/60 text-slate-50",
  config: "bg-amber-900/80 border-amber-500/60 text-amber-50",
  internal: "bg-slate-900/80 border-slate-500/60 text-slate-50",
};

const SHOW_OPEN_SETTINGS: ReadonlySet<ErrorCategory> = new Set([
  "auth",
  "billing",
  "config",
]);

export function ErrorToast({ error, onDismiss, onRetry, onOpenSettings }: Props) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const Icon = ICON[error.category] ?? HelpCircle;
  const colorClass = COLORS[error.category] ?? COLORS.internal;
  const showOpenSettings = SHOW_OPEN_SETTINGS.has(error.category);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        `Code: ${error.code}\nCategory: ${error.category}\n` +
          `i18n_key: ${error.i18n_key}\nDetail: ${error.detail}\n` +
          `Correlation: ${error.correlation_id}`,
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard API not available, fall through
    }
  };

  return (
    <motion.div
      role="alert"
      aria-live="polite"
      className={`fixed top-20 left-1/2 -translate-x-1/2 z-50
                  max-w-[min(560px,90vw)] border rounded-lg shadow-lg
                  backdrop-blur-sm ${colorClass} px-4 py-3`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">
            {t(`error.title.${error.category}`, { code: error.code })}
          </p>
          <p className="text-xs mt-1 opacity-80 whitespace-pre-wrap">
            {t(error.i18n_key, error.params as Record<string, string>)}
          </p>
        </div>
        <button
          onClick={onDismiss}
          aria-label={t("error.action.dismiss")}
          className="opacity-60 hover:opacity-100 flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mt-2 pl-8">
        {error.retryable && onRetry && (
          <button
            onClick={onRetry}
            className="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20
                       inline-flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            {t("error.action.retry")}
          </button>
        )}
        {showOpenSettings && onOpenSettings && (
          <button
            onClick={onOpenSettings}
            className="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20
                       inline-flex items-center gap-1"
          >
            <SettingsIcon className="w-3 h-3" />
            {t("error.action.open_settings")}
          </button>
        )}
        <button
          onClick={handleCopy}
          className="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20
                     inline-flex items-center gap-1"
        >
          <Copy className="w-3 h-3" />
          {copied ? t("error.action.copied") : t("error.action.copy")}
        </button>
      </div>
    </motion.div>
  );
}
