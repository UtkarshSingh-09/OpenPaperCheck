import { CoverageInfo } from '@/types/api';
import { Database, CheckCircle, AlertCircle, Calendar } from 'lucide-react';
import { formatDate } from '@/lib/formatters';

interface ProvenanceCardProps {
  coverage: CoverageInfo;
  dataAsOf: Record<string, string>;
  disclaimer: string;
}

export default function ProvenanceCard({ coverage, dataAsOf, disclaimer }: ProvenanceCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
        <Database className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
        <span>Provenance &amp; Source Freshness</span>
      </h3>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Answered Sources */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Data Sources Answered
          </span>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {coverage.sources_answered.map((s) => (
              <span
                key={s}
                className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-900"
              >
                <CheckCircle className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                <span>{s}</span>
              </span>
            ))}
            {coverage.sources_failed && coverage.sources_failed.length > 0 && (
              coverage.sources_failed.map((s) => (
                <span
                  key={s}
                  className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2 py-1 text-xs font-medium text-rose-800 border border-rose-200 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-900"
                >
                  <AlertCircle className="h-3 w-3 text-rose-600 dark:text-rose-400" />
                  <span>{s} (failed)</span>
                </span>
              ))
            )}
          </div>
        </div>

        {/* Data As Of Dates */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Database Snapshot Freshness
          </span>
          <div className="mt-2 space-y-1 text-xs text-slate-600 dark:text-slate-400">
            {Object.entries(dataAsOf).map(([src, dt]) => (
              <div key={src} className="flex items-center justify-between">
                <span className="capitalize font-mono">{src}:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200 flex items-center gap-1">
                  <Calendar className="h-3 w-3 text-slate-400" />
                  <span>{formatDate(dt)}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mandatory ethical disclaimer */}
      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
        <p>
          <strong>Ethical Disclaimer:</strong> {disclaimer}
        </p>
      </div>
    </div>
  );
}
