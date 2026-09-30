import { Metadata } from 'next';
import { ShieldCheck, Scale, AlertOctagon, CheckCircle2, HeartHandshake } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Ethics Charter & Principles — OpenPaperCheck',
  description:
    'Ethical principles, banned words standard, zero personal profiling, and 3-tier reference honesty rule of OpenPaperCheck.',
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-8 dark:border-slate-800">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          <Scale className="h-4 w-4" />
          <span>Integrity Standard</span>
        </div>
        <h1 className="mt-2 font-serif text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-4xl">
          Ethics Charter &amp; Core Principles
        </h1>
        <p className="mt-3 text-base text-slate-600 dark:text-slate-400 leading-relaxed">
          OpenPaperCheck is built on the principle that scholarly integrity software must be as rigorous,
          humble, and accountable as the scientific process itself.
        </p>
      </div>

      <div className="mt-8 space-y-10">
        {/* Principle 1: Zero Personal Accusations */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <span>1. Zero Personal Profiling &amp; Accusations</span>
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            OpenPaperCheck audits <strong>papers and citations</strong>, never people. We do not inspect
            or store author demographics, institution rankings, h-indices, nationality, or personal identities.
            No researcher should ever be scored or blacklisted by an algorithm.
          </p>
        </section>

        {/* Principle 2: Banned Words List */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <AlertOctagon className="h-5 w-5 text-rose-600 dark:text-rose-400" />
            <span>2. Strict Banned Words Standard</span>
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            Scholarly communication requires objectivity. OpenPaperCheck strictly bans emotive and subjective
            labels in all API payloads, UI text, and documentation. The following words are permanently banned
            and enforced by automated unit tests:
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            {['fake', 'fraud', 'fraudulent', 'scam', 'cheat', 'guilty', 'criminal', 'shady', 'predatory'].map(
              (w) => (
                <span
                  key={w}
                  className="rounded-md border border-rose-300 bg-rose-50 px-2.5 py-1 font-mono text-xs font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-300"
                >
                  &ldquo;{w}&rdquo;
                </span>
              )
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Instead of subjective terms, we report verifiable factual statements: &ldquo;Retracted by publisher notice on YYYY-MM-DD&rdquo;,
            &ldquo;Retraction Watch Record #4036&rdquo;, or &ldquo;Cited 2 retracted references&rdquo;.
          </p>
        </section>

        {/* Principle 3: 3-Tier Honesty */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            <span>3. 3-Tier Reference Honesty Rule</span>
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            In scholarly publishing, reference lists vary greatly in quality and openness. We never fabricate
            false negatives:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-900/60 dark:bg-emerald-950/30">
              <h3 className="font-semibold text-emerald-900 dark:text-emerald-200 text-xs">Tier 1: Checked</h3>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                References with valid persistent DOIs verified against the retraction snapshot.
              </p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-900/60 dark:bg-amber-950/30">
              <h3 className="font-semibold text-amber-900 dark:text-amber-200 text-xs">Tier 2: Unstructured</h3>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                References lacking persistent DOIs are explicitly marked as <em>unchecked</em>.
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-100/50 p-4 dark:border-slate-800 dark:bg-slate-900">
              <h3 className="font-semibold text-slate-900 dark:text-slate-200 text-xs">Tier 3: Restricted</h3>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                When publishers do not deposit references openly, we report this restriction transparently.
              </p>
            </div>
          </div>
        </section>

        {/* Principle 4: Absence of Flag is Not Endorsement */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <HeartHandshake className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <span>4. Absence of a Flag is Not Endorsement</span>
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            A state of <code>NO FLAGS FOUND</code> strictly means that no formal retraction notice or expression
            of concern exists in our snapshot. It is never a proof of scientific correctness, replicability, or
            validity. Peer review and scientific critique remain essential.
          </p>
        </section>
      </div>
    </div>
  );
}
