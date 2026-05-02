export type RelatedService = {
  name: string;
  reason: string;
};

export type RetrievedPassage = {
  text: string;
  source: string;
  page: number | null;
  distance: number | null;
};

export type ChatResponse = {
  session_id: string;
  answer: string;
  booking_link: string | null;
  related_services: RelatedService[];
  escalated: boolean;
  escalation_reason: string | null;
  support_url: string | null;
  sources: RetrievedPassage[];
  retrieval_confidence: number | null;
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: unknown;
};

export type ApiErrorEnvelope = {
  error: ApiErrorBody;
};

export type HealthResponse = {
  status: string;
  kb_chunks: number;
  chroma_path: string;
  hint?: string | null;
};
