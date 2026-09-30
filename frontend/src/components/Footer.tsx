import Link from 'next/link';
import { ShieldCheck, Info } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-50 py-12 dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand & Mission */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-serif text-base font-bold text-slate-900 dark:text-slate-100">
                OpenPaperCheck
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Open scholarly retraction and reference integrity infrastructure. Verifies whether papers
              are retracted or lean on retracted literature using transparent, public authorities.
            </p>
            <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/80 p-3 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
              <Info className="h-4 w-4 shrink-0 text-amber-700 dark:text-amber-400 mt-0.5" />
              <p>
                <strong>Ethical Standard:</strong> Absence of a flag is NOT an endorsement.
                We report only verifiable historical notices. We do not use banned subjective words
                nor assess author reputations or personal attributes.
              </p>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200">
              Transparency
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>
                <Link href="/sources" className="hover:text-indigo-600 dark:hover:text-indigo-400">
                  Data Sources &amp; Freshness
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-indigo-600 dark:hover:text-indigo-400">
                  Ethics Charter &amp; Banned Words
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com/UtkarshSingh-09/OpenPaperCheck/blob/main/docs/SIGNALS_AND_ML.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  Deterministic Signals (S-001 to S-040)
                </a>
              </li>
              <li>
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  Interactive REST API (Swagger)
                </a>
              </li>
            </ul>
          </div>

          {/* Authorities & Open Source */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200">
              Data &amp; License
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>
                <a
                  href="https://retractionwatch.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  Retraction Watch Database (CC-BY 4.0)
                </a>
              </li>
              <li>
                <a
                  href="https://www.crossref.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  Crossref Metadata API
                </a>
              </li>
              <li>
                <a
                  href="https://pubpeer.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  PubPeer Foundation
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/UtkarshSingh-09/OpenPaperCheck"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  Open Source (Apache-2.0)
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-slate-200 pt-6 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-500">
          <p>
            OpenPaperCheck &bull; Built with FastAPI and Next.js &bull; Data licensed under CC-BY 4.0 &bull; Code under Apache 2.0
          </p>
        </div>
      </div>
    </footer>
  );
}
