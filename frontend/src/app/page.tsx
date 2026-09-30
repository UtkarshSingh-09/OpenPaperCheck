import DoiSearchBox from '@/components/DoiSearchBox';
import {
  ShieldAlert,
  ListChecks,
  Scale,
  Terminal,
  Database,
} from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero Section */}
      <section className="w-full bg-linear-to-b from-indigo-50/50 via-white to-slate-50 py-16 sm:py-24 px-4 sm:px-6 lg:px-8 border-b border-slate-200/80 dark:from-slate-900 dark:via-slate-950 dark:to-slate-950 dark:border-slate-800">
        <div className="mx-auto max-w-4xl text-center flex flex-col items-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/80 px-3.5 py-1 text-xs font-semibold text-indigo-700 shadow-2xs dark:border-indigo-900/60 dark:bg-indigo-950/60 dark:text-indigo-300">
            <span className="flex h-2 w-2 rounded-full bg-indigo-600 animate-pulse" />
            <span>Open Scholarly Integrity Infrastructure</span>
          </div>

          {/* Heading */}
          <h1 className="mt-6 font-serif text-3xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-slate-50 leading-[1.15]">
            Verify Retractions &amp; Citing Integrity{' '}
            <span className="text-indigo-600 dark:text-indigo-400">in Seconds</span>
          </h1>

          {/* Subheading */}
          <p className="mt-4 max-w-2xl text-base text-slate-600 sm:text-lg dark:text-slate-300 leading-relaxed">
            Audit any scholarly paper by DOI. Instant, sourced facts on whether a paper
            has been retracted or leans on retracted citations — with zero subjective accusations.
          </p>

          {/* Search Box */}
          <div className="mt-8 sm:mt-10 w-full flex justify-center">
            <DoiSearchBox size="large" autoFocus />
          </div>
        </div>
      </section>

      {/* Core Principles (Ethical & Technical Architecture) */}
      <section className="w-full max-w-7xl py-16 px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="font-serif text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">
            Built on Rigorous Academic Standards
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Designed specifically for researchers, librarians, peer reviewers, and editors who demand verifiable facts.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Principle 1 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-slate-100">
                Retraction Notices
              </h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Direct matching against Retraction Watch database records. Retractions, Expressions of Concern, and notices sourced verbatim.
              </p>
            </div>
            <div className="mt-4 text-xs font-mono font-medium text-rose-600 dark:text-rose-400">
              Signals S-001 &bull; S-002 &bull; S-003
            </div>
          </div>

          {/* Principle 2 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
                <ListChecks className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-slate-100">
                3-Tier Reference Honesty
              </h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Separates checked DOIs, unchecked unstructured citations, and restricted publisher lists. Never creates a false sense of security.
              </p>
            </div>
            <div className="mt-4 text-xs font-mono font-medium text-amber-600 dark:text-amber-400">
              Signal S-010 &bull; S-040
            </div>
          </div>

          {/* Principle 3 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
                <Scale className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-slate-100">
                Zero Personal Accusations
              </h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Strict adherence to ethical guidelines. Zero demographic or author features. Banned words list strictly enforced in all outputs.
              </p>
            </div>
            <div className="mt-4 text-xs font-mono font-medium text-indigo-600 dark:text-indigo-400">
              Ethical Standard (ETHICS.md)
            </div>
          </div>

          {/* Principle 4 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-slate-100">
                Open &amp; Verifiable
              </h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Every statement links to external authorities (Crossref, Retraction Watch, PubPeer). Fast REST API and PyPI CLI tool.
              </p>
            </div>
            <div className="mt-4 text-xs font-mono font-medium text-emerald-600 dark:text-emerald-400">
              CC-BY 4.0 &bull; Apache-2.0
            </div>
          </div>
        </div>
      </section>

      {/* Terminal CLI Banner */}
      <section className="w-full max-w-7xl px-4 sm:px-6 lg:px-8 pb-16">
        <div className="rounded-3xl bg-slate-900 p-8 sm:p-10 text-white shadow-xl dark:bg-slate-900/90 border border-slate-800">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
            <div className="max-w-xl">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                <Terminal className="h-4 w-4" />
                <span>Command Line Tool Available on PyPI</span>
              </div>
              <h3 className="mt-3 font-serif text-2xl font-bold sm:text-3xl text-slate-50">
                Audit literature right from your terminal or CI pipeline
              </h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Check papers offline in milliseconds. Automatically downloads the verified Retraction Watch snapshot and works with any research workflow.
              </p>
            </div>

            <div className="rounded-2xl bg-black/60 p-4 border border-slate-700/80 font-mono text-xs sm:text-sm text-slate-200">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-500 text-xs">
                <span>Terminal / Bash</span>
                <span className="text-emerald-400">● live on PyPI</span>
              </div>
              <pre className="pt-3 overflow-x-auto space-y-1.5">
                <span className="text-slate-500"># Install from PyPI</span>
                <br />
                <span className="text-emerald-400">$</span> pip install openpapercheck
                <br />
                <br />
                <span className="text-slate-500"># Check any paper by DOI</span>
                <br />
                <span className="text-emerald-400">$</span> opc check 10.1016/s0140-6736(97)11096-0
              </pre>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
