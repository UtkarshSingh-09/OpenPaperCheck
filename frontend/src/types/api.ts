/**
 * TypeScript API contracts matching OpenPaperCheck FastAPI schemas (backend/openapi.json).
 */

export type PaperPublicState =
  | 'retracted_external'
  | 'needs_review'
  | 'no_flags_found'
  | 'insufficient_data';

export type SignalId =
  | 'S-001'
  | 'S-002'
  | 'S-003'
  | 'S-010'
  | 'S-040';

export interface SignalEvidence {
  source?: string;
  provider?: string;
  deposit_status?: string;
  has_references?: boolean;
  rw_record_id?: number | null;
  record_id?: number | null;
  nature?: string;
  retraction_nature?: string;
  retraction_date?: string;
  date?: string;
  original_date?: string;
  notice_doi?: string | null;
  reasons?: string[];
  notice_urls?: string[];
  [key: string]: unknown;
}

export interface Signal {
  id: SignalId;
  name: string;
  category: string;
  is_public: boolean;
  value: unknown;
  description: string;
  evidence: SignalEvidence[];
}

export type CitationTiming =
  | 'cited_after_retraction'
  | 'cited_before_retraction'
  | 'unknown';

export interface RetractedRefInfo {
  position?: number | null;
  doi: string;
  nature: string;
  retraction_date: string;
  timing: CitationTiming;
  rw_record_id?: number | null;
  reasons: string[];
}

export interface ReferenceBreakdown {
  available: boolean;
  deposit_status: 'open' | 'deposited' | 'restricted' | 'missing' | string;
  source: string;
  total: number;
  with_doi: number;
  without_doi: number;
  retracted: RetractedRefInfo[];
}

export interface PaperMetadata {
  title: string;
  journal: string;
  publisher: string;
  publication_date: string;
  doi: string;
}

export interface CoverageInfo {
  sources_answered: string[];
  sources_failed: string[];
}

export interface CheckResponse {
  doi: string;
  state: PaperPublicState;
  headline: string;
  paper: PaperMetadata;
  signals: Signal[];
  references: ReferenceBreakdown;
  coverage: CoverageInfo;
  data_as_of: Record<string, string>;
  external_links: Record<string, string>;
  disclaimer: string;
}

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  invalid_doi?: string;
  missing_doi?: string;
  upstream_status?: number;
  errors?: Array<{ loc: string[]; msg: string; type: string }>;
}

export interface HealthResponse {
  status: string;
  version: string;
  db: string;
  as_of: string;
  records_count: number | null;
  is_sample: boolean;
}

export interface SourceMetadata {
  name: string;
  authority: string;
  license: string;
  records_count: number | null;
  as_of_date: string;
  description: string;
}

export interface SourcesResponse {
  sources: SourceMetadata[];
  disclaimer: string;
}
