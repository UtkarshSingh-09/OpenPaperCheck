'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Clipboard, X, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';
import { cleanDoi, isValidDoi, SAMPLE_DOIS } from '@/lib/doi';

interface DoiSearchBoxProps {
  initialValue?: string;
  autoFocus?: boolean;
  size?: 'default' | 'large';
}

export default function DoiSearchBox({
  initialValue = '',
  autoFocus = false,
  size = 'large',
}: DoiSearchBoxProps) {
  const router = useRouter();
  const [input, setInput] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const cleaned = cleanDoi(input);
    if (!cleaned) {
      setError('Please enter a DOI or paper link (e.g. 10.1038/nature12373)');
      return;
    }

    if (!isValidDoi(cleaned)) {
      setError(`"${cleaned}" does not match standard scholarly DOI syntax (10.NNNN/...)`);
      return;
    }

    setIsLoading(true);
    // Route to /paper/[...doi]
    router.push(`/paper/${cleaned}`);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInput(text);
        setError(null);
      }
    } catch {
      // Clipboard access denied
    }
  };

  const handleSampleClick = (doi: string) => {
    setInput(doi);
    setError(null);
    setIsLoading(true);
    router.push(`/paper/${doi}`);
  };

  const isLarge = size === 'large';

  return (
    <div className="w-full max-w-3xl">
      <form onSubmit={handleSubmit} className="relative">
        <div
          className={`flex items-center rounded-2xl border bg-white shadow-lg transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 dark:bg-slate-900 ${
            error
              ? 'border-rose-400 ring-2 ring-rose-500/20'
              : 'border-slate-300 dark:border-slate-700'
          } ${isLarge ? 'p-2 sm:p-2.5' : 'p-1.5'}`}
        >
          {/* Search Icon */}
          <div className="flex h-11 w-11 shrink-0 items-center justify-center text-slate-400">
            <Search className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          </div>

          {/* Input field */}
          <input
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (error) setError(null);
            }}
            placeholder="Paste DOI or link: 10.1016/s0140-6736(97)11096-0 or https://doi.org/..."
            autoFocus={autoFocus}
            className="flex-1 bg-transparent px-2 text-slate-900 outline-hidden placeholder:text-slate-400 dark:text-slate-100 sm:text-base text-sm font-mono tracking-tight"
          />

          {/* Actions inside bar */}
          <div className="flex items-center gap-1.5 pr-1">
            {input ? (
              <button
                type="button"
                onClick={() => setInput('')}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                title="Clear input"
              >
                <X className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePaste}
                className="hidden items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800 sm:flex"
                title="Paste from clipboard"
              >
                <Clipboard className="h-3 w-3" />
                <span>Paste</span>
              </button>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  <span>Audit Paper</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-2.5 flex items-center gap-2 text-xs text-rose-600 dark:text-rose-400">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Sample pills */}
      <div className="mt-4">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
          <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          <span>Try verified benchmark examples:</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {SAMPLE_DOIS.map((s) => (
            <button
              key={s.doi}
              type="button"
              onClick={() => handleSampleClick(s.doi)}
              className="group flex items-center gap-2 rounded-lg border border-slate-200 bg-white/80 px-2.5 py-1.5 text-left text-xs transition-all hover:border-indigo-300 hover:bg-indigo-50/50 dark:border-slate-800 dark:bg-slate-900/80 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/30"
            >
              <span
                className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-wider border ${s.badgeColor}`}
              >
                {s.tag}
              </span>
              <span className="font-medium text-slate-700 dark:text-slate-300 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                {s.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
