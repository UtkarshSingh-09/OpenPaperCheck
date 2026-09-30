import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { fetchPaperCheck, ApiError } from '@/lib/api';
import { cleanDoi } from '@/lib/doi';
import { CheckResponse, ProblemDetail } from '@/types/api';
import StateBanner from '@/components/StateBanner';
import PaperHeader from '@/components/PaperHeader';
import FactsList from '@/components/FactsList';
import ReferenceAuditCard from '@/components/ReferenceAuditCard';
import ProvenanceCard from '@/components/ProvenanceCard';
import DoiSearchBox from '@/components/DoiSearchBox';
import { AlertCircle, ArrowLeft, ExternalLink } from 'lucide-react';

interface PageProps {
  params: Promise<{
    doi: string[];
  }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const rawDoi = resolvedParams.doi ? resolvedParams.doi.join('/') : '';
  const cleaned = cleanDoi(rawDoi);

  return {
    title: `Audit: ${cleaned} — OpenPaperCheck`,
    description: `Scholarly retraction and reference audit for paper DOI ${cleaned}.`,
  };
}

export default async function PaperReportPage({ params }: PageProps) {
  const resolvedParams = await params;
  const rawDoi = resolvedParams.doi ? resolvedParams.doi.join('/') : '';
  const cleaned = cleanDoi(rawDoi);

  if (!cleaned) {
    notFound();
  }

  let report: CheckResponse | null = null;
  let errorDetail: { status: number; message: string; problem?: ProblemDetail } | null = null;

  try {
    report = await fetchPaperCheck(cleaned);
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      errorDetail = {
        status: err.status,
        message: err.message,
        problem: err.problem,
      };
    } else {
      const msg = err instanceof Error ? err.message : 'Unable to connect to OpenPaperCheck API backend.';
      errorDetail = {
        status: 500,
        message: msg,
      };
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Navigation & Search Bar */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/80 pb-6 dark:border-slate-800">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Search</span>
        </Link>

        <div className="w-full sm:max-w-md">
          <DoiSearchBox size="default" initialValue={cleaned} />
        </div>
      </div>

      {/* Error state */}
      {errorDetail ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/60 p-6 sm:p-8 dark:border-rose-900/60 dark:bg-rose-950/30">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-6 w-6 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-mono text-xs font-semibold text-rose-700 dark:text-rose-300">
                HTTP {errorDetail.status} &bull; {errorDetail.problem?.title || 'Notice'}
              </span>
              <h2 className="mt-1 text-xl font-bold text-rose-950 dark:text-rose-100">
                Unable to audit DOI: <span className="font-mono">{cleaned}</span>
              </h2>
              <p className="mt-2 text-sm text-rose-900 dark:text-rose-200 leading-relaxed">
                {errorDetail.message}
              </p>

              {errorDetail.status === 404 && (
                <div className="mt-4 rounded-xl border border-rose-200 bg-white p-4 text-xs text-slate-700 dark:border-rose-900 dark:bg-slate-900 dark:text-slate-300">
                  <p className="font-semibold text-slate-900 dark:text-slate-100">
                    Why might a DOI not be found?
                  </p>
                  <ul className="mt-1.5 list-disc pl-4 space-y-1">
                    <li>The paper might not be registered with Crossref or DataCite.</li>
                    <li>The DOI might have a typo (check hyphens, slashes, or prefixes).</li>
                    <li>Preprint servers like arXiv or bioRxiv might use different identifiers.</li>
                  </ul>
                </div>
              )}

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/"
                  className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-rose-700"
                >
                  Try Benchmark Examples
                </Link>
                <a
                  href={`https://doi.org/${cleaned}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-xl border border-rose-300 bg-white px-4 py-2 text-xs font-medium text-rose-900 hover:bg-rose-50 dark:border-rose-800 dark:bg-slate-900 dark:text-rose-200"
                >
                  <span>Resolve at doi.org</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : report ? (
        <div className="space-y-6">
          {/* 1. Public State Banner */}
          <StateBanner state={report.state} headline={report.headline} />

          {/* 2. Paper Bibliographic Metadata */}
          <PaperHeader
            paper={report.paper}
            pubpeerUrl={report.external_links?.pubpeer}
          />

          {/* 3. Sourced Facts & Deterministic Signals */}
          <FactsList signals={report.signals} />

          {/* 4. 3-Tier Reference Breakdown & Retracted References */}
          <ReferenceAuditCard
            references={report.references}
            targetDoi={report.doi}
          />

          {/* 5. Provenance & Source Freshness */}
          <ProvenanceCard
            coverage={report.coverage}
            dataAsOf={report.data_as_of}
            disclaimer={report.disclaimer}
          />
        </div>
      ) : null}
    </div>
  );
}
