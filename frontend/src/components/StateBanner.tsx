import { PaperPublicState } from '@/types/api';
import { STATE_CONFIGS } from '@/lib/formatters';
import { ShieldAlert, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';

interface StateBannerProps {
  state: PaperPublicState;
  headline: string;
  className?: string;
}

export default function StateBanner({ state, headline, className = '' }: StateBannerProps) {
  const config = STATE_CONFIGS[state] || STATE_CONFIGS.insufficient_data;

  const renderIcon = () => {
    switch (state) {
      case 'retracted_external':
        return <ShieldAlert className="h-8 w-8 text-rose-600 dark:text-rose-400 shrink-0" />;
      case 'needs_review':
        return <AlertTriangle className="h-8 w-8 text-amber-600 dark:text-amber-400 shrink-0" />;
      case 'no_flags_found':
        return <ShieldCheck className="h-8 w-8 text-emerald-600 dark:text-emerald-400 shrink-0" />;
      case 'insufficient_data':
      default:
        return <HelpCircle className="h-8 w-8 text-slate-500 dark:text-slate-400 shrink-0" />;
    }
  };

  return (
    <div
      className={`rounded-2xl border p-5 sm:p-6 shadow-sm transition-all ${config.cardBorderClass} ${config.bgLightClass} ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="mt-0.5">{renderIcon()}</div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full border px-3 py-1 font-mono text-xs font-bold tracking-wider ${config.badgeClass}`}
              >
                {config.label}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Official Integrity Assessment
              </span>
            </div>
            <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-950 dark:text-slate-50 sm:text-2xl">
              {headline}
            </h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              {config.summaryDescription}
            </p>
          </div>
        </div>
      </div>

      {state === 'no_flags_found' && (
        <div className="mt-4 rounded-xl border border-emerald-200/80 bg-emerald-50/70 p-3 text-xs text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300">
          <strong>Scholarly Note:</strong> Absence of a flag means no formal retraction notices were found
          in our indexed Retraction Watch and Crossref snapshot. It is not an endorsement of scientific validity or methodology.
        </div>
      )}
    </div>
  );
}
