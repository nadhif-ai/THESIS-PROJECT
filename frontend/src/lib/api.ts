import { invalidateAdmin, queryClient, resourceKey } from "./query-client.ts";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  const requestCsrf = csrf;
  const read = ["GET", "HEAD"].includes((options.method || "GET").toUpperCase());
  const signal = read
    ? AbortSignal.any([...(options.signal ? [options.signal] : []), AbortSignal.timeout(20_000)])
    : options.signal;
  if (!(options.body instanceof FormData) && options.body)
    headers.set("Content-Type", "application/json");
  if (csrf) headers.set("X-CSRF-Token", csrf);
  const response = await fetch(`/admin/api${path}`, {
    ...options,
    signal,
    headers,
    credentials: "same-origin",
  });
  const data = await response.json().catch((error) => {
    if (signal?.aborted) throw signal.reason;
    if (read && error instanceof TypeError) throw error;
    return null;
  });
  if (!response.ok) {
    if (response.status === 401 && path !== "/login")
      window.dispatchEvent(new Event("auth-expired"));
    throw new ApiError(
      typeof data?.detail === "string"
        ? data.detail
        : "The request could not be completed. Check your input and try again.",
      response.status,
    );
  }
  if (data === null)
    throw new Error(
      "The server returned an unreadable response. Refresh this page and try again.",
    );
  if (options.method && !["GET", "HEAD", "OPTIONS"].includes(options.method.toUpperCase())) {
    if (path.startsWith("/versions"))
      void invalidateAdmin("/versions", "/overview", "/jobs");
    else if (path === "/settings") {
      await queryClient.cancelQueries({ queryKey: resourceKey(path) });
      if (requestCsrf && requestCsrf === csrf)
        queryClient.setQueryData(resourceKey(path), data);
    }
    else if (path === "/playground")
      void invalidateAdmin("/conversations", "/overview");
    else if (path.startsWith("/evaluations/dataset"))
      void invalidateAdmin("/evaluations/dataset");
    else if (path.startsWith("/evaluations"))
      void invalidateAdmin("/jobs", "/overview");
  }
  return data as T;
}
export const jsonBody = (value: unknown) => JSON.stringify(value);
export type AdminSession = { username: string; csrf: string };
export type Version = {
  compatible: boolean;
  id: string;
  namespace: string;
  status: string;
  created_at: string;
  manifest: {
    archived?: boolean;
    files: string[];
    index_statistics?: {
      max_tokens: number;
      over_limit: number;
      embedding_token_limit: number;
      token_count_method?: string;
    };
  };
  chunking: {
    chunk_size: number;
    chunk_overlap: number;
    preprocessing: string;
  };
  chunk_count: number;
  error: string | null;
};
export type Context = {
  text: string;
  metadata: Record<string, unknown>;
  distance: number;
  similarity: number;
};
export type Answer = {
  answer: string;
  sources: string[];
  retrieval_context: Context[];
  usage: { prompt_tokens: number; completion_tokens: number };
  latency_seconds: number;
  trace_url: string | null;
};
export type Metric = {
  name: string;
  score: number | null;
  reason: string | null;
  passed: boolean | null;
  error?: string;
};
export type EvaluationResult = {
  id: string;
  dataset: string;
  model: string;
  judge: string;
  knowledge_version: string;
  chunking?: {
    chunk_size: number;
    chunk_overlap: number;
    preprocessing: string;
  };
  evaluation_recipe?: string;
  experiment_url?: string;
  reporting_error?: string;
  averages?: Record<string, number | null>;
  cases: {
    id: string;
    input?: string;
    scenario?: string;
    answer?: string;
    expected_output?: string;
    expected_outcome?: string;
    turns?: { role: string; content: string }[];
    metrics: Metric[];
    trace_url?: string;
    error?: string;
  }[];
};
export type Job = {
  id: string;
  kind: string;
  status: string;
  created_at: string;
  updated_at?: string;
  payload?: {
    version_id?: string;
    dataset?: string;
    limit?: number;
    evaluation_id?: string;
  };
  has_result?: boolean;
  result_case_count?: number | null;
  progress?: {
    phase?: string;
    started_at?: string;
    completed?: number;
    total?: number;
    case_id?: string | null;
    case_label?: string | null;
    metric?: string | null;
    metrics_completed?: number;
    metrics_total?: number;
    errors?: number;
  };
  error?: string;
  result?: EvaluationResult;
};
export type WhatsAppStatus = {
  provider: string;
  session: string;
  session_status?: string;
  engine?: string;
  worker_running: boolean;
  credentials_configured?: boolean;
  webhook_configured?: boolean;
  webhook_url?: string | null;
  checked_at?: string;
  queue?: Record<string, number>;
  last_received_at?: string | null;
  last_sent_at?: string | null;
  last_ack_at?: string | null;
};
export type Conversation = {
  id: number;
  session_id: string;
  channel: string;
  question: string;
  answer: string;
  created_at: string;
  latency: number;
  usage: Record<string, number>;
};
export type Providers = {
  openrouter_model: string;
  eval_model: string;
  semantic_top_k: number;
  embedding_model: string;
  dimension: number;
  pinecone_index: string;
  langsmith_project: string;
  whatsapp_provider: "waha" | "fonnte";
  waha_session: string | null;
  providers: Record<string, boolean>;
};
