import { Signal } from '@/types/api';
import { FileSearch, ExternalLink } from 'lucide-react';
import { formatDate } from '@/lib/formatters';

interface FactsListProps {
  signals: Signal[];
}

export default function FactsList({ signals }: FactsListProps) {
  if (!signals || signals.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
          Deterministic Signals &amp; Evidence
        </h3>
        <p className="mt-2 text-sm text-slate-500">No signals triggered for this paper.</p>
      </div>
    );
  }

  const getSignalBadgeColor = (id: string, value: unknown) => {
    if (id === 'S-001' && value === true) {
      return 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-800';
    }
    if ((id === 'S-002' || id === 'S-010') && (value === true || (typeof value === 'number' && value > 0))) {
      return 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800';
    }
    if (id === 'S-040') {
      return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
    return 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800';
  };

  const renderSignalValue = (val: unknown): string => {
    if (typeof val === 'boolean') return val ? 'true' : 'false';
    if (typeof val === 'number') return String(val);
    if (typeof val === 'string') return val;
    if (typeof val === 'object' && val !== null) {
      const obj = val as Record<string, unknown>;
      if (typeof obj.deposit_status === 'string') return obj.deposit_status;
      return 'evaluated';
    }
    return String(val);
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <span>Sourced Integrity Signals</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Transparent deterministic rules based on verified authoritative records
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {signals.length} {signals.length === 1 ? 'signal' : 'signals'} evaluated
        </span>
      </div>

      <div className="mt-4 space-y-4">
        {signals.map((signal) => {
          const badgeClass = getSignalBadgeColor(signal.id, signal.value);
          const hasEvidence = signal.evidence && signal.evidence.length > 0;

          return (
            <div
              key={signal.id}
              className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950/40"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-xs font-bold ${badgeClass}`}
                  >
                    {signal.id}
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                    {signal.name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-mono">
                    {signal.category}
                  </span>
                  <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-300 bg-slate-200/80 dark:bg-slate-800 px-2 py-0.5 rounded">
                    {renderSignalValue(signal.value)}
                  </span>
                </div>
              </div>

              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {signal.description}
              </p>

              {/* Evidence details */}
              {hasEvidence && (
                <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-xs dark:border-slate-800 dark:bg-slate-900">
                  <div className="font-semibold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1">
                    <span>Indexed Evidence Details:</span>
                  </div>
                  {signal.evidence.map((ev, idx) => {
                    const recordId = ev.rw_record_id || ev.record_id;
                    const nature = ev.nature || ev.retraction_nature;
                    const date = ev.retraction_date || ev.date;
                    const reasons = ev.reasons;

                    return (
                      <div key={idx} className="mt-1.5 space-y-1.5 border-t border-slate-100 pt-2 first:border-0 first:pt-0 dark:border-slate-800">
                        {recordId && (
                          <div className="flex items-center gap-2">
                            <span className="text-slate-500">Retraction Watch Record:</span>
                            <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                              #{recordId}
                            </span>
                            <a
                              href="https://retractionwatch.com/"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-0.5 text-indigo-600 hover:underline dark:text-indigo-400"
                            >
                              <span>Database</span>
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        )}

                        {nature && (
                          <div>
                            <span className="text-slate-500">Notice Nature: </span>
                            <span className="font-medium text-slate-800 dark:text-slate-200">
                              {nature}
                            </span>
                          </div>
                        )}

                        {date && (
                          <div>
                            <span className="text-slate-500">Notice Date: </span>
                            <span className="font-medium text-slate-800 dark:text-slate-200">
                              {formatDate(date)}
                            </span>
                          </div>
                        )}

                        {reasons && Array.isArray(reasons) && reasons.length > 0 && (
                          <div>
                            <span className="text-slate-500">Verbatim Notice Reasons:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {reasons.map((r: string, rIdx: number) => (
                                <span
                                  key={rIdx}
                                  className="rounded bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-800 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-900"
                                >
                                  {r}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {ev.provider && (
                          <div className="text-slate-500">
                            Provider: <span className="font-mono text-slate-700 dark:text-slate-300">{ev.provider}</span> ({ev.deposit_status || 'ok'})
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
