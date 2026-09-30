import { PaperMetadata } from '@/types/api';
import CopyButton from './CopyButton';
import { ExternalLink, Calendar, Building2, BookOpen, MessageSquare } from 'lucide-react';
import { formatDate } from '@/lib/formatters';

interface PaperHeaderProps {
  paper: PaperMetadata;
  pubpeerUrl?: string;
}

export default function PaperHeader({ paper, pubpeerUrl }: PaperHeaderProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {/* Title */}
      <h1 className="font-serif text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl leading-snug">
        {paper.title || 'Untitled Scholarly Work'}
      </h1>

      {/* Bibliographic Metadata Row */}
      <div className="mt-4 flex flex-wrap items-center gap-y-2 gap-x-6 text-sm text-slate-600 dark:text-slate-400">
        {paper.journal && (
          <div className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
            <BookOpen className="h-4 w-4 text-indigo-500" />
            <span>{paper.journal}</span>
          </div>
        )}

        {paper.publisher && (
          <div className="flex items-center gap-1.5">
            <Building2 className="h-4 w-4 text-slate-400" />
            <span>{paper.publisher}</span>
          </div>
        )}

        {paper.publication_date && (
          <div className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4 text-slate-400" />
            <span>{formatDate(paper.publication_date)}</span>
          </div>
        )}
      </div>

      {/* Persistent Identifier & Quick Actions */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
        {/* DOI Chip */}
        <div className="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 dark:bg-slate-800">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">DOI:</span>
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 font-mono text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
          >
            <span>{paper.doi}</span>
            <ExternalLink className="h-3 w-3" />
          </a>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          <CopyButton text={paper.doi} label="Copy" />
        </div>

        {/* Action links */}
        <div className="flex items-center gap-2">
          {pubpeerUrl && (
            <a
              href={pubpeerUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              title="Search community discussions on PubPeer"
            >
              <MessageSquare className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>PubPeer Comments</span>
              <ExternalLink className="h-3 w-3 text-slate-400" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
