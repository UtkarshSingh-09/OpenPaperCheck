import Link from 'next/link';
import { ReferenceBreakdown } from '@/types/api';
import { formatTiming, formatDate } from '@/lib/formatters';
import CopyButton from './CopyButton';
import {
  ListChecks,
  AlertTriangle,
  ShieldCheck,
  CheckCircle,
  HelpCircle,
  Clock,
} from 'lucide-react';

interface ReferenceAuditCardProps {
  references: ReferenceBreakdown;
  targetDoi?: string;
}

export default function ReferenceAuditCard({ references }: ReferenceAuditCardProps) {
  const hasRetracted = references.retracted && references.retracted.length > 0;
  const isDepositRestricted =
    references.deposit_status === 'restricted' || references.deposit_status === 'missing';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <ListChecks className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <span>Reference List Integrity Audit</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Evaluates whether cited literature contains retracted works using Crossref citation graphs
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Deposit status:</span>
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              isDepositRestricted
                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
            }`}
          >
            {references.deposit_status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* 3-Tier Metrics Grid */}
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Listed</span>
          <p className="mt-1 font-serif text-2xl font-bold text-slate-900 dark:text-slate-100">
            {references.total}
          </p>
          <span className="text-[11px] text-slate-400">Publisher citation count</span>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <CheckCircle className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
            <span>Checked (With DOI)</span>
          </span>
          <p className="mt-1 font-serif text-2xl font-bold text-slate-900 dark:text-slate-100">
            {references.with_doi}
          </p>
          <span className="text-[11px] text-slate-400">Verified against snapshot</span>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <HelpCircle className="h-3 w-3 text-amber-500" />
            <span>Unchecked (No DOI)</span>
          </span>
          <p className="mt-1 font-serif text-2xl font-bold text-slate-900 dark:text-slate-100">
            {references.without_doi}
          </p>
          <span className="text-[11px] text-slate-400">Unstructured references</span>
        </div>

        <div
          className={`rounded-xl border p-3.5 ${
            hasRetracted
              ? 'border-rose-300 bg-rose-50/60 text-rose-900 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200'
              : 'border-emerald-300 bg-emerald-50/60 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200'
          }`}
        >
          <span className="text-xs font-medium flex items-center gap-1">
            {hasRetracted ? (
              <AlertTriangle className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
            ) : (
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            )}
            <span>Retracted Citations</span>
          </span>
          <p className="mt-1 font-serif text-2xl font-bold">
            {references.retracted.length}
          </p>
          <span className="text-[11px] opacity-80">
            {hasRetracted ? 'Flagged references' : 'No citations flagged'}
          </span>
        </div>
      </div>

      {/* Deposit Status Notice if Restricted */}
      {isDepositRestricted && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
          <p className="font-semibold">Notice on Citation Data Availability:</p>
          <p className="mt-1">
            The publisher for this paper has restricted or not deposited an open reference list with Crossref.
            OpenPaperCheck explicitly reports this restriction rather than fabricating a false negative.
          </p>
        </div>
      )}

      {/* Retracted References Table */}
      {hasRetracted ? (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
            <span>Identified Retracted References ({references.retracted.length})</span>
          </h4>

          <div className="mt-3 overflow-hidden rounded-xl border border-rose-200 dark:border-rose-900/60">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-rose-50/80 text-xs font-semibold text-rose-950 dark:bg-rose-950/60 dark:text-rose-200">
                  <tr>
                    <th scope="col" className="px-4 py-3">#</th>
                    <th scope="col" className="px-4 py-3">Cited Paper DOI</th>
                    <th scope="col" className="px-4 py-3">Notice Nature</th>
                    <th scope="col" className="px-4 py-3">Notice Date</th>
                    <th scope="col" className="px-4 py-3">Citation Timing</th>
                    <th scope="col" className="px-4 py-3">Reasons &amp; Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rose-100 bg-white dark:divide-rose-900/30 dark:bg-slate-900">
                  {references.retracted.map((ref, idx) => {
                    const timing = formatTiming(ref.timing);
                    return (
                      <tr key={idx} className="hover:bg-rose-50/40 dark:hover:bg-rose-950/20">
                        <td className="px-4 py-3 font-mono text-xs text-slate-500">
                          {ref.position !== null && ref.position !== undefined
                            ? ref.position
                            : idx + 1}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Link
                              href={`/paper/${ref.doi}`}
                              className="font-mono text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                              title="Audit this cited paper directly"
                            >
                              {ref.doi}
                            </Link>
                            <CopyButton text={ref.doi} />
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                            {ref.nature || 'Retraction'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                          {formatDate(ref.retraction_date)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs ${timing.badgeClass}`}
                          >
                            <Clock className="h-3 w-3" />
                            <span>{timing.label}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {ref.rw_record_id && (
                            <div className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                              RW Record #{ref.rw_record_id}
                            </div>
                          )}
                          {ref.reasons && ref.reasons.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {ref.reasons.map((r, rIdx) => (
                                <span
                                  key={rIdx}
                                  className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                                >
                                  {r}
                                </span>
                              ))}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>
            {references.with_doi > 0
              ? `All ${references.with_doi} references with persistent DOIs were checked; none match indexed retraction notices.`
              : 'No references with persistent DOIs were available to evaluate against retraction databases.'}
          </span>
        </div>
      )}
    </div>
  );
}
