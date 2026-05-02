import type { ApiErrorEnvelope, ChatResponse, HealthResponse } from "./types";

const API_PREFIX = import.meta.env.VITE_API_BASE?.replace(/\/$/, "") ?? "";

function url(path: string): string {
  return `${API_PREFIX}${path}`;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function parseJsonResponse<T>(res: Response): Promise<T | ApiErrorEnvelope> {
  const text = await res.text();
  if (!text) {
    throw new ApiError(res.status, "EMPTY_BODY", "Server returned an empty response.");
  }
  try {
    return JSON.parse(text) as T | ApiErrorEnvelope;
  } catch {
    throw new ApiError(
      res.status,
      "INVALID_JSON",
      "Server returned non-JSON data.",
      text.slice(0, 500),
    );
  }
}

function isErrorEnvelope(x: unknown): x is ApiErrorEnvelope {
  return (
    typeof x === "object" &&
    x !== null &&
    "error" in x &&
    typeof (x as ApiErrorEnvelope).error === "object" &&
    (x as ApiErrorEnvelope).error !== null
  );
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(url("/api/health"));
  const data = await parseJsonResponse<HealthResponse | ApiErrorEnvelope>(res);
  if (!res.ok && isErrorEnvelope(data)) {
    const e = data.error;
    throw new ApiError(res.status, e.code, e.message, e.details);
  }
  if (!res.ok) {
    throw new ApiError(res.status, "HEALTH_FAILED", "Health check failed.");
  }
  return data as HealthResponse;
}

export async function postChat(message: string, sessionId: string | null): Promise<ChatResponse> {
  const res = await fetch(url("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  const data = await parseJsonResponse<ChatResponse | ApiErrorEnvelope>(res);

  if (!res.ok) {
    if (isErrorEnvelope(data)) {
      const e = data.error;
      throw new ApiError(res.status, e.code, e.message, e.details);
    }
    throw new ApiError(res.status, "UNKNOWN", `Request failed (${res.status}).`);
  }

  if (isErrorEnvelope(data)) {
    const e = data.error;
    throw new ApiError(res.status, e.code, e.message, e.details);
  }

  return data as ChatResponse;
}
