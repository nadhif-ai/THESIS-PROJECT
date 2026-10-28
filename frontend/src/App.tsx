import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import type { CSSProperties, FormEvent, ReactNode, RefObject } from "react";
import {
  Grid2X2,
  Database,
  MessagesSquare,
  SlidersHorizontal,
  FlaskConical,
  MessageSquare,
  ArrowUpRight,
  RefreshCcw,
  Send,
  LogOut,
  Check,
  FileText,
  Search,
  Moon,
  Sun,
  X,
  Eye,
  EyeOff,
  CircleCheck,
  CircleAlert,
  Circle,
  Clock3,
} from "lucide-react";
import { toast } from "sonner";
import { useTheme } from "next-themes";
import { ReplyText, GenerationDetails, Typing } from "@/components/playground-reply";
import brandMark from "@/assets/brand-mark.png";
import printingDesk from "@/assets/printing-desk.jpg";
import { api, ApiError, jsonBody, setCsrf } from "@/lib/api";
import { NINEROUTER_MODELS, NINEROUTER_MODEL_OPTIONS, providerModelLabel } from "@/lib/provider-models";
import { dashboardPriorities } from "@/lib/dashboard-priorities";
import { adminPagePath, readAdminPage } from "@/lib/admin-navigation";
import { replyProcessing } from "@/lib/whatsapp-status";
import {
  isTransientReadError,
  queryClient,
  resourceKey,
} from "@/lib/query-client";
import { prefetchResource, useResource } from "@/hooks/use-resource";
import { KnowledgePage } from "@/components/knowledge-page";
import { CatalogPage, MediaPreview } from "@/components/catalog-page";
import { EvaluationMath, EvaluationMethodGuide, MetricMath } from "@/components/evaluation-math";
import { evaluationView, metricEvidence, percentage, QA_METRICS } from "@/lib/evaluation-metrics";
import type { KnowledgeCatalog } from "@/components/knowledge-page";
import type {
  AdminSession,
  Version,
  Answer,
  Job,
  Conversation,
  EvaluationResult,
  EvaluationSummary,
  Providers,
  WhatsAppStatus,
} from "@/lib/api";
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  FieldGroup,
  Field,
  FieldContent,
  FieldLabel,
  FieldDescription,
} from "@/components/ui/field";
import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyMedia,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import { Skeleton } from "@/components/ui/skeleton";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  Message,
  MessageContent,
  MessageHeader,
  MessageFooter,
} from "@/components/ui/message";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import {
  MessageScroller,
  MessageScrollerProvider,
  MessageScrollerViewport,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerButton,
} from "@/components/ui/message-scroller";

const pages = [
  { name: "Dashboard", icon: Grid2X2 },
  { name: "Knowledge", icon: Database },
  { name: "Catalog", icon: FileText },
  { name: "Playground", icon: MessagesSquare },
  { name: "Conversations", icon: MessageSquare },
  { name: "Providers", icon: SlidersHorizontal },
  { name: "Evaluations", icon: FlaskConical },
];
const date = (value: string) =>
  new Date(value).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
const descriptions: Record<string, string> = {
  Catalog: "Manage approved product illustrations and preview when they appear in replies.",
  Dashboard:
    "Active knowledge, customer activity, and work that needs attention.",
  Knowledge:
    "Manage sources and sync one knowledge base for every conversation.",
  Playground:
    "Try a customer question and inspect the evidence behind the answer.",
  Conversations: "Find a customer question and review the reply they received.",
  Providers:
    "Configure models and check the path from WhatsApp to a customer reply.",
  Evaluations:
    "Run reviewed cases, follow scoring progress, and compare the results.",
};
const jobName = (kind: string) =>
  ({
    evaluate: "Evaluation",
    index: "Knowledge indexing",
    sync: "Knowledge synchronization",
    generate: "Scenario generation",
    report: "Report upload",
  })[kind] || kind;
function BrandMark() {
  return (
    <span className="brand-mark">
      <img src={brandMark} alt="" />
    </span>
  );
}
function ThemeButton() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Switch to light theme" : "Switch to dark theme"}
      onClick={() => setTheme(dark ? "light" : "dark")}
    >
      {dark ? <Sun /> : <Moon />}
    </Button>
  );
}
function displayAnswer(text: string) {
  return text
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|li)>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&nbsp;/g, " ");
}
function Status({ value }: { value: string }) {
  const success = [
    "published",
    "completed",
    "ready",
    "reviewed",
    "WORKING",
    "sent",
    "running worker",
  ].includes(value);
  const danger = [
    "failed",
    "unreachable",
    "FAILED",
    "uncertain",
    "interrupted",
  ].includes(value);
  const active = [
    "running",
    "indexing",
    "STARTING",
    "generating",
    "sending",
  ].includes(value);
  const labels: Record<string, string> = {
    published: "Published",
    ready: "Ready for review",
    reviewed: "Reviewed",
    completed: "Completed",
    running: "Running",
    queued: "Queued",
    draft: "Draft",
    failed: "Failed",
    interrupted: "Interrupted",
    WORKING: "Connected",
    STARTING: "Connecting",
    SCAN_QR_CODE: "Scan QR code",
    STOPPED: "Stopped",
    FAILED: "Connection failed",
    unreachable: "Unreachable",
    uncertain: "Delivery uncertain",
    sent: "Sent",
  };
  return (
    <Badge
      variant="outline"
      className="status-label"
      data-tone={
        success
          ? "success"
          : danger
            ? "danger"
            : active
              ? "active"
              : value === "SCAN_QR_CODE"
                ? "warning"
                : "neutral"
      }
    >
      {success && <Check data-icon="inline-start" />}
      {labels[value] || value}
    </Badge>
  );
}
function ErrorNotice({ error, retry }: { error: string; retry?: () => void }) {
  return (
    <Alert variant="destructive" role="alert">
      <CircleAlert />
      <AlertTitle>We could not complete this request</AlertTitle>
      <AlertDescription>
        {error}
        {retry && (
          <Button variant="outline" onClick={retry}>
            Try again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
function NoItems({
  title,
  description,
  icon = Database,
}: {
  title: string;
  description: string;
  icon?: typeof Database;
}) {
  const Icon = icon;
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icon />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}
function Panel({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="panel-heading">
          <div className="flex flex-col gap-1">
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
function Loading({ label = "Loading workspace data…" }: { label?: string }) {
  return (
    <div className="flex flex-col gap-5" role="status" aria-label={label}>
      <p className="loading-copy">{label}</p>
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}
async function action(
  task: () => Promise<unknown>,
  message: string,
  reload?: () => void,
) {
  try {
    await task();
    toast.success(message);
    reload?.();
  } catch (error) {
    toast.error((error as Error).message);
  }
}

function Login({ onLogin }: { onLogin: (user: AdminSession) => void }) {
  const [username, setUsername] = useState("admin"),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [showPassword, setShowPassword] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await api<AdminSession>("/login", {
        method: "POST",
        body: jsonBody({ username, password }),
      });
      setCsrf(user.csrf);
      onLogin(user);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story" aria-label="About this workspace">
        <a
          className="workspace-brand"
          href="/"
          aria-label="Asia Visual Grafika home"
        >
          <BrandMark />
          <div>
            <strong>Asia Visual Grafika</strong>
            <small>Printing support workspace</small>
          </div>
        </a>
        <div>
          <h1>Keep printing guidance ready for customer questions.</h1>
          <p>
            Keep printing guidance current, check customer replies, and follow
            your WhatsApp connection from one workspace.
          </p>
        </div>
        <img
          className="login-image"
          src={printingDesk}
          alt="Paper samples and blue print proofs on a printing worktable"
        />
        <footer>
          Administrator workspace. Customers contact the shop through WhatsApp.
        </footer>
      </section>
      <section className="login-form-area" aria-labelledby="login-heading">
        <div className="login-theme">
          <ThemeButton />
        </div>
        <div className="login-form">
          <h2 id="login-heading">Sign in to your workspace</h2>
          <p>Use your administrator account to continue.</p>
          <form onSubmit={submit} className="flex flex-col gap-6">
            <FieldGroup>
              <Field data-invalid={!!error}>
                <FieldLabel htmlFor="username">Username</FieldLabel>
                <Input
                  id="username"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  aria-invalid={!!error}
                />
              </Field>
              <Field data-invalid={!!error}>
                <FieldLabel htmlFor="password">Password</FieldLabel>
                <div className="password-control">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    aria-invalid={!!error}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff /> : <Eye />}
                  </Button>
                </div>
              </Field>
            </FieldGroup>
            {error && <ErrorNotice error={error} />}
            <Button
              type="submit"
              disabled={busy}
              data-icon={busy ? "inline-start" : undefined}
            >
              {busy && <Spinner />}Sign in
            </Button>
          </form>
          <p className="help-copy login-footnote">
            Need access? Ask the person who set up this workspace for your
            administrator credentials.
          </p>
          <a className="login-home-link" href="/">
            Back to the overview
          </a>
        </div>
      </section>
    </main>
  );
}

type Overview = {
  conversations: number;
  whatsapp_messages: number;
  average_latency: number | null;
  published: Version | null;
  latest_evaluation: EvaluationSummary | null;
  recent: Conversation[];
  jobs: Job[];
};
function Dashboard({ navigate }: { navigate: (page: string) => void }) {
  const { data, error, reload, refreshing, updatedAt } = useResource<Overview>("/overview", true);
  const knowledge = useResource<KnowledgeCatalog>("/knowledge", true);
  const whatsapp = useResource<WhatsAppStatus>("/whatsapp/status", true);
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!data)
    return <Loading label="Loading active knowledge and recent activity…" />;
  const activeJobs = data.jobs.filter((job) =>
    ["queued", "running"].includes(job.status),
  );
  const priorities = dashboardPriorities({ published: data.published, jobs: data.jobs, knowledge: knowledge.data, whatsapp: whatsapp.data });
  const next = priorities[0];
  return (
    <div className="page-section dashboard-page">
      {error && <ErrorNotice error={error} retry={reload} />}
      {whatsapp.error && <ErrorNotice error={`WhatsApp readiness could not be refreshed. ${whatsapp.error}`} retry={whatsapp.reload} />}
      {!whatsapp.data && !whatsapp.error && <p role="status" className="help-copy">Checking WhatsApp readiness…</p>}
      <section className="dashboard-next" aria-labelledby="dashboard-next-title">
        <div>
          <h2 id="dashboard-next-title">{next?.title || "Review customer guidance"}</h2>
          <p>{next?.detail || "Test a customer question against active knowledge, then inspect its supporting evidence."}</p>
        </div>
        <Button onClick={() => navigate(next?.page || "Playground")}>
          {next?.action || "Test a customer question"}
        </Button>
      </section>
      {priorities.length > 1 && (
        <ul className="dashboard-review-list" aria-label="Other conditions to review">
          {priorities.slice(1).map(item => <li key={item.title}>
            <CircleAlert aria-hidden="true" />
            <div><h3>{item.title}</h3><p>{item.detail}</p></div>
            <Button variant="outline" size="sm" onClick={() => navigate(item.page)}>{item.action}</Button>
          </li>)}
        </ul>
      )}
      <div className="dashboard-check-time">
        <p className="help-copy">{error ? "Last successful overview" : "Overview checked"} {updatedAt ? date(updatedAt) : "Not recorded"}. Updates automatically.</p>
        <Button size="sm" variant="ghost" disabled={refreshing} onClick={reload}>
          <RefreshCcw data-icon="inline-start" />{refreshing ? "Refreshing…" : "Refresh overview"}
        </Button>
      </div>
      <section className="overview-proof" aria-label="Active knowledge">
        <div>
          <h2>Knowledge readiness</h2>
          <p className="help-copy mb-3">The active snapshot used by WhatsApp and Playground.</p>
          <div className="proof-record">
            <Badge variant="outline">
              {data.published?.compatible === false ? "Reindexing required" : data.published?.chunk_count
                ? "Knowledge active"
                : "Knowledge empty"}
            </Badge>
            <span>
              <strong>{data.published?.manifest.files.length || 0}</strong>{" "}
              documents
            </span>
            <span>
              <strong>{data.published?.chunk_count || 0}</strong> indexed
              passages
            </span>
            <span>
              {data.published
                ? `Synchronized ${date(data.published.manifest.synced_at || data.published.created_at)}`
                : "Add sources in Knowledge to get started"}
            </span>
          </div>
        </div>
        <Button variant="outline" onClick={() => navigate("Knowledge")}>
          Manage knowledge
        </Button>
        <div className="dashboard-knowledge-state">
          {knowledge.error ? <ErrorNotice error={knowledge.error} retry={knowledge.reload} />
            : !knowledge.data ? <p role="status" className="help-copy">Checking source changes…</p>
            : <p className="help-copy">{knowledge.data.sync_job
              ? data.published?.chunk_count
                ? "Sync in progress. The previous snapshot remains active until its replacement is verified."
                : "Sync in progress. Customer knowledge becomes available after verification and activation."
              : knowledge.data.pending
                ? "Unsynchronized source changes are excluded from customer replies."
                : "No source changes waiting to sync."}</p>}
        </div>
      </section>
      {activeJobs.length > 0 && (
        <Panel
          title="Work in progress"
          description="Observed stages update automatically while a job is running."
        >
          {activeJobs.map((job) => (
            <JobProgress key={job.id} job={job} />
          ))}
        </Panel>
      )}
      <div className="overview-columns">
        <div className="page-section">
          <WhatsAppConnection compact />
          <Panel
            title="Recent conversations"
            description="Latest customer, playground, API, and evaluation replies."
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("Conversations")}
              >
                View history
              </Button>
            }
          >
            <dl className="dashboard-activity-context">
              <div><dt>WhatsApp replies</dt><dd>{data.whatsapp_messages.toLocaleString()}</dd></div>
              <div><dt>All channels</dt><dd>{data.conversations.toLocaleString()}</dd></div>
              <div><dt>Average response</dt><dd>{data.average_latency != null ? `${data.average_latency}s` : "Not recorded"}</dd></div>
            </dl>
            <p className="help-copy mb-4">Totals and response time use all stored replies.</p>
            {data.recent.length ? (
              <Table className="recent-conversations-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Question</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.recent.slice(0, 5).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="max-w-60 truncate">
                        <span title={r.question}>{r.question}</span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{r.channel}</Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {date(r.created_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <NoItems
                title="Your conversation history starts here"
                description="Ask a question in the playground or connect WhatsApp."
              />
            )}
            {data.recent.length === 0 && <Button variant="outline" className="mt-4" onClick={() => navigate("Playground")}>Try a customer question</Button>}
          </Panel>
        </div>
        <LatestEvaluation summary={data.latest_evaluation} activeVersion={data.published?.id} />
      </div>
      {data.jobs.length > 0 && (
        <Panel title="Background work">
          <JobTable jobs={data.jobs} />
        </Panel>
      )}
    </div>
  );
}

function LatestEvaluation({ summary, activeVersion }: {
  summary: EvaluationSummary | null;
  activeVersion?: string;
}) {
  return (
    <Panel title="Latest QA evaluation" description={summary
      ? `${summary.dataset === "audited" ? "Reviewed QA" : "Original questions"} · ${summary.case_count} cases${summary.runtime_top_k != null ? ` · k=${summary.runtime_top_k}` : ""} · ${date(summary.completed_at || summary.created_at)}`
      : "No completed QA evaluation yet."}>
      {summary ? (
        <>
          <div className="evaluation-summary-values">
            {QA_METRICS.map((name) => {
              const score = summary.averages?.[name];
              const available = typeof score === "number" && Number.isFinite(score);
              return (
                <div key={name}>
                  <span>{name}</span>
                  <strong data-unavailable={!available || undefined}>{available ? percentage(score) : "Unavailable"}</strong>
                  <small>{summary.scored_cases[name] || 0}/{summary.case_count} scored</small>
                </div>
              );
            })}
          </div>
          <p className="help-copy mt-4">Mean scores; missing results are excluded.</p>
          {summary.knowledge_version && summary.knowledge_version !== activeVersion && (
            <p className="help-copy mt-2">This run used older knowledge.</p>
          )}
        </>
      ) : <p className="help-copy">Complete a QA run to see answer quality and retrieval scores here.</p>}
      <Button variant="outline" className="mt-4" asChild>
        <a href={summary ? `/admin/evaluations?run=${encodeURIComponent(summary.job_id)}` : "/admin/evaluations"}>
          {summary ? "View evaluation" : "Open evaluations"}
        </a>
      </Button>
    </Panel>
  );
}

function Playground() {
  const evidence = useRef<HTMLDivElement>(null);
  const { data, error, reload } = useResource<KnowledgeCatalog>(
    "/knowledge",
    true,
  );
  const [session, setSession] = useState(() => crypto.randomUUID()),
    [question, setQuestion] = useState(""),
    [busy, setBusy] = useState(false),
    [failure, setFailure] = useState(""),
    [history, setHistory] = useState<
      { role: string; text: string; response?: Answer }[]
    >([]),
    [inspect, setInspect] = useState<Answer | null>(null);
  async function send(event: FormEvent) {
    event.preventDefault();
    if (!question.trim() || busy) return;
    const input = question.trim();
    setQuestion("");
    setFailure("");
    setBusy(true);
    setHistory((h) => [...h, { role: "user", text: input }]);
    try {
      const response = await api<Answer>("/playground", {
        method: "POST",
        body: jsonBody({
          question: input,
          session_id: session,
        }),
      });
      setHistory((h) => [
        ...h,
        { role: "assistant", text: response.answer, response },
      ]);
      setInspect(response);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!data) return <Loading label="Loading active knowledge…" />;
  return (
    <div className="flex flex-col gap-4">
      {error && <ErrorNotice error={error} retry={reload} />}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Badge variant="outline">Current synchronized knowledge</Badge>
        <Button
          variant="outline"
          onClick={() => {
            setHistory([]);
            setInspect(null);
            setSession(crypto.randomUUID());
          }}
          disabled={busy || history.length === 0}
        >
          <RefreshCcw data-icon="inline-start" />
          New conversation
        </Button>
      </div>
      <p className="help-copy">
        {data.active?.chunk_count
          ? "Uses the same active knowledge as WhatsApp. Unsynchronized source changes are excluded."
          : "Knowledge is empty. Factual questions receive a general fallback; greetings and reset remain available."}
      </p>
      <div className="playground-grid">
        <Card className="flex min-h-0 flex-col">
          <CardHeader>
            <CardTitle>Try a customer conversation</CardTitle>
            <CardDescription>
              The same chatbot pipeline used by WhatsApp.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex min-h-0 flex-1 flex-col">
            <MessageScrollerProvider autoScroll>
              <MessageScroller>
                <MessageScrollerViewport>
                  <MessageScrollerContent className="p-1">
                    {history.length === 0 ? (
                      <MessageScrollerItem messageId="empty">
                        <div className="flex min-h-72 items-center justify-center">
                          <NoItems
                            title="Ask like a customer"
                            description="Ask about a print file, material, price, or shop policy. The answer and its sources will appear here."
                            icon={MessagesSquare}
                          />
                        </div>
                      </MessageScrollerItem>
                    ) : (
                      history.map((row, i) => (
                        <MessageScrollerItem
                          key={i}
                          messageId={String(i)}
                          scrollAnchor={row.role === "user"}
                        >
                          <Message
                            align={row.role === "user" ? "end" : "start"}
                          >
                            <MessageContent>
                              <MessageHeader>
                                {row.role === "user"
                                  ? "You"
                                  : "Asia Visual Grafika"}
                              </MessageHeader>
                              {row.response && (
                                <MediaPreview answer={row.response} diagnostics={false} />
                              )}
                              <Bubble
                                variant={
                                  row.role === "user" ? "default" : "muted"
                                }
                              >
                                <BubbleContent>
                                  {row.role === "assistant" ? (
                                    <ReplyText text={displayAnswer(row.text)} />
                                  ) : <p className="whitespace-pre-wrap">{row.text}</p>}
                                </BubbleContent>
                              </Bubble>
                              {row.response && (
                                <MessageFooter className="playground-message-footer">
                                  <GenerationDetails answer={row.response} />
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setInspect(row.response!);
                                      if (window.matchMedia("(max-width: 1023px)").matches) {
                                        evidence.current?.scrollIntoView({ block: "start" });
                                        evidence.current?.focus({ preventScroll: true });
                                      }
                                    }}
                                  >
                                    Inspect{" "}
                                    {row.response.retrieval_context.length}{" "}
                                    sources
                                  </Button>
                                </MessageFooter>
                              )}
                            </MessageContent>
                          </Message>
                        </MessageScrollerItem>
                      ))
                    )}
                    {busy && (
                      <MessageScrollerItem messageId="pending">
                        <Message align="start">
                          <MessageContent>
                            <MessageHeader>Asia Visual Grafika</MessageHeader>
                            <Bubble variant="muted"><BubbleContent><Typing /></BubbleContent></Bubble>
                            <span className="help-copy">Preparing a reply…</span>
                          </MessageContent>
                        </Message>
                      </MessageScrollerItem>
                    )}
                  </MessageScrollerContent>
                </MessageScrollerViewport>
                <MessageScrollerButton />
              </MessageScroller>
            </MessageScrollerProvider>
          </CardContent>
          <CardFooter className="flex-col items-stretch gap-3">
            {failure && <ErrorNotice error={failure} />}
            <form onSubmit={send} className="flex items-end gap-2">
              <Field className="flex-1">
                <FieldLabel htmlFor="question" className="sr-only">
                  Customer question
                </FieldLabel>
                <Textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Type a customer question…"
                  rows={2}
                  disabled={busy}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void send(e);
                    }
                  }}
                />
              </Field>
              <Button
                type="submit"
                size="icon"
                disabled={busy || !question.trim()}
                aria-label="Send question"
              >
                {busy ? <Spinner /> : <Send />}
              </Button>
            </form>
            <p className="help-copy composer-hint">
              <span>Enter to send. Shift + Enter for a new line.</span>
              <span>Test replies stay in this workspace.</span>
            </p>
          </CardFooter>
        </Card>
        <Card ref={evidence} tabIndex={-1} className="flex min-h-0 flex-col">
          <CardHeader>
            <CardTitle>Behind the answer</CardTitle>
            <CardDescription>
              Retrieved evidence, response time, and trace.
            </CardDescription>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 overflow-y-auto">
            {!inspect ? (
              <NoItems
                title="Evidence appears here"
                description="Send a question, then inspect the knowledge used for its answer."
                icon={FileText}
              />
            ) : (
              <div className="flex flex-col gap-5">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{inspect.latency_seconds}s</Badge>
                  <Badge variant="outline">
                    {inspect.usage.prompt_tokens +
                      inspect.usage.completion_tokens}{" "}
                    tokens
                  </Badge>
                  {inspect.trace_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href={inspect.trace_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        LangSmith trace
                        <ArrowUpRight data-icon="inline-end" />
                      </a>
                    </Button>
                  )}
                </div>
                {inspect.media_decision && (
                  <details className="source-passage">
                    <summary>Image selection details</summary>
                    <MediaPreview answer={{ ...inspect, media_url: null, media_selection: null }} />
                  </details>
                )}
                <p className="help-copy">
                  {inspect.retrieval_context.length} retrieved passages. Review their content to judge whether they support the answer.
                </p>
                {inspect.retrieval_context.map((chunk, i) => (
                  <details className="source-passage" key={i} open={i === 0}>
                    <summary>
                      <span className="source-number">{i + 1}</span>
                      <span>
                        {String(chunk.metadata.source || "Knowledge passage")}
                      </span>
                      <span className="source-score">
                        {chunk.metadata.retrieval_method === "section_expansion"
                          ? "Related passage"
                          : typeof chunk.similarity === "number" && Number.isFinite(chunk.similarity)
                            ? `Similarity ${chunk.similarity.toFixed(3)}` : "Similarity unavailable"}
                      </span>
                    </summary>
                    <p className="help-copy">
                      {chunk.metadata.retrieval_method === "section_expansion"
                        ? "Included from the same section of the synchronized knowledge to complete the retrieved evidence."
                        : "Cosine similarity measures closeness to your question, not answer accuracy."}
                    </p>
                    <p className="passage-text">{chunk.text}</p>
                  </details>
                ))}
                {inspect.retrieval_context.length === 0 && (
                  <NoItems
                    title="No knowledge passages attached"
                    description={inspect.media_decision?.retrieval_reason === "social_message"
                      ? "This social reply did not require business facts."
                      : "Review the reply and image selection details. No business passages were included in this response."}
                  />
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Conversations() {
  const [channel, setChannel] = useState("whatsapp"),
    [search, setSearch] = useState(""),
    [selected, setSelected] = useState<Conversation | null>(null),
    [pageIndex, setPageIndex] = useState(0);
  const { data, error, reload } = useResource<Conversation[]>(
    `/conversations${channel ? "?channel=" + channel : ""}`,
    true,
  );
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!data)
    return <Loading label="Loading recorded customer questions and replies…" />;
  const rows = data.filter((r) =>
    (r.question + " " + r.answer).toLowerCase().includes(search.toLowerCase()),
  );
  const lastPage = Math.max(0, Math.ceil(rows.length / 20) - 1);
  const currentPage = Math.min(pageIndex, lastPage);
  const visibleRows = rows.slice(currentPage * 20, currentPage * 20 + 20);
  return (
    <div className="flex flex-col gap-5">
      {error && <ErrorNotice error={error} retry={reload} />}
      <FieldGroup className="conversation-filters">
        <Field className="max-w-sm">
          <FieldLabel htmlFor="conversation-search">Search messages</FieldLabel>
          <Input
            id="conversation-search"
            placeholder="Find a question or answer"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPageIndex(0);
            }}
          />
        </Field>
        <Field className="max-w-52">
          <FieldLabel htmlFor="channel">Channel</FieldLabel>
          <NativeSelect
            id="channel"
            value={channel}
            onChange={(e) => {
              setChannel(e.target.value);
              setPageIndex(0);
            }}
          >
            {[
              ["whatsapp", "WhatsApp"],
              ["playground", "Playground"],
              ["api", "API"],
              ["evaluation", "Evaluation"],
              ["", "All channels"],
            ].map(([value, label]) => (
              <NativeSelectOption key={value} value={value}>
                {label}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
      </FieldGroup>
      <Panel
        title="Conversation history"
        description={`${rows.length} matching messages from the latest ${data.length} records in this channel.`}
      >
        {rows.length ? (
          <Table className="conversation-table">
            <TableHeader>
              <TableRow>
                <TableHead>Customer question</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>Response time</TableHead>
                <TableHead>Received</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleRows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <button
                      className="question-link"
                      onClick={() => setSelected(row)}
                    >
                      {row.question}
                    </button>
                    <p className="answer-preview">
                      {row.answer
                        ? displayAnswer(row.answer)
                        : "No automatic reply recorded."}
                    </p>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{row.channel}</Badge>
                  </TableCell>
                  <TableCell>
                    {row.latency
                      ? `${row.latency.toFixed(1)}s`
                      : "Not recorded"}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {date(row.created_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <NoItems
            title={
              search
                ? "No replies match this search"
                : "No replies recorded in this channel"
            }
            description={
              search
                ? "Clear the search or choose another channel to see recorded replies."
                : "Replies will appear here after a customer message, playground question, or evaluation is processed."
            }
            icon={MessageSquare}
          />
        )}
      </Panel>
      {rows.length > 20 && (
        <div className="flex items-center justify-between gap-4">
          <p className="help-copy">
            Showing {currentPage * 20 + 1}–
            {Math.min((currentPage + 1) * 20, rows.length)} of {rows.length}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={currentPage === 0}
              onClick={() => setPageIndex(currentPage - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={currentPage === lastPage}
              onClick={() => setPageIndex(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
      <Dialog
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Conversation detail</DialogTitle>
            <DialogDescription>
              {selected && date(selected.created_at)}
            </DialogDescription>
          </DialogHeader>
          <div className="flex max-h-[65vh] flex-col gap-4 overflow-y-auto">
            <div className="proof-record">
              <Badge variant="outline">{selected?.channel}</Badge>
              <span>
                {selected?.latency
                  ? `${selected.latency.toFixed(1)}s response`
                  : "Response time not recorded"}
              </span>
            </div>
            <p className="whitespace-pre-wrap">
              <strong>Customer</strong>
              <br />
              {selected?.question}
            </p>
            <p className="whitespace-pre-wrap">
              <strong>Chatbot</strong>
              <br />
              {selected
                ? selected.answer
                  ? displayAnswer(selected.answer)
                  : "No automatic reply recorded."
                : ""}
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ProvidersPage() {
  const { data, error, reload } = useResource<Providers>("/settings"),
    [draftForm, setForm] = useState<Providers | null>(null),
    [saving, setSaving] = useState(false);
  const form = draftForm || data;
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!form)
    return (
      <Loading label="Loading model settings and provider configuration…" />
    );
  const answerModelKey = form.answer_provider === "9router" ? "ninerouter_model" : "openrouter_model";
  const answerModels = form.answer_provider === "9router"
    ? NINEROUTER_MODELS
    : ["openai/gpt-6-luna", "anthropic/claude-haiku-5.5", "minimax/minimax-m3.1-flash"];
  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    await action(
      () => api("/settings", { method: "PUT", body: jsonBody(form) }),
      "Provider settings saved",
      () => setForm(null),
    );
    setSaving(false);
  }
  return (
    <div className="providers-grid">
      {error && <ErrorNotice error={error} retry={reload} />}
      <div className="page-section">
        <Panel
          title="Models and retrieval"
          description="Choose separate models for replies, evaluation scoring, and product intent."
        >
          <form onSubmit={save} className="flex flex-col gap-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="answer-provider">Answering provider</FieldLabel>
                <NativeSelect
                  id="answer-provider"
                  value={form.answer_provider}
                  onChange={(event) => setForm({ ...form, answer_provider: event.target.value as Providers["answer_provider"] })}
                >
                  <NativeSelectOption value="openrouter">OpenRouter</NativeSelectOption>
                  <NativeSelectOption value="9router">9Router (OpenAI-compatible)</NativeSelectOption>
                </NativeSelect>
                <FieldDescription>Used for customer replies in WhatsApp, Playground, and evaluations.</FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="answer-model">Answering model</FieldLabel>
                <NativeSelect
                  id="answer-model"
                  value={form[answerModelKey]}
                  onChange={(e) =>
                    setForm({ ...form, [answerModelKey]: e.target.value })
                  }
                  required
                >
                  {[...new Set([form[answerModelKey], ...answerModels])].map((model) => <NativeSelectOption key={model} value={model}>{model}</NativeSelectOption>)}
                </NativeSelect>
                <FieldDescription>
                  Model identifier used for customer replies.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="judge-model">
                  Evaluation scoring model
                </FieldLabel>
                <NativeSelect
                  id="judge-model"
                  value={form.eval_model}
                  onChange={(e) =>
                    setForm({ ...form, eval_model: e.target.value })
                  }
                  required
                >
                  {[...new Set([form.eval_model, "deepseek/deepseek-v4.1-flash", "z-ai/glm-5.3-flash", "anthropic/claude-haiku-5.5", ...NINEROUTER_MODEL_OPTIONS])].map((model) => <NativeSelectOption key={model} value={model}>{providerModelLabel(model)}</NativeSelectOption>)}
                </NativeSelect>
                <FieldDescription>
                  DeepEval uses the selected provider and model to score answers.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="intent-model">Intent model</FieldLabel>
                <NativeSelect id="intent-model" value={form.product_intent_model || ""} onChange={(event) => setForm({ ...form, product_intent_model: event.target.value })} required>
                  {!form.product_intent_model && <NativeSelectOption value="" disabled>Choose an intent model</NativeSelectOption>}
                  {[...new Set([form.product_intent_model, "z-ai/glm-5.3-flash", "openai/gpt-oss-20b", ...NINEROUTER_MODEL_OPTIONS])].filter(Boolean).map((model) => <NativeSelectOption key={model} value={model}>{providerModelLabel(model)}</NativeSelectOption>)}
                </NativeSelect>
                <FieldDescription>Identifies product and image requests using the selected provider. The model must support structured JSON output.</FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="top-k">Retrieved passages</FieldLabel>
                <Input
                  id="top-k"
                  type="number"
                  min={1}
                  max={20}
                  value={form.semantic_top_k}
                  onChange={(e) =>
                    setForm({ ...form, semantic_top_k: Number(e.target.value) })
                  }
                  required
                />
                <FieldDescription>
                  Maximum source passages supplied to an answer. More passages
                  can add context and model usage.
                </FieldDescription>
              </Field>
            </FieldGroup>
            <Button type="submit" disabled={saving}>
              {saving && <Spinner data-icon="inline-start" />}Save settings
            </Button>
          </form>
        </Panel>
        <Panel
          title="Provider configuration"
          description="Backend credential availability. This is not a live connectivity test."
        >
          <Table>
            <TableBody>
              {Object.entries(form.providers).map(([name, connected]) => (
                <TableRow key={name}>
                  <TableCell className="capitalize">{name === "9router" ? "9Router" : name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {connected ? "Configured" : name === "9router" ? "Missing key or endpoint" : "Missing key"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Panel>
        <details className="advanced-settings">
          <summary>
            <Database />
            Knowledge infrastructure
          </summary>
          <Panel title="Knowledge infrastructure">
            <dl className="definition-list">
              <dt>Vector index</dt>
              <dd>{form.pinecone_index}</dd>
              <dt>Embedding model</dt>
              <dd>{form.embedding_model}</dd>
              <dt>Vector dimensions</dt>
              <dd>{form.dimension}</dd>
              <dt>Trace project</dt>
              <dd>{form.langsmith_project}</dd>
            </dl>
            <p className="help-copy mt-5">
              Changing embeddings requires a compatible index and reindexing.
              Historical evaluation results retain the embedding identity used
              for that run.
            </p>
          </Panel>
        </details>
      </div>
      <WhatsAppConnection />
    </div>
  );
}

function WhatsAppConnection({ compact = false }: { compact?: boolean }) {
  const { data, error, reload, refreshing, updatedAt } =
    useResource<WhatsAppStatus>("/whatsapp/status", true);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  async function save(
    path: string,
    method: string,
    body: unknown,
    message: string,
  ) {
    setSaving(true);
    setSaveError("");
    try {
      await api(path, { method, body: jsonBody(body) });
      toast.success(message);
      reload();
    } catch (error) {
      setSaveError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }
  const connected = data?.session_status === "WORKING";
  const pending = ["STARTING", "SCAN_QR_CODE"].includes(
    data?.session_status || "",
  );
  const queue = data?.queue;
  const attention = data?.attention
    ? data.attention.failed + data.attention.uncertain
    : queue
      ? (queue.failed || 0) + (queue.uncertain || 0)
      : null;
  const guidance: Record<string, string> = {
    STARTING:
      "WAHA is starting the session. The status refreshes automatically.",
    SCAN_QR_CODE:
      "Open the configured WAHA console and scan the session QR code with WhatsApp on the shop phone.",
    STOPPED:
      "Start this session in the WAHA console, then refresh this connection check.",
    FAILED:
      "Inspect the WAHA session in its console and restart it after resolving the error.",
    unreachable:
      "The backend could not read the WAHA session. Check the server address, API key, and network, then refresh.",
  };
  const checks = data
    ? [
        {
          title: "Credentials",
          ready: data.credentials_configured,
          detail:
            data.credentials_configured === undefined
              ? "Availability was not reported by this backend."
              : data.credentials_configured
                ? "API and webhook credentials are configured."
                : "Configure the WAHA API key and webhook secret on the backend.",
        },
        {
          title: "WhatsApp session",
          ready: connected,
          detail: connected
            ? `${data.session}${data.engine ? ` · ${data.engine}` : ""}. WAHA reports an active session.`
            : guidance[data.session_status || ""] ||
              "Session readiness has not been reported.",
        },
        {
          title: "Webhook configuration",
          ready: data.webhook_configured,
          detail:
            data.webhook_configured === undefined
              ? "Configuration was not reported by this backend."
              : data.webhook_configured
                ? "A callback URL and verification secret are configured. Receipt of a message confirms delivery."
                : "Set a callback URL and webhook secret, then configure the callback in WAHA.",
        },
        replyProcessing(data),
      ]
    : [];
  return (
    <Panel
      title={compact ? "WhatsApp connection" : "WhatsApp · WAHA"}
      description={
        compact
          ? "Observed session and message processing."
          : "Follow the connection from configuration to customer replies."
      }
      action={
        <Button
          size="sm"
          variant="outline"
          disabled={refreshing}
          onClick={reload}
        >
          {refreshing ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <RefreshCcw data-icon="inline-start" />
          )}
          Refresh
        </Button>
      }
    >
      {error && <ErrorNotice error={error} retry={reload} />}
      {!data && !error ? (
        <Loading label="Checking WhatsApp session and message queue…" />
      ) : data?.provider !== "waha" ? (
        data && (
          <NoItems
            title="WAHA is not the active transport"
            description="This workspace uses the configured Fonnte transport. Enable WAHA on the backend to inspect its session and inbox here."
            icon={MessageSquare}
          />
        )
      ) : (
        data && (
          <>
            <div className="proof-record">
              <Status value={data.session_status || "Not reported"} />
              <span>
                {data.execution_mode === "vercel_queue"
                  ? "Replies processed on Vercel"
                  : data.worker_running
                    ? "Reply worker running"
                    : "Reply worker stopped"}
              </span>
            </div>
            <Field
              orientation="horizontal"
              className="mt-4"
              data-disabled={saving || data.bot_replies_enabled === undefined}
            >
              <FieldContent>
                <FieldLabel
                  htmlFor={
                    compact ? "dashboard-bot-replies" : "providers-bot-replies"
                  }
                >
                  Bot replies
                </FieldLabel>
                <FieldDescription
                  id={compact ? "dashboard-bot-help" : "providers-bot-help"}
                >
                  {data.bot_replies_enabled === false
                    ? "Off. New messages are saved without an automatic reply."
                    : "On. New WhatsApp messages receive automatic replies."}
                </FieldDescription>
              </FieldContent>
              <div className="flex min-h-11 shrink-0 items-center gap-2">
                {saving && <Spinner aria-label="Saving WhatsApp settings" />}
                <Switch
                  id={
                    compact ? "dashboard-bot-replies" : "providers-bot-replies"
                  }
                  checked={data.bot_replies_enabled === true}
                  aria-describedby={
                    compact ? "dashboard-bot-help" : "providers-bot-help"
                  }
                  disabled={saving || data.bot_replies_enabled === undefined}
                  onCheckedChange={(enabled) =>
                    void save(
                      "/whatsapp/replies",
                      "PUT",
                      { enabled },
                      enabled
                        ? "Bot replies turned on"
                        : "Bot replies turned off",
                    )
                  }
                />
              </div>
            </Field>
            <p className="help-copy mt-2">
              Turning replies back on only answers new messages. Playground
              stays available. A reply already being sent may still arrive.
            </p>
            {saveError && (
              <div className="mt-4">
                <ErrorNotice error={saveError} />
              </div>
            )}
            {!connected && compact && (
              <p className="help-copy mt-4">
                {guidance[data.session_status || ""] ||
                  "Readiness has not been confirmed. Check the configured session in WAHA."}
              </p>
            )}
            {!compact && (
              <div className="connection-checks">
                {checks.map((check) => (
                  <div
                    className="connection-check"
                    key={check.title}
                    data-state={
                      check.ready === undefined
                        ? "waiting"
                        : check.ready
                          ? "ready"
                          : pending && check.title === "WhatsApp session"
                            ? "waiting"
                            : "blocked"
                    }
                  >
                    {check.ready ? (
                      <CircleCheck />
                    ) : check.ready === undefined ||
                      (pending && check.title === "WhatsApp session") ? (
                      <Clock3 />
                    ) : (
                      <CircleAlert />
                    )}
                    <div>
                      <strong>{check.title}</strong>
                      <p>{check.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {queue && (
              <div className="queue-ledger mt-4">
                {[
                  ["Queued", queue.queued || 0],
                  [
                    "Processing",
                    (queue.generating || 0) + (queue.sending || 0),
                  ],
                  ["Sent", queue.sent || 0],
                  ["Not answered (bot off)", queue.skipped || 0],
                ].map(([name, value]) => (
                  <div key={name}>
                    <strong>{value}</strong>
                    <span>{name}</span>
                  </div>
                ))}
              </div>
            )}
            {attention != null && attention > 0 && (
              <Alert variant="destructive" className="mt-4">
                <CircleAlert />
                <AlertTitle>{attention} messages need attention</AlertTitle>
                <AlertDescription className="flex flex-col items-start gap-3">
                  <span>
                    {data.attention?.failed ?? queue?.failed ?? 0} failed ·{" "}
                    {data.attention?.uncertain ?? queue?.uncertain ?? 0}{" "}
                    delivery uncertain. Check WhatsApp before retrying an
                    uncertain delivery.
                  </span>
                  <span>
                    Ignoring this warning keeps the message history. New
                    failures will still appear.
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={saving || !data.attention?.items.length}
                    onClick={() =>
                      void save(
                        "/whatsapp/attention/ignore",
                        "POST",
                        { items: data.attention?.items },
                        "Warning ignored",
                      )
                    }
                  >
                    Ignore warning
                  </Button>
                </AlertDescription>
              </Alert>
            )}
            {!compact && (
              <dl className="definition-list mt-5">
                <dt>Session</dt>
                <dd>{data.session}</dd>
                <dt>Last received</dt>
                <dd>
                  {data.last_received_at
                    ? date(data.last_received_at)
                    : "Not recorded"}
                </dd>
                <dt>Last reply sent</dt>
                <dd>
                  {data.last_sent_at ? date(data.last_sent_at) : "Not recorded"}
                </dd>
                <dt>Latest receipt</dt>
                <dd>
                  {data.last_ack_at ? date(data.last_ack_at) : "Not recorded"}
                </dd>
              </dl>
            )}
            <p className="help-copy mt-4">
              {error ? "Last successful check" : "Checked"}{" "}
              {data.checked_at || updatedAt
                ? date((data.checked_at || updatedAt)!)
                : "Not reported"}
              . {refreshing ? "Refreshing…" : "Updates automatically."}
            </p>
            {!compact && (
              <p className="help-copy mt-3">
                The WAHA server, backend, and callback network must remain
                available to process customer messages.
              </p>
            )}
          </>
        )
      )}
    </Panel>
  );
}

function JobProgress({ job }: { job: Job }) {
  const [now, setNow] = useState(() => Date.now());
  const live = ["queued", "running"].includes(job.status);
  useEffect(() => {
    if (!live) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [live]);
  const progress = job.progress;
  const total = progress?.total ?? job.result_case_count;
  const completed =
    progress?.completed ??
    (job.status === "completed" ? job.result_case_count : 0) ??
    0;
  const started = progress?.started_at || job.created_at;
  const elapsed = Math.max(
    0,
    Math.floor(
      ((live ? now : new Date(job.updated_at || started).getTime()) -
        new Date(started).getTime()) /
        1000,
    ),
  );
  const phase =
    job.status === "queued"
      ? "queued"
      : live
        ? progress?.phase || job.status
        : job.status;
  const phases = ["preparing", "answering", "scoring", "reporting"];
  const labels: Record<string, string> = {
    queued: "Waiting for the background worker",
    preparing: "Preparing captured knowledge and references",
    answering: job.payload?.rescore_of
      ? "Reusing saved answers and retrieval evidence"
      : "Generating the current case answer",
    indexing: "Synchronizing knowledge passages",
    prepare: "Preparing the captured source list",
    embed: "Embedding and upserting passages",
    verify: "Checking Pinecone visibility",
    query_verify: "Checking synchronized retrieval",
    activate: "Activating synchronized knowledge",
    cleanup: "Scheduling cleanup of unused originals and vectors",
    generating: "Generating conversation candidates from indexed knowledge",
    scoring: "Scoring the answer against its reference",
    reporting: "Saving scores and uploading the report",
    running: "The worker is processing this task",
    completed: "Results saved",
    failed: "Task failed",
    interrupted: "Execution stopped before the next checkpoint",
  };
  return (
    <section
      className="job-progress"
      aria-label={`${jobName(job.kind)} progress`}
    >
      <div className="job-progress-heading">
        <strong>
          {jobName(job.kind)} · {job.id.slice(0, 8)}
        </strong>
        <Status value={job.status} />
      </div>
      <p className="job-case-copy" role="status">
        {labels[phase] || phase}
        {progress?.metric && `: ${progress.metric}`}
      </p>
      <div className="job-progress-count">
        <span>
          {total != null
            ? `${completed} of ${total} ${job.kind === "sync" ? "passages processed" : "cases recorded"}`
            : job.status === "queued"
              ? "Waiting for a checkpoint worker"
              : "This task does not report a case count"}
        </span>
        <span>
          {Math.floor(elapsed / 60)}m {elapsed % 60}s{" "}
          {job.status === "queued" ? "in queue" : "elapsed"}
        </span>
      </div>
      {total != null && total > 0 && (
        <progress
          max={total}
          value={completed}
          aria-label="Recorded evaluation cases"
        />
      )}
      {job.kind === "evaluate" && (
        <ol className="job-stage-list">
          {phases.map((stage, index) => (
            <li key={stage} data-current={stage === phase}>
              {job.status === "completed" || phases.indexOf(phase) > index ? (
                <Check />
              ) : stage === phase ? (
                <Clock3 />
              ) : (
                <Circle />
              )}
              {["Prepare", job.payload?.rescore_of ? "Reuse" : "Answer", "Score", "Report"][index]}
            </li>
          ))}
        </ol>
      )}
      {progress?.case_label && (
        <p className="help-copy">
          Case {progress.case_id}: {progress.case_label}
        </p>
      )}
      {phase === "scoring" && !!progress?.metrics_total && (
        <p className="help-copy">
          {progress.metrics_completed || 0} of {progress.metrics_total} metrics
          recorded for this case.
        </p>
      )}
      {phase === "reporting" && !!progress?.feedback_total && (
        <p className="help-copy">
          {progress.feedback_completed || 0} of {progress.feedback_total} metric
          feedback records sent to LangSmith.
        </p>
      )}
      {!!progress?.errors && (
        <p className="help-copy">
          {progress.errors} cases have an answer or scoring error. Quality
          scores remain separate.
        </p>
      )}
      {job.error && <ErrorNotice error={job.error} />}
      {job.updated_at && (
        <p className="help-copy">
          Last progress update {date(job.updated_at)}.
        </p>
      )}
    </section>
  );
}

function jobCaseCount(job: Job) {
  if (job.progress?.total != null)
    return `${job.progress.completed || 0}/${job.progress.total} cases`;
  if (job.result_case_count != null)
    return `${job.result_case_count} cases saved`;
  return job.status === "queued"
    ? "Waiting for worker"
    : job.status === "running"
      ? "Processing"
      : "Progress not recorded";
}
function JobAction({
  job,
  inspect,
  select,
}: {
  job: Job;
  inspect?: (job: Job) => void;
  select?: (job: Job) => void;
}) {
  if (
    job.error ||
    (job.resumable && ["queued", "running", "interrupted"].includes(job.status))
  )
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="help-copy">{job.error}</p>
        {job.dispatch_error && (
          <p className="help-copy">{job.dispatch_error}</p>
        )}
        {job.resumable && (
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              void action(
                () => api(`/jobs/${job.id}/resume`, { method: "POST" }),
                "Resuming saved work",
              )
            }
          >
            Resume
          </Button>
        )}
        {select && (
          <Button variant="outline" size="sm" onClick={() => select(job)}>
            View progress
          </Button>
        )}
        {job.result_case_count != null && inspect && <Button variant="ghost" size="sm" data-run={job.id} aria-label={`Inspect result for run ${job.id}`} onClick={() => inspect(job)}>Inspect result</Button>}
      </div>
    );
  if (job.result_case_count != null && inspect)
    return (
      <Button variant="ghost" size="sm" data-run={job.id} aria-label={`Inspect result for run ${job.id}`} onClick={() => inspect(job)}>
        Inspect result
      </Button>
    );
  if (select)
    return (
      <Button variant="ghost" size="sm" onClick={() => select(job)}>
        View progress
      </Button>
    );
  return (
    <span className="help-copy">
      {job.has_result
        ? "Saved"
        : ["queued", "running"].includes(job.status)
          ? "In progress"
          : "No saved result"}
    </span>
  );
}

function JobTable({
  jobs,
  inspect,
  select,
}: {
  jobs: Job[];
  inspect?: (job: Job) => void;
  select?: (job: Job) => void;
}) {
  return (
    <>
      <ul className="jobs-mobile" aria-label="Background tasks">
        {jobs.map((job) => (
          <li key={job.id} className="job-mobile-item">
            <div className="job-mobile-heading">
              <strong>{jobName(job.kind)} · {job.id.slice(0, 8)}</strong>
              <Status value={job.status} />
            </div>
            <div className="job-mobile-meta">
              <span>{jobCaseCount(job)}</span>
              <time dateTime={job.created_at}>{date(job.created_at)}</time>
            </div>
            <JobAction job={job} inspect={inspect} select={select} />
          </li>
        ))}
      </ul>
      <Table className="jobs-table">
        <TableHeader>
          <TableRow>
            <TableHead>Task</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Progress</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Result</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id}>
              <TableCell><span className="block font-medium">{jobName(job.kind)}</span><span className="help-copy">{job.id.slice(0, 8)}</span></TableCell>
              <TableCell>
                <Status value={job.status} />
              </TableCell>
              <TableCell>
                <span className="help-copy">{jobCaseCount(job)}</span>
              </TableCell>
              <TableCell className="whitespace-nowrap">
                {date(job.created_at)}
              </TableCell>
              <TableCell>
                <JobAction job={job} inspect={inspect} select={select} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
function Evaluations() {
  const resources = useResource<Job[]>("/jobs", true),
    knowledge = useResource<KnowledgeCatalog>("/knowledge", true),
    dataset = useResource<{
      exists: boolean;
      reviewed: boolean;
      stale?: boolean;
      count: number;
      cases?: unknown[];
    }>("/evaluations/dataset", false),
    qa = useResource<{
      exists: boolean;
      reviewed: boolean;
      count: number;
      held_count: number;
      cases?: unknown[];
    }>("/evaluations/dataset?kind=audited", false);
  const providers = useResource<Providers>("/settings");
  const [kind, setKind] = useState("legacy"),
    [limit, setLimit] = useState(10),
    [resultJobId, setResultJobId] = useState(() => new URLSearchParams(window.location.search).get("run") || ""),
    [datasetOpen, setDatasetOpen] = useState(false),
    [datasetKind, setDatasetKind] = useState("conversations"),
    [busy, setBusy] = useState(false),
    [selectedJobId, setSelectedJobId] = useState(""),
    [resultFilter, setResultFilter] = useState("all");
  const [historyStatus, setHistoryStatus] = useState(() => new URLSearchParams(window.location.search).get("status") || "all");
  const [historyKind, setHistoryKind] = useState(() => new URLSearchParams(window.location.search).get("task") || "all");
  const returnPosition = useRef<{ scroll: number; run: string } | null>(window.history.state?.evaluationReturn || null);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const datasetTrigger = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    const previousRestoration = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";
    const change = () => {
      const params = new URLSearchParams(window.location.search);
      setResultJobId(params.get("run") || "");
      setHistoryStatus(params.get("status") || "all");
      setHistoryKind(params.get("task") || "all");
    };
    window.addEventListener("popstate", change);
    return () => {
      window.removeEventListener("popstate", change);
      window.history.scrollRestoration = previousRestoration;
    };
  }, []);
  useLayoutEffect(() => {
    if (resultJobId) {
      resultHeading.current?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    } else if (returnPosition.current) {
      const { scroll, run } = returnPosition.current;
      document.querySelectorAll<HTMLButtonElement>("button[data-run]").forEach((button) => {
        if (button.dataset.run === run && button.getClientRects().length) button.focus({ preventScroll: true });
      });
      window.scrollTo(0, scroll);
    }
  }, [resultJobId]);
  function filterHistory(key: string, value: string) {
    const url = new URL(window.location.href);
    if (value === "all") url.searchParams.delete(key);
    else url.searchParams.set(key, value);
    window.history.replaceState(window.history.state, "", url);
    if (key === "status") setHistoryStatus(value);
    else setHistoryKind(value);
  }
  function inspectResult(job: Pick<Job, "id">) {
    returnPosition.current = { scroll: window.scrollY, run: job.id };
    window.history.replaceState({ ...window.history.state, evaluationReturn: returnPosition.current }, "");
    const url = new URL(window.location.href);
    url.searchParams.set("run", job.id);
    window.history.pushState({ evaluationResult: true, evaluationReturn: returnPosition.current }, "", url);
    setResultFilter("all");
    setResultJobId(job.id);
  }
  function backToHistory() {
    if (window.history.state?.evaluationResult) window.history.back();
    else {
      const url = new URL(window.location.href);
      url.searchParams.delete("run");
      window.history.replaceState(window.history.state, "", url);
      setResultJobId("");
    }
  }
  const resultResource = useResource<Job>(
    resultJobId ? `/jobs/${encodeURIComponent(resultJobId)}` : null,
    true,
  );
  const savedResult = resultResource.data?.result;
  const result = savedResult && Array.isArray(savedResult.cases) ? evaluationView(savedResult) : undefined;
  const evidence = result ? Object.keys(result.averages || {}).map((name) => metricEvidence(result, name)) : [];
  const scoredMetrics = evidence.reduce((total, item) => total + item.scored, 0);
  const failedMetrics = evidence.reduce((total, item) => total + item.errors, 0);
  async function retryScoring() {
    if (!result || busy) return;
    setBusy(true);
    try {
      const job = await api<{ job_id: string }>(`/evaluations/${encodeURIComponent(result.id)}/rescore`, { method: "POST" });
      const url = new URL(window.location.href);
      url.searchParams.set("run", job.job_id);
      window.history.replaceState(window.history.state, "", url);
      setResultJobId(job.job_id);
      setResultFilter("all");
      resources.reload();
      toast.success("Scoring retry queued. Saved answers and references are preserved.");
    } catch (error) {
      toast.error((error as Error).message);
    } finally { setBusy(false); }
  }
  const reviewData = datasetKind === "audited" ? qa.data : dataset.data;
  const evaluationJobs = (resources.data || []).filter((job) =>
    ["evaluate", "generate", "report"].includes(job.kind),
  );
  const activeJobs = evaluationJobs.filter((job) =>
    ["queued", "running"].includes(job.status),
  );
  const filteredJobs = evaluationJobs.filter((job) =>
    (historyStatus === "all" || job.status === historyStatus) &&
    (historyKind === "all" || job.kind === historyKind),
  );
  const focusedJob = evaluationJobs.find((job) => job.id === selectedJobId);
  const visibleJobs = activeJobs.length
    ? activeJobs
    : focusedJob
      ? [focusedJob]
      : [];
  const activeKnowledge = knowledge.data?.active;
  const referenceReady =
    kind === "legacy" ||
    (kind === "audited" ? qa.data?.reviewed : dataset.data?.reviewed);
  const needsAttention = (row: EvaluationResult["cases"][number]) =>
    !!row.error ||
    row.metrics.length === 0 ||
    row.metrics.some((metric) => metric.error || metric.status === "unavailable" || metric.score == null || metric.passed === false);
  const resultCases =
    result?.cases.filter(
      (row) => resultFilter === "all" || needsAttention(row),
    ) || [];
  const run = async () => {
    if (!activeKnowledge?.chunk_count || !referenceReady) return;
    setBusy(true);
    try {
      const job = await api<{ job_id: string }>("/evaluations", {
        method: "POST",
        body: jsonBody({
          dataset: kind,
          limit,
        }),
      });
      setSelectedJobId(job.job_id);
      resources.reload();
      toast.success("Evaluation queued. Progress will appear above.");
    } catch (error) {
      toast.error((error as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="evaluations-workspace">
      <div hidden={!!resultJobId} className="evaluation-overview">
      {[resources, knowledge, dataset, qa, providers].map((resource, index) =>
        resource.error ? (
          <ErrorNotice
            key={index}
            error={resource.error}
            retry={resource.reload}
          />
        ) : null,
      )}
      {visibleJobs.length > 0 && (
        <Panel
          title={
            activeJobs.length
              ? "Evaluation work in progress"
              : "Selected run progress"
          }
          description="Counts advance after cases are saved. Reporting can continue after the last case is scored."
        >
          {visibleJobs.map((job) => (
            <JobProgress key={job.id} job={job} />
          ))}
        </Panel>
      )}
      <div className="evaluation-setup">
        <Panel
          title="Run an evaluation"
          description="The current synchronized knowledge is captured when you start. This run calls your configured model APIs."
        >
          {!knowledge.data ? (
            !knowledge.error && <Loading label="Loading active knowledge…" />
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void run();
              }}
              className="flex flex-col gap-6"
            >
              <FieldGroup>
                <Field>
                  <FieldLabel>Knowledge base</FieldLabel>
                  <p>
                    {activeKnowledge?.chunk_count
                      ? `Current synchronized knowledge · ${activeKnowledge.chunk_count} passages`
                      : "No searchable knowledge. Add active sources and sync first."}
                  </p>
                  <FieldDescription>
                    Changes synchronized during this run apply to the next
                    evaluation. This run keeps its captured data.
                  </FieldDescription>
                </Field>
                <Field>
                  <FieldLabel htmlFor="evaluation-dataset">Dataset</FieldLabel>
                  <NativeSelect
                    id="evaluation-dataset"
                    value={kind}
                    onChange={(e) => setKind(e.target.value)}
                  >
                    <NativeSelectOption value="legacy">
                      Original 10 questions
                    </NativeSelectOption>
                    <NativeSelectOption
                      value="audited"
                      disabled={!qa.data?.reviewed}
                    >
                      Reviewed QA references (
                      {qa.data ? `${qa.data.count} cases` : "loading…"})
                    </NativeSelectOption>
                    <NativeSelectOption
                      value="conversations"
                      disabled={!dataset.data?.reviewed}
                    >
                      Reviewed conversation scenarios
                    </NativeSelectOption>
                    <NativeSelectOption
                      value="heldout"
                      disabled={!dataset.data?.reviewed}
                    >
                      Held-out conversation scenarios
                    </NativeSelectOption>
                  </NativeSelect>
                </Field>
                <Field>
                  <FieldLabel htmlFor="case-limit">Case limit</FieldLabel>
                  <Input
                    id="case-limit"
                    type="number"
                    min={1}
                    max={40}
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    required
                  />
                  <FieldDescription>
                    One run, with bounded concurrency. Metric failures appear
                    separately from quality scores.
                  </FieldDescription>
                </Field>
              </FieldGroup>
              <div className="help-copy">
                <p>
                  Current knowledge ·{" "}
                  {kind === "legacy"
                    ? "Original questions"
                    : kind === "audited"
                      ? "Reviewed QA"
                      : kind === "heldout"
                        ? "Held-out conversations"
                        : "Reviewed conversations"}{" "}
                  · Up to {limit || 0} cases
                </p>
                <p>
                  Answer: {(providers.data?.answer_provider === "9router" ? providers.data.ninerouter_model : providers.data?.openrouter_model) || "Loading model…"}
                </p>
                <p>
                  Scoring:{" "}
                  {providers.data?.eval_model ? providerModelLabel(providers.data.eval_model) : "Loading scoring model…"}
                </p>
              </div>
              <Button
                type="submit"
                disabled={
                  busy ||
                  !referenceReady ||
                  !activeKnowledge?.chunk_count ||
                  !activeKnowledge.compatible ||
                  !Number.isInteger(limit) ||
                  limit < 1 ||
                  limit > 40
                }
                className="self-start"
              >
                {busy ? (
                  <Spinner data-icon="inline-start" />
                ) : (
                  <FlaskConical data-icon="inline-start" />
                )}
                Run evaluation
              </Button>
            </form>
          )}
        </Panel>
        <div className="evaluation-references">
        <Panel
          title="Conversation scenarios"
          description="Generate candidates from business knowledge, then review their expected outcomes."
        >
          {!dataset.data ? (
            !dataset.error && <Loading label="Loading conversation references…" />
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <Badge variant="outline">{dataset.data.count} scenarios</Badge>
                <Status
                  value={
                    dataset.data.reviewed
                      ? "reviewed"
                      : dataset.data.stale
                        ? "needs reference update"
                        : dataset.data.exists
                          ? "awaiting review"
                          : "not generated"
                  }
                />
              </div>
              <p className="help-copy">
                {dataset.data.stale &&
                  "These candidates include superseded business facts. Correct or regenerate their contexts and expected outcomes before review. "}
                A reserved portion is held out from development runs. Generated
                labels need a human check before scoring.
              </p>
              {!dataset.data.exists ? (
                <Button
                  variant="outline"
                  disabled={!activeKnowledge?.chunk_count}
                  onClick={() =>
                    action(
                      () =>
                        api("/evaluations/generate", {
                          method: "POST",
                          body: jsonBody({}),
                        }),
                      "Dataset generation queued",
                      resources.reload,
                    )
                  }
                >
                  Generate conversation scenarios
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={(event) => {
                    datasetTrigger.current = event.currentTarget;
                    setDatasetKind("conversations");
                    setDatasetOpen(true);
                  }}
                >
                  Review dataset
                </Button>
              )}
            </div>
          )}
        </Panel>
      <Panel
        title="QA reference review"
        description="Review required facts and clarification guidance before comparing chunking configurations."
      >
        {!qa.data ? (
          !qa.error && <Loading label="Loading QA references…" />
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="outline">{qa.data.count} candidate cases</Badge>
              <Badge variant="outline">
                {qa.data.held_count} held for business confirmation
              </Badge>
              <Status
                value={qa.data.reviewed ? "reviewed" : "awaiting review"}
              />
              <Button
                variant="outline"
                onClick={(event) => {
                  datasetTrigger.current = event.currentTarget;
                  setDatasetKind("audited");
                  setDatasetOpen(true);
                }}
              >
                Review QA references
              </Button>
            </div>
            <p className="help-copy mt-4">
              Held cases are excluded. Changes to the reference file invalidate
              its review. The original benchmark remains available separately.
            </p>
          </>
        )}
      </Panel>
        </div>
      </div>
      <Panel
        title="Evaluation history"
        description="Inspect case scores, download results, and open the corresponding LangSmith experiment."
      >
        <EvaluationMethodGuide />
        <div className="evaluation-history-filters">
          <Field><FieldLabel htmlFor="history-status">Run status</FieldLabel>
            <NativeSelect id="history-status" value={historyStatus} onChange={(event) => filterHistory("status", event.target.value)}>
              <NativeSelectOption value="all">All statuses</NativeSelectOption>
              {["completed", "failed", "interrupted", "queued", "running"].map((status) => <NativeSelectOption key={status} value={status}>{status[0].toUpperCase() + status.slice(1)}</NativeSelectOption>)}
            </NativeSelect>
          </Field>
          <Field><FieldLabel htmlFor="history-kind">Task type</FieldLabel>
            <NativeSelect id="history-kind" value={historyKind} onChange={(event) => filterHistory("task", event.target.value)}>
              <NativeSelectOption value="all">All evaluation work</NativeSelectOption>
              <NativeSelectOption value="evaluate">Evaluation</NativeSelectOption>
              <NativeSelectOption value="generate">Dataset generation</NativeSelectOption>
              <NativeSelectOption value="report">Reporting</NativeSelectOption>
            </NativeSelect>
          </Field>
          <p className="help-copy" role="status">{resources.data ? `${filteredJobs.length} of ${evaluationJobs.length} runs` : "Loading runs…"}</p>
        </div>
        {!resources.data ? (
          !resources.error && <Loading label="Loading evaluation history…" />
        ) : filteredJobs.length ? (
          <JobTable
            jobs={filteredJobs}
            inspect={inspectResult}
            select={(job) => {
              setSelectedJobId(job.id);
              window.scrollTo({ top: 0, behavior: "instant" });
            }}
          />
        ) : (
          <NoItems
            title={evaluationJobs.length ? "No runs match these filters" : "No evaluation runs yet"}
            description={evaluationJobs.length ? "Choose another status or task type to see saved runs." : "Run the original questions to establish an answer quality reference."}
            icon={FlaskConical}
          />
        )}
      </Panel>
      </div>
      {resultJobId && <header className="evaluation-result-heading">
        <Button variant="outline" className="self-start" onClick={backToHistory}>Back to evaluation history</Button>
        <div><h2 ref={resultHeading} tabIndex={-1}>Run {resultJobId.slice(0, 8)}</h2><p className="help-copy break-words">{resultJobId}</p></div>
        {resultResource.data && <div className="flex flex-wrap items-center gap-3"><Status value={resultResource.data.status} /><span className="help-copy">Started {date(resultResource.data.created_at)}</span></div>}
      </header>}
      {resultResource.error && (
        <ErrorNotice
          error={resultResource.error}
          retry={resultResource.reload}
        />
      )}
      {resultJobId && !resultResource.data && !resultResource.error && (
        <Loading label="Loading saved evaluation results…" />
      )}
      {resultJobId && resultResource.data && !result && <Panel title="No saved evaluation result" description="This task has not saved case results. Review its progress and any errors before starting another run."><JobProgress job={resultResource.data} /></Panel>}
      {result && (
        <Panel
          title="Recorded quality metrics"
          description={`${result.cases.length} recorded cases${result.chunking ? ` · Chunking ${result.chunking.chunk_size}/${result.chunking.chunk_overlap}` : " · Historical configuration"}`}
          action={
            <Button variant="outline" size="sm" asChild>
              <a href={`/admin/api/evaluations/${result.id}/export`} download>
                Export JSON
              </a>
            </Button>
          }
        >
          {failedMetrics > 0 && <Alert variant="destructive" className="mb-6">
            <AlertTitle>{scoredMetrics === 0 ? "Scoring failed for this run" : "Only part of this run was scored"}</AlertTitle>
            <AlertDescription>
              <p>{failedMetrics} metric requests failed. A completed job means processing ended; it does not mean the judge produced valid scores.</p>
              {result.scoring_error && <p>{result.scoring_error}</p>}
              {["legacy", "audited"].includes(result.dataset) && result.cases.every((row) => row.answer && row.expected_output && !row.error) && <>
                <p>Retry scoring keeps available scores and uses the original saved answers, contexts, references and judge for missing or failed metrics. It creates a new run and calls the scoring API.</p>
                <Button variant="outline" disabled={busy || ["queued", "running"].includes(resultResource.data?.status || "")} onClick={() => void retryScoring()}>{busy && <Spinner data-icon="inline-start" />}Retry scoring</Button>
              </>}
            </AlertDescription>
          </Alert>}
          {result.rescore_of && <p className="help-copy mb-5">Scoring retry of run {result.rescore_of}. Original answers and retrieval evidence were reused.</p>}
          {result.reporting_note && <p className="help-copy mb-5">{result.reporting_note}</p>}
          <dl className="evaluation-provenance">
            <div><dt>Dataset</dt><dd>{result.dataset}</dd></div>
            <div><dt>Knowledge snapshot</dt><dd>{result.knowledge_version || "Not recorded"}</dd></div>
            <div><dt>Answering model</dt><dd>{result.model || "Not recorded"}</dd></div>
            <div><dt>Scoring model</dt><dd>{result.judge ? providerModelLabel(result.judge) : "Not recorded"}</dd></div>
          </dl>
          <p className="help-copy mb-4">Scores average only the cases with a recorded score. Missing scores remain unavailable.</p>
          <div className="evaluation-metrics">
            {Object.entries(result.averages || {}).map(([name, score]) => {
              const stats = metricEvidence(result, name);
              return (
              <div className="evaluation-average" key={name}>
                <strong>{score == null && stats.errors ? "Scoring failed" : percentage(score)}</strong>
                <span>{name}</span>
                <span>{stats.scored}/{stats.total} case scores · {stats.errors} errors</span>
                {stats.borderline > 0 && <span>{stats.borderline} borderline verdicts counted as accepted. Review the case evidence.</span>}
                {stats.standardError !== null && <span>Standard error: {(stats.standardError * 100).toFixed(1)} percentage points</span>}
                {stats.interval && <span>Approx. 95% interval: {percentage(stats.interval[0])}–{percentage(stats.interval[1])}</span>}
              </div>
            );})}
          </div>
          <p className="help-copy mt-3">These are benchmark means, not confidence that an answer is correct. {result.cases.length < 30 ? "Small benchmark: use more independently reviewed cases before drawing broad conclusions. " : "Intervals assume independent, representative cases and exclude judge calibration uncertainty. "}Missing scores can bias the mean. Validate judge decisions against human review.</p>
          <EvaluationMath result={result} />
          <h3 className="evaluation-evidence-title">Case evidence</h3>
          <Field className="mt-5 max-w-xs">
            <FieldLabel htmlFor="result-filter">Cases to inspect</FieldLabel>
            <NativeSelect
              id="result-filter"
              value={resultFilter}
              onChange={(event) => setResultFilter(event.target.value)}
            >
              <NativeSelectOption value="all">
                All cases ({result.cases.length})
              </NativeSelectOption>
              <NativeSelectOption value="attention">
                Need attention ({result.cases.filter(needsAttention).length})
              </NativeSelectOption>
            </NativeSelect>
          </Field>
          <p className="help-copy mt-3">
            A low quality score is a scored result. Answer and metric errors are
            reported separately.
          </p>
          {result.reporting_error && (
            <Alert className="mt-5">
              <AlertTitle>Scores saved locally</AlertTitle>
              <AlertDescription>
                LangSmith reporting needs a retry. This will reuse the scores.
              </AlertDescription>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  action(
                    () =>
                      api(`/evaluations/${result.id}/report`, {
                        method: "POST",
                      }),
                    "Reporting retry queued",
                    resources.reload,
                  )
                }
              >
                Retry report
              </Button>
            </Alert>
          )}
          {result.experiment_url && (
            <Button className="mt-5" variant="outline" asChild>
              <a href={result.experiment_url} target="_blank" rel="noreferrer">
                Open LangSmith experiment
                <ArrowUpRight data-icon="inline-end" />
              </a>
            </Button>
          )}
          <div className="flex flex-col gap-3 mt-6">
            {resultCases.map((row) => (
              <details className="evaluation-case" key={row.id}>
                <summary>
                  <span><small className="evaluation-case-id">Case {row.id}</small>{row.input || row.scenario || "Question not recorded"}</span>
                  <Badge variant="outline">
                    {row.error
                      ? "Answer error"
                      : row.metrics.some((metric) => metric.error)
                        ? "Scoring error"
                        : row.metrics.some((metric) => metric.status === "unavailable")
                          ? "Annotations needed"
                        : row.metrics.length === 0
                          ? "Not scored"
                          : `${row.metrics.filter((metric) => metric.passed).length}/${row.metrics.filter((metric) => metric.passed != null).length} threshold checks passed`}
                  </Badge>
                </summary>
                <div className="evaluation-answer-reference">
                  <section><h4>Recorded answer</h4><p className="passage-text">{row.answer ? displayAnswer(row.answer) : row.turns?.length ? "See the recorded conversation below." : "No answer was recorded for this case."}</p></section>
                {(row.expected_output || row.expected_outcome) && (
                  <section>
                    <h4>Reference answer / expected outcome</h4>
                    <p>{row.expected_output || row.expected_outcome}</p>
                  </section>
                )}
                </div>
                {row.trace_url && <Button variant="outline" size="sm" asChild><a href={row.trace_url} target="_blank" rel="noreferrer">Open case trace<ArrowUpRight data-icon="inline-end" /></a></Button>}
                {!!row.retrieval_context?.length && <details className="metric-detail evaluation-passages">
                  <summary>Retrieved evidence ({row.retrieval_context.length} passages)</summary>
                  <ol>{row.retrieval_context.map((passage, index) => <li key={index}><h4>Passage {index + 1}{passage.metadata?.source ? ` · ${String(passage.metadata.source)}` : ""}</h4><p>{passage.text}</p></li>)}</ol>
                </details>}
                {row.turns && (
                  <div className="flex flex-col gap-4 mt-4">
                    {row.turns.map((turn, index) => (
                      <Message
                        key={index}
                        align={turn.role === "user" ? "end" : "start"}
                      >
                        <MessageContent>
                          <MessageHeader>
                            {turn.role === "user" ? "Customer" : "Chatbot"}
                          </MessageHeader>
                          <Bubble variant="muted">
                            <BubbleContent>
                              <p className="whitespace-pre-wrap">
                                {turn.role === "assistant"
                                  ? displayAnswer(turn.content)
                                  : turn.content}
                              </p>
                            </BubbleContent>
                          </Bubble>
                        </MessageContent>
                      </Message>
                    ))}
                  </div>
                )}
                {row.error && <ErrorNotice error={row.error} />}
                {row.metrics.map((metric) => (
                  <details className="metric-detail" key={metric.name}>
                    <summary className="flex min-h-11 cursor-pointer items-center justify-between gap-3">
                      <strong>{metric.name}</strong>
                      <Badge variant={metric.error ? "destructive" : "outline"}>
                        {metric.error
                          ? "Scoring error"
                          : metric.status === "unavailable" ? "Annotations needed"
                          : percentage(metric.score)}
                      </Badge>
                    </summary>
                    <p>{metric.reason || metric.error || "No scoring explanation was recorded."}</p>
                    {metric.threshold != null && <p>Pass threshold: {percentage(metric.threshold)} · {metric.passed == null ? "No threshold verdict" : metric.passed ? "Passed" : "Below threshold"}</p>}
                    <MetricMath metric={metric} />
                  </details>
                ))}
              </details>
            ))}
            {resultCases.length === 0 && (
              <NoItems
                title={
                  resultFilter === "attention"
                    ? "No cases need attention"
                    : "No case results were saved"
                }
                description={
                  resultFilter === "attention"
                    ? "All recorded case metrics have scores, with no failed thresholds or answer and scoring errors."
                    : "This run did not record case results. Inspect its progress and error details before starting another run."
                }
                icon={Check}
              />
            )}
          </div>
        </Panel>
      )}
      {reviewData && (
        <Dialog open={datasetOpen} onOpenChange={setDatasetOpen}>
          <DialogContent className="sm:max-w-4xl" onCloseAutoFocus={(event) => {
            event.preventDefault();
            datasetTrigger.current?.focus();
          }}>
            <DialogHeader>
              <DialogTitle>
                {datasetKind === "audited"
                  ? "Review QA references"
                  : "Review conversation scenarios"}
              </DialogTitle>
              <DialogDescription>
                Check business facts and expected outcomes. Edit
                {datasetKind === "audited"
                  ? " testing/evals/qa-reference-candidates.json"
                  : " testing/evals/.dataset.json"}{" "}
                locally if corrections are needed; changes invalidate the
                review.
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[55dvh] overflow-y-auto">
              {(reviewData.cases || []).map((item, index) => {
                const row = item as Record<string, unknown>;
                return (
                  <article
                    className="reference-case"
                    key={String(row.id || index)}
                  >
                    <h3>
                      {String(
                        row.question ||
                          row.scenario ||
                          row.input ||
                          `Reference ${index + 1}`,
                      )}
                    </h3>
                    {row.review_status === "hold" && (
                      <Status value="Held for confirmation" />
                    )}
                    <dl>
                      {[
                        ["ground_truth", "Reference answer"],
                        ["expected_outcome", "Expected outcome"],
                        ["review_notes", "Review guidance"],
                        ["context", "Source context"],
                      ]
                        .filter(([key]) => row[key] != null)
                        .map(([key, label]) => (
                          <div key={key}>
                            <dt>{label}</dt>
                            <dd>
                              {typeof row[key] === "string"
                                ? (row[key] as string)
                                : JSON.stringify(row[key], null, 2)}
                            </dd>
                          </div>
                        ))}
                    </dl>
                  </article>
                );
              })}
            </div>
            <details className="advanced-settings">
              <summary>View source JSON</summary>
              <pre className="dataset-preview">
                {JSON.stringify(reviewData.cases, null, 2)}
              </pre>
            </details>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDatasetOpen(false)}>
                Close
              </Button>
              <Button
                disabled={
                  datasetKind === "conversations" && dataset.data?.stale
                }
                onClick={() =>
                  action(
                    () =>
                      api(`/evaluations/dataset/review?kind=${datasetKind}`, {
                        method: "POST",
                      }),
                    "Dataset marked reviewed",
                    () => {
                      dataset.reload();
                      qa.reload();
                      setDatasetOpen(false);
                    },
                  )
                }
              >
                {datasetKind === "audited"
                  ? "I reviewed the non-held references"
                  : "I reviewed these scenarios"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function WorkspaceLink({
  item,
  active,
  navigate,
}: {
  item: (typeof pages)[number];
  active: boolean;
  navigate: (name: string) => void;
}) {
  const { setOpenMobile } = useSidebar();
  const prefetch = () => {
    const path = {
      Dashboard: "/overview",
      Knowledge: "/knowledge",
      Catalog: "/catalog",
      Playground: "/knowledge",
      Conversations: "/conversations?channel=whatsapp",
      Providers: "/settings",
      Evaluations: "/jobs",
    }[item.name];
    if (!active && path) void prefetchResource(path);
  };
  return (
    <SidebarMenuButton asChild isActive={active} tooltip={item.name}>
      <a
        href={adminPagePath(item.name)}
        aria-current={active ? "page" : undefined}
        aria-label={item.name}
        onPointerEnter={prefetch}
        onFocus={prefetch}
        onClick={(event) => {
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
            return;
          event.preventDefault();
          navigate(item.name);
          setOpenMobile(false);
        }}
      >
        <item.icon />
        <span>{item.name}</span>
      </a>
    </SidebarMenuButton>
  );
}
function CloseMobileSidebar() {
  const { setOpenMobile } = useSidebar();
  return (
    <Button
      className="mobile-sidebar-close"
      variant="ghost"
      size="icon"
      aria-label="Close navigation"
      onClick={() => setOpenMobile(false)}
    >
      <X />
    </Button>
  );
}
function WorkspaceBrand({ navigate }: { navigate: (name: string) => void }) {
  const { setOpenMobile } = useSidebar();
  return (
    <a
      className="workspace-brand"
      href={adminPagePath("Dashboard")}
      aria-label="Asia Visual Grafika dashboard"
      title="Asia Visual Grafika"
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
          return;
        event.preventDefault();
        navigate("Dashboard");
        setOpenMobile(false);
      }}
    >
      <BrandMark />
      <span className="brand-name">
        <strong>Asia Visual Grafika</strong>
        <small>Chatbot workspace</small>
      </span>
    </a>
  );
}
function WorkspaceTools({
  title,
  navigate,
  navigationTrigger,
}: {
  title: string;
  navigate: (name: string) => void;
  navigationTrigger: RefObject<HTMLButtonElement | null>;
}) {
  const { isMobile, state } = useSidebar();
  const searchTrigger = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false),
    [search, setSearch] = useState("");
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  const matches = pages
    .filter((item) =>
      (item.name + " " + descriptions[item.name])
        .toLowerCase()
        .includes(search.toLowerCase()),
    )
    .sort(
      (a, b) =>
        Number(b.name.toLowerCase().includes(search.toLowerCase())) -
        Number(a.name.toLowerCase().includes(search.toLowerCase())),
    );
  return (
    <>
      <SidebarTrigger
        ref={navigationTrigger}
        aria-label={
          isMobile
            ? "Open navigation menu"
            : state === "expanded"
              ? "Collapse navigation"
              : "Expand navigation"
        }
        title="Toggle navigation (Ctrl or Command + B)"
      />
      {isMobile && <span className="help-copy">Menu</span>}
      <div className="workspace-breadcrumb">
        <span>Workspace</span>
        <span>/</span>
        <strong>{title}</strong>
      </div>
      <Button
        ref={searchTrigger}
        className="workspace-search"
        variant="ghost"
        aria-label="Search workspace pages"
        onClick={() => setOpen(true)}
      >
        <Search data-icon="inline-start" />
        <span>Search workspace</span>
        <kbd>⌘ K</kbd>
      </Button>
      <ThemeButton />
      <Dialog
        open={open}
        onOpenChange={(value) => {
          setOpen(value);
          if (!value) setSearch("");
        }}
      >
        <DialogContent
          onCloseAutoFocus={(event) => {
            event.preventDefault();
            searchTrigger.current?.focus();
          }}
        >
          <DialogHeader>
            <DialogTitle>Go to a workspace page</DialogTitle>
            <DialogDescription>
              Search the page name or the task you want to complete.
            </DialogDescription>
          </DialogHeader>
          <Field>
            <FieldLabel htmlFor="workspace-search">Find a page</FieldLabel>
            <Input
              id="workspace-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Knowledge, conversations, evaluations…"
            />
          </Field>
          <nav aria-label="Workspace search results">
            {matches.map((item) => (
              <button
                key={item.name}
                className="navigation-result"
                onClick={() => {
                  navigate(item.name);
                  setOpen(false);
                  setSearch("");
                }}
              >
                <item.icon />
                <span>
                  <strong>{item.name}</strong>
                  <small>{descriptions[item.name]}</small>
                </span>
              </button>
            ))}
          </nav>
          {matches.length === 0 && (
            <NoItems
              title="No pages match this search"
              description="Try the page name, or clear the search to show all workspace pages."
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
function readPage() {
  return readAdminPage(window.location);
}

function Workspace() {
  const navigationTrigger = useRef<HTMLButtonElement>(null);
  const [auth, setAuth] = useState<AdminSession | null | undefined>(undefined),
    [page, setPage] = useState(readPage);
  const session = useQuery({
    queryKey: resourceKey("/me"),
    queryFn: async ({ signal }) => {
      const user = await api<AdminSession>("/me", { signal });
      if (!signal.aborted) setCsrf(user.csrf);
      return user;
    },
    enabled: (query) => auth === undefined && query.state.data === undefined,
    staleTime: 0,
    gcTime: 0,
    retry: (_failures, error) => isTransientReadError(error),
  });
  const user = auth === undefined ? session.data : auth;
  const signedIn = user
    ? true
    : auth === null ||
        (session.error instanceof ApiError && session.error.status === 401)
      ? false
      : null;
  const username = user?.username || "";
  const clearSession = () => {
    queryClient.clear();
    setCsrf("");
    setAuth(null);
  };
  const navigate = (name: string) => {
    if (window.location.pathname !== adminPagePath(name) || window.location.search) {
      window.history.pushState(null, "", adminPagePath(name));
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
    setPage(name);
    window.scrollTo(0, 0);
  };
  useEffect(() => {
    const expired = () => clearSession();
    const change = () => {
      const name = readPage();
      if (window.location.pathname !== "/admin/login")
        window.history.replaceState(
          window.history.state,
          "",
          adminPagePath(name) + window.location.search,
        );
      setPage(name);
    };
    change();
    window.addEventListener("auth-expired", expired);
    window.addEventListener("hashchange", change);
    window.addEventListener("popstate", change);
    return () => {
      window.removeEventListener("auth-expired", expired);
      window.removeEventListener("hashchange", change);
      window.removeEventListener("popstate", change);
    };
  }, []);
  const title = pages.find((p) => p.name === page)?.name || "Dashboard";
  useEffect(() => {
    document.title = `${signedIn ? title : "Sign in"} · Asia Visual Grafika`;
  }, [title, signedIn]);
  return (
    <TooltipProvider>
      <Toaster richColors />
      {signedIn === null ? (
        <main className="p-12">
          {session.error ? (
            <ErrorNotice
              error={session.error.message}
              retry={() => void session.refetch()}
            />
          ) : (
            <Loading
              label={
                session.isPaused
                  ? "You're offline. Your workspace will reconnect when you're back online."
                  : session.failureCount
                    ? "Reconnecting to your workspace. Retrying automatically…"
                    : "Loading workspace data…"
              }
            />
          )}
        </main>
      ) : !signedIn ? (
        <Login
          onLogin={(user) => {
            queryClient.clear();
            window.history.replaceState(
              null,
              "",
              adminPagePath(page) + window.location.search,
            );
            setAuth(user);
          }}
        />
      ) : (
        <SidebarProvider
          defaultOpen={false}
          style={
            {
              "--sidebar-width": "248px",
              "--sidebar-width-icon": "72px",
            } as CSSProperties
          }
        >
          <a
            className="skip-link"
            href="#workspace-content"
            onClick={(event) => {
              event.preventDefault();
              document.getElementById("workspace-content")?.focus();
            }}
          >
            Skip to content
          </a>
          <Sidebar
            collapsible="icon"
            onCloseAutoFocus={(event) => {
              event.preventDefault();
              navigationTrigger.current?.focus();
            }}
          >
            <SidebarHeader>
              <WorkspaceBrand navigate={navigate} />
              <CloseMobileSidebar />
            </SidebarHeader>
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupLabel>Workspace</SidebarGroupLabel>
                <nav aria-label="Main navigation">
                  <SidebarMenu>
                    {pages.map((p) => (
                      <SidebarMenuItem key={p.name}>
                        <WorkspaceLink
                          item={p}
                          active={title === p.name}
                          navigate={navigate}
                        />
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </nav>
              </SidebarGroup>
            </SidebarContent>
            <SidebarFooter>
              <div className="sidebar-note">
                <div className="sidebar-note-copy">
                  <strong>WhatsApp customer support</strong>
                  <p>
                    Prepare and review answers here. Customers use WhatsApp.
                  </p>
                </div>
              </div>
              <div className="account-line">
                <span className="account-initial" aria-hidden="true">
                  {username.slice(0, 2)}
                </span>
                <span className="account-details">
                  <strong>{username}</strong>Administrator
                </span>
              </div>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    tooltip="Sign out"
                    aria-label="Sign out"
                    onClick={() =>
                      action(
                        () => api("/logout", { method: "POST" }),
                        "Signed out",
                        clearSession,
                      )
                    }
                  >
                    <LogOut />
                    <span>Sign out</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarFooter>
          </Sidebar>
          <SidebarInset>
            <header className="workspace-header">
              <WorkspaceTools
                title={title}
                navigate={navigate}
                navigationTrigger={navigationTrigger}
              />
            </header>
            <main
              className="workspace-main"
              id="workspace-content"
              tabIndex={-1}
            >
              <div className="page-intro">
                <h1>{title}</h1>
                <p>{descriptions[title]}</p>
              </div>
              {title === "Dashboard" ? (
                <Dashboard navigate={navigate} />
              ) : title === "Knowledge" ? (
                <KnowledgePage testKnowledge={() => navigate("Playground")} />
              ) : title === "Catalog" ? (
                <CatalogPage />
              ) : title === "Playground" ? (
                <Playground />
              ) : title === "Conversations" ? (
                <Conversations />
              ) : title === "Providers" ? (
                <ProvidersPage />
              ) : (
                <Evaluations />
              )}
            </main>
          </SidebarInset>
        </SidebarProvider>
      )}
    </TooltipProvider>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Workspace />
    </QueryClientProvider>
  );
}
