import { Metadata } from 'next';
import { fetchSources, fetchHealth } from '@/lib/api';
import { Database, ShieldCheck } from 'lucide-react';
import { formatDate } from '@/lib/formatters';

export const metadata: Metadata = {
  title: 'Data Sources & Freshness — OpenPaperCheck',
  description:
    'Transparency documentation: authoritative scholarly data sources, snapshot freshness, and licenses used by OpenPaperCheck.',
};

export default async function SourcesPage() {
  let sourcesData = null;
  let healthData = null;

  try {
    [sourcesData, healthData] = await Promise.all([
      fetchSources().catch(() => null),
      fetchHealth().catch(() => null),
    ]);
  } catch {
    // Graceful fallback
  }

  const sources = sourcesData?.sources || [
    {
      name: 'retraction_watch',
      authority: 'Retraction Watch Database (The Center for Scientific Integrity)',
      license: 'CC-BY 4.0',
      records_count: healthData?.records_count || 60000,
      as_of_date: healthData?.as_of || '2026-09-29',
      description:
        'Comprehensive database of scholarly retractions, expressions of concern, and corrections across scientific disciplines.',
    },
    {
      name: 'crossref',
      authority: 'Crossref (Publishers International Linking Association)',
      license: 'Public Metadata / Open DOI Registry',
      records_count: null,
      as_of_date: 'Live Upstream API',
      description:
        'Official DOI registry providing bibliographic metadata, publisher relations, and deposited reference lists.',
    },
  ];

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-8 dark:border-slate-800">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          <Database className="h-4 w-4" />
          <span>Complete Provenance</span>
        </div>
        <h1 className="mt-2 font-serif text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-4xl">
          Scholarly Data Sources &amp; Transparency
        </h1>
        <p className="mt-3 text-base text-slate-600 dark:text-slate-400 leading-relaxed">
          OpenPaperCheck adheres to strict reproducibility and provenance standards. Every claim
          links back to an official record from an authoritative scholarly metadata provider.
        </p>
      </div>

      {/* Snapshot Health Status */}
      {healthData && (
        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 dark:border-emerald-900/60 dark:bg-emerald-950/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-emerald-900 dark:text-emerald-200 text-sm">
                Service Status: {healthData.status.toUpperCase()} &bull; v{healthData.version}
              </span>
            </div>
            {healthData.is_sample && (
              <span className="rounded-md border border-amber-300 bg-amber-100 px-2 py-0.5 font-mono text-xs font-bold text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
                SAMPLE SNAPSHOT MODE
              </span>
            )}
          </div>
          <p className="mt-2 text-xs text-emerald-800 dark:text-emerald-300">
            Database snapshot healthy. Records indexed:{' '}
            <strong>{healthData.records_count?.toLocaleString() || 'N/A'}</strong> &bull; Snapshot as of:{' '}
            <strong>{formatDate(healthData.as_of)}</strong>.
          </p>
        </div>
      )}

      {/* Sources List */}
      <div className="mt-8 space-y-6">
        {sources.map((src) => (
          <div
            key={src.name}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 dark:border-slate-800">
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 capitalize">
                {src.authority}
              </h2>
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                License: {src.license}
              </span>
            </div>

            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {src.description}
            </p>

            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950">
                <span className="text-slate-500">Records Count:</span>
                <p className="mt-0.5 font-mono font-bold text-slate-800 dark:text-slate-200">
                  {src.records_count ? src.records_count.toLocaleString() : 'Live dynamic index'}
                </p>
              </div>

              <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950">
                <span className="text-slate-500">Freshness Date:</span>
                <p className="mt-0.5 font-medium text-slate-800 dark:text-slate-200">
                  {formatDate(src.as_of_date)}
                </p>
              </div>

              <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950 col-span-2 sm:col-span-1">
                <span className="text-slate-500">Upstream Authority:</span>
                <p className="mt-0.5 font-medium text-slate-800 dark:text-slate-200">
                  Verified Scholarly Body
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Ethics Disclaimer */}
      <div className="mt-10 rounded-2xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
          <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          <span>Ethical Disclaimer</span>
        </h3>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          OpenPaperCheck strictly reports historical, verifiable facts from indexed scholarly notices.
          It does not generate subjective claims, personal accusations, or predict scientific truth.
          Absence of a flag is not an endorsement.
        </p>
      </div>
    </div>
  );
}
