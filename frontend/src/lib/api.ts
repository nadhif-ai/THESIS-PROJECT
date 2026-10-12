let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && options.body)
    headers.set("Content-Type", "application/json");
  if (csrf) headers.set("X-CSRF-Token", csrf);
  const response = await fetch(`/admin/api${path}`, {
    ...options,
    headers,
    credentials: "same-origin",
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "/login")
      window.dispatchEvent(new Event("auth-expired"));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be completed. Check your input and try again.",
    );
  }
  return data as T;
}
export const jsonBody = (value: unknown) => JSON.stringify(value);
export type Version = {
  id: string;
  namespace: string;
  status: string;
  created_at: string;
  manifest: {
    files: string[];
    index_statistics?: { max_tokens: number; over_limit: number; embedding_token_limit: number };
  };
  chunking: { chunk_size: number; chunk_overlap: number; preprocessing: string };
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
  chunking?: { chunk_size: number; chunk_overlap: number; preprocessing: string };
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
  error?: string;
  result?: EvaluationResult;
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
  providers: Record<string, boolean>;
};
