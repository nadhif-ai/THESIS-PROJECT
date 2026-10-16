import { useEffect, useRef, useState } from "react";
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
  Plus,
  Upload,
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
import brandMark from "@/assets/brand-mark.png";
import printingDesk from "@/assets/printing-desk.jpg";
import { api, ApiError, jsonBody, setCsrf } from "@/lib/api";
import { adminPagePath, readAdminPage } from "@/lib/admin-navigation";
import { isTransientReadError, queryClient, resourceKey } from "@/lib/query-client";
import { prefetchResource, useResource } from "@/hooks/use-resource";
import type {
  AdminSession,
  Version,
  Answer,
  Job,
  Conversation,
  EvaluationResult,
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
const percentage = (value?: number | null) =>
  value == null ? "Not scored" : `${Math.round(value * 100)}%`;
const descriptions: Record<string, string> = {
  Dashboard:
    "Published knowledge, customer activity, and work that needs attention.",
  Knowledge:
    "Prepare a draft, check its sources, and publish a reviewed version.",
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
  published: Version;
  baseline: { cases: number; hit_rate: number; precision: number };
  recent: Conversation[];
  jobs: Job[];
};
function Dashboard({ navigate }: { navigate: (page: string) => void }) {
  const { data, error, reload } = useResource<Overview>("/overview", true);
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!data)
    return <Loading label="Loading published knowledge and recent activity…" />;
  const activeJobs = data.jobs.filter((job) =>
    ["queued", "running"].includes(job.status),
  );
  return (
    <div className="page-section">
      {error && <ErrorNotice error={error} retry={reload} />}
      <section className="overview-proof" aria-label="Published knowledge">
        <div>
          <h2>Knowledge available to customer replies</h2>
          <div className="proof-record">
            <Status value={data.published.status} />
            <span>
              <strong>{data.published.manifest.files.length}</strong> documents
            </span>
            <span>
              <strong>{data.published.chunk_count}</strong> indexed passages
            </span>
            <span>Version {data.published.id.slice(-6)}</span>
          </div>
        </div>
        <Button onClick={() => navigate("Playground")}>
          Test a customer question
        </Button>
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
      <div className="stat-strip">
        <div>
          <span>Recorded WhatsApp replies</span>
          <strong>{data.whatsapp_messages}</strong>
        </div>
        <div>
          <span>Replies across all channels</span>
          <strong>{data.conversations}</strong>
        </div>
        <div>
          <span>Average recorded response</span>
          <strong>
            {data.average_latency != null
              ? `${data.average_latency}s`
              : "Not recorded"}
          </strong>
        </div>
      </div>
      <p className="help-copy">
        Activity totals and response time use all stored replies.
      </p>
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
                        {r.question}
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
          </Panel>
        </div>
        <Panel
          title="Retrieval reference"
          description={`${data.baseline.cases} original questions, evaluated at k=3`}
        >
          <div className="baseline-values">
            <div>
              <strong>{data.baseline.hit_rate}%</strong>
              <span>Hit rate</span>
            </div>
            <div>
              <strong>{percentage(data.baseline.precision)}</strong>
              <span>Source precision</span>
            </div>
          </div>
          <p className="help-copy mt-4">
            These scores measure source retrieval. DeepEval adds answer quality
            and conversation evaluation.
          </p>
          <Button
            variant="outline"
            className="mt-5"
            onClick={() => navigate("Evaluations")}
          >
            Open evaluations
          </Button>
        </Panel>
      </div>
      {data.jobs.length > 0 && (
        <Panel title="Background work">
          <JobTable jobs={data.jobs} />
        </Panel>
      )}
    </div>
  );
}

function VersionSelect({
  versions,
  value,
  onChange,
  readyOnly = false,
}: {
  versions: Version[];
  value: string;
  onChange: (id: string) => void;
  readyOnly?: boolean;
}) {
  return (
    <NativeSelect
      aria-label="Knowledge version"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {versions
        .filter((v) => !readyOnly || (v.compatible && ["ready", "published"].includes(v.status)))
        .map((v) => (
          <NativeSelectOption key={v.id} value={v.id}>
            {v.manifest.archived ? "Archived" : v.status === "published"
              ? "Published"
              : v.status === "ready"
                ? "Ready"
                : "Draft"}{" "}
            · {date(v.created_at)} · {v.id.slice(-6)}
            {v.chunking &&
              ` · ${v.chunking.chunk_size}/${v.chunking.chunk_overlap}`}
          </NativeSelectOption>
        ))}
    </NativeSelect>
  );
}
function ChunkingSettings({
  version,
  reload,
}: {
  version: Version;
  reload: () => void;
}) {
  const [size, setSize] = useState(version.chunking.chunk_size),
    [overlap, setOverlap] = useState(version.chunking.chunk_overlap),
    [busy, setBusy] = useState(false);
  const editable = !version.manifest.archived && ["draft", "failed"].includes(version.status);
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    await action(
      () =>
        api(`/versions/${version.id}/chunking`, {
          method: "PUT",
          body: jsonBody({ chunk_size: size, chunk_overlap: overlap }),
        }),
      "Chunking saved. Index this draft to apply it.",
      reload,
    );
    setBusy(false);
  }
  return (
    <Panel
      title="Passage configuration"
      description="Sizes use characters. New indexing preserves section headings and checks the embedding input limit."
    >
      <form onSubmit={save} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field>
            <FieldLabel htmlFor="chunk-size">Chunk size</FieldLabel>
            <Input
              id="chunk-size"
              type="number"
              min={400}
              max={2000}
              value={size}
              disabled={!editable}
              onChange={(e) => setSize(Number(e.target.value))}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="chunk-overlap">Overlap</FieldLabel>
            <Input
              id="chunk-overlap"
              type="number"
              min={0}
              max={Math.min(400, size - 1)}
              value={overlap}
              disabled={!editable}
              onChange={(e) => setOverlap(Number(e.target.value))}
            />
          </Field>
        </div>
        <p className="help-copy">
          {version.chunking.preprocessing === "legacy"
            ? "Historical passages use the original splitting process. Create a draft to use section-based splitting."
            : "Overlap applies within each section. Product headings are retained in each passage."}
          {version.manifest.index_statistics &&
            ` Maximum passage ${version.manifest.index_statistics.token_count_method === "utf8_upper_bound" ? "token upper bound" : "tokens"}: ${version.manifest.index_statistics.max_tokens} (limit ${version.manifest.index_statistics.embedding_token_limit}).`}
        </p>
        {editable && (
          <Button type="submit" disabled={busy} className="self-start">
            {busy && <Spinner />}Save chunking
          </Button>
        )}
      </form>
    </Panel>
  );
}

function Knowledge({
  versionId,
  onVersionChange,
  testVersion,
}: {
  versionId: string;
  onVersionChange: (id: string) => void;
  testVersion: (id: string) => void;
}) {
  const { data, error, reload } = useResource<{
    versions: Version[];
    published: string;
  }>("/versions", true);
  const [selected, setSelected] = useState(versionId),
    [file, setFile] = useState<{
      name: string;
      content: string | null;
      editable: boolean;
    } | null>(null),
    [editOpen, setEditOpen] = useState(false),
    [newName, setNewName] = useState(""),
    [saving, setSaving] = useState(false),
    [publishOpen, setPublishOpen] = useState(false),
    [passages, setPassages] = useState<
      { id: string; text: string; metadata: Record<string, unknown> }[] | null
    >(null);
  const current =
    data?.versions.find((v) => v.id === selected) || data?.versions[0];
  async function draft() {
    if (!current) return;
    try {
      const v = await api<Version>("/versions", {
        method: "POST",
        body: jsonBody({ base_id: current.id }),
      });
      setSelected(v.id);
      reload();
      toast.success("Draft created. Customer knowledge stays published.");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  async function upload(files: FileList | null) {
    if (!current || !files?.[0]) return;
    const form = new FormData();
    form.append("file", files[0]);
    await action(
      () =>
        api(`/versions/${current.id}/upload`, { method: "POST", body: form }),
      "File added to the draft",
      reload,
    );
  }
  async function edit(name: string) {
    if (!current) return;
    try {
      setFile(
        await api(`/versions/${current.id}/files/${encodeURIComponent(name)}`),
      );
      setEditOpen(true);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  async function save() {
    if (!current || !file) return;
    setSaving(true);
    try {
      await api(`/versions/${current.id}/files`, {
        method: "PUT",
        body: jsonBody({ name: file.name, content: file.content }),
      });
      setEditOpen(false);
      reload();
      toast.success("Draft saved");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  if (error && !data) return <ErrorNotice error={error} retry={reload} />;
  if (!data)
    return <Loading label="Loading knowledge versions and documents…" />;
  if (!current)
    return (
      <NoItems
        title="No knowledge versions yet"
        description="Ask the workspace administrator to initialize the starting business documents."
      />
    );
  const editable = !current.manifest.archived && ["draft", "failed"].includes(current.status);
  return (
    <div className="flex flex-col gap-6">
      {error && <ErrorNotice error={error} retry={reload} />}
      <div className="knowledge-toolbar">
        <Field className="max-w-md">
          <FieldLabel>Knowledge version</FieldLabel>
          <VersionSelect
            versions={data.versions}
            value={current.id}
            onChange={(id) => {
              setSelected(id);
              onVersionChange(id);
              setFile(null);
            }}
          />
        </Field>
        <div className="flex flex-wrap gap-2">
          {current.compatible && ["ready", "published"].includes(current.status) && (
            <Button
              onClick={() => testVersion(current.id)}
              variant={current.status === "ready" ? "default" : "outline"}
            >
              Test this version
            </Button>
          )}
          {["ready", "published"].includes(current.status) && (
            <Button
              variant="outline"
              onClick={() =>
                api<
                  {
                    id: string;
                    text: string;
                    metadata: Record<string, unknown>;
                  }[]
                >(`/versions/${current.id}/chunks`)
                  .then(setPassages)
                  .catch((e) => toast.error(e.message))
              }
            >
              Inspect passages
            </Button>
          )}

          <Button variant="outline" onClick={draft}>
            <Plus data-icon="inline-start" />
            Create draft
          </Button>
          {editable && (
            <Button
              onClick={() =>
                action(
                  () =>
                    api(`/versions/${current.id}/index`, { method: "POST" }),
                  "Indexing queued",
                  reload,
                )
              }
            >
              <Database data-icon="inline-start" />
              Index draft
            </Button>
          )}
          {current.compatible && current.status === "ready" && (
            <Button variant="outline" onClick={() => setPublishOpen(true)}>
              <Check data-icon="inline-start" />
              Publish to WhatsApp
            </Button>
          )}
        </div>
      </div>
      <Alert>
        <Database />
        <AlertTitle>
          {current.manifest.archived ? "Historical knowledge archive" : current.status === "published"
            ? "Customers use this published version"
            : current.status === "ready"
              ? "Ready to test before publishing"
              : current.status === "indexing"
                ? "Indexing this draft"
                : "Prepare a separate draft"}
        </AlertTitle>
        <AlertDescription>
          {current.manifest.archived
            ? "This snapshot is read-only and retains its earlier evaluation results. Create a new draft to edit and reindex it."
            : editable
            ? "Add or edit documents, index the draft, then test it in the playground before publishing."
            : current.status === "ready"
              ? "Indexing is complete. Test this version in the playground or publish it."
              : current.status === "indexing"
                ? "Indexing is running. The previous published version remains available."
                : "Create a draft to update documents. You can return to this published version later."}
        </AlertDescription>
      </Alert>
      <div className="version-summary">
        <span>Version {current.id.slice(-6)}</span>
        <span>
          <strong>{current.manifest.files.length}</strong> documents
        </span>
        <span>
          <strong>{current.chunk_count}</strong> passages
        </span>
        <span>Created {date(current.created_at)}</span>
        <Status value={current.status} />
      </div>
      {current.error && <ErrorNotice error={current.error} />}
      <Panel
        title="Business documents"
        description={`${current.manifest.files.length} files in this version`}
        action={
          editable && (
            <div>
              <Button
                variant="outline"
                onClick={() =>
                  document.getElementById("upload-document")?.click()
                }
              >
                <Upload data-icon="inline-start" />
                Upload document
              </Button>
              <input
                id="upload-document"
                type="file"
                accept=".txt,.md,.pdf,.csv"
                className="hidden"
                onChange={(e) => {
                  void upload(e.target.files);
                  e.target.value = "";
                }}
              />
            </div>
          )
        }
      >
        {current.manifest.files.length === 0 ? (
          <NoItems
            title="This draft has no documents"
            description="Upload a TXT, MD, PDF, or CSV file, or write a text document below. Then index the draft."
            icon={FileText}
          />
        ) : (
          <Table className="document-table">
            <TableHeader>
              <TableRow>
                <TableHead>Document</TableHead>
                <TableHead>Format</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {current.manifest.files.map((name) => (
                <TableRow key={name}>
                  <TableCell>
                    <div className="document-name">
                      <FileText />
                      <span>{name}</span>
                    </div>
                  </TableCell>
                  <TableCell>{name.split(".").at(-1)?.toUpperCase()}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => edit(name)}
                      >
                        View{editable && " / edit"}
                      </Button>
                      {editable && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (
                              window.confirm(`Remove ${name} from this draft?`)
                            )
                              void action(
                                () =>
                                  api(
                                    `/versions/${current.id}/files/${encodeURIComponent(name)}`,
                                    { method: "DELETE" },
                                  ),
                                "Removed from draft",
                                reload,
                              );
                          }}
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Panel>
      <details className="advanced-settings">
        <summary>
          <SlidersHorizontal />
          Passage configuration
        </summary>
        <ChunkingSettings key={current.id} version={current} reload={reload} />
      </details>
      {editable && (
        <Panel
          title="Create a text document"
          description="Add a new policy, service guide, or FAQ to this draft."
        >
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              setFile({
                name: newName.endsWith(".txt") ? newName : newName + ".txt",
                content: "",
                editable: true,
              });
              setEditOpen(true);
            }}
          >
            <Field className="max-w-sm">
              <FieldLabel htmlFor="new-document">Filename</FieldLabel>
              <Input
                id="new-document"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="delivery-policy.txt"
                required
              />
            </Field>
            <Button variant="outline" type="submit">
              <Plus data-icon="inline-start" />
              Write document
            </Button>
          </form>
        </Panel>
      )}
      <Dialog open={publishOpen} onOpenChange={setPublishOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Publish this knowledge version?</DialogTitle>
            <DialogDescription>
              Customer replies will use version {current.id.slice(-6)} instead
              of the currently published version {data.published.slice(-6)}.
            </DialogDescription>
          </DialogHeader>
          <div className="proof-record">
            <span>{current.manifest.files.length} documents</span>
            <span>{current.chunk_count} passages</span>
          </div>
          <p className="help-copy">
            Test this version in Playground before publishing. You can publish
            an earlier ready version to return to it.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPublishOpen(false)}>
              Keep reviewing
            </Button>
            <Button
              onClick={() =>
                action(
                  () =>
                    api(`/versions/${current.id}/publish`, { method: "POST" }),
                  "Knowledge published",
                  () => {
                    setPublishOpen(false);
                    reload();
                  },
                )
              }
            >
              Publish to WhatsApp
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{file?.name}</DialogTitle>
            <DialogDescription>
              {file?.editable
                ? "Changes are saved to this draft. Index it again before testing."
                : "Document preview"}
            </DialogDescription>
          </DialogHeader>
          {file?.content == null ? (
            <NoItems
              title="PDF document"
              description="Index this document to inspect its extracted passages in the playground."
            />
          ) : (
            <Field>
              <FieldLabel htmlFor="file-content">Content</FieldLabel>
              <Textarea
                id="file-content"
                className="min-h-80"
                value={file.content}
                readOnly={!file.editable}
                onChange={(e) => setFile({ ...file, content: e.target.value })}
              />
            </Field>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>
              Close
            </Button>
            {file?.editable && (
              <Button onClick={save} disabled={saving}>
                {saving && <Spinner data-icon="inline-start" />}Save draft
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={passages !== null}
        onOpenChange={(open) => {
          if (!open) setPassages(null);
        }}
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>Indexed knowledge passages</DialogTitle>
            <DialogDescription>
              {passages?.length} passages in this knowledge version.
            </DialogDescription>
          </DialogHeader>
          <div className="flex max-h-[65vh] flex-col gap-4 overflow-y-auto">
            {passages?.map((passage, index) => (
              <details
                className="source-passage"
                key={passage.id}
                open={index === 0}
              >
                <summary>
                  <span className="source-number">{index + 1}</span>
                  <span>{String(passage.metadata.source || "Knowledge")}</span>
                </summary>
                <p className="passage-text mt-3">{passage.text}</p>
              </details>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPassages(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Playground({
  versionId,
  onVersionChange,
}: {
  versionId: string;
  onVersionChange: (id: string) => void;
}) {
  const { data, error, reload } = useResource<{
    versions: Version[];
    published: string;
  }>("/versions", true);
  const [selected, setSelected] = useState(versionId),
    [session, setSession] = useState(() => crypto.randomUUID()),
    [question, setQuestion] = useState(""),
    [busy, setBusy] = useState(false),
    [failure, setFailure] = useState(""),
    [history, setHistory] = useState<
      { role: string; text: string; response?: Answer }[]
    >([]),
    [inspect, setInspect] = useState<Answer | null>(null);
  const version = data?.versions.some(
    (item) =>
      item.id === selected && item.compatible && ["ready", "published"].includes(item.status),
  )
    ? selected
    : data?.published || "";
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
          version_id: version,
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
  if (!data)
    return <Loading label="Loading versions available for answer testing…" />;
  const currentVersion = data.versions.find((item) => item.id === version);
  return (
    <div className="flex flex-col gap-4">
      {error && <ErrorNotice error={error} retry={reload} />}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <VersionSelect
          versions={data.versions}
          value={version}
          readyOnly
          onChange={(id) => {
            setSelected(id);
            onVersionChange(id);
            setHistory([]);
            setInspect(null);
            setSession(crypto.randomUUID());
          }}
        />
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
        Using version {version.slice(-6)} ·{" "}
        {currentVersion?.status === "published"
          ? "Published for customers"
          : "Ready for review"}
        . Testing does not publish a version.
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
                              <Bubble
                                variant={
                                  row.role === "user" ? "default" : "muted"
                                }
                              >
                                <BubbleContent>
                                  <p className="whitespace-pre-wrap">
                                    {row.role === "assistant"
                                      ? displayAnswer(row.text)
                                      : row.text}
                                  </p>
                                </BubbleContent>
                              </Bubble>
                              {row.response && (
                                <MessageFooter>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setInspect(row.response!)}
                                  >
                                    Inspect{" "}
                                    {row.response.retrieval_context.length}{" "}
                                    sources · {row.response.latency_seconds}s
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
                        <div className="flex items-center gap-2 p-3">
                          <Spinner />
                          <span className="help-copy">
                            Finding business knowledge and writing a reply…
                          </span>
                        </div>
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
        <Card className="flex min-h-0 flex-col">
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
                {inspect.retrieval_context.map((chunk, i) => (
                  <details className="source-passage" key={i} open={i === 0}>
                    <summary>
                      <span className="source-number">{i + 1}</span>
                      <span>
                        {String(chunk.metadata.source || "Knowledge passage")}
                      </span>
                      <span className="source-score">
                        {percentage(chunk.similarity)}
                      </span>
                    </summary>
                    <p className="help-copy">
                      Cosine similarity · higher is closer
                    </p>
                    <p className="passage-text">{chunk.text}</p>
                  </details>
                ))}
                {inspect.retrieval_context.length === 0 && (
                  <NoItems
                    title="No retrieval needed"
                    description="Greetings and menu replies do not require knowledge search."
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
                      {row.answer ? displayAnswer(row.answer) : "No automatic reply recorded."}
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
              {selected ? selected.answer ? displayAnswer(selected.answer) : "No automatic reply recorded." : ""}
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
          title="Answering and evaluation"
          description="Choose models independently and control retrieval."
        >
          <form onSubmit={save} className="flex flex-col gap-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="answer-model">Answering model</FieldLabel>
                <Input
                  id="answer-model"
                  value={form.openrouter_model}
                  onChange={(e) =>
                    setForm({ ...form, openrouter_model: e.target.value })
                  }
                  required
                />
                <FieldDescription>
                  OpenRouter model identifier used for customer replies.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="judge-model">
                  Evaluation scoring model
                </FieldLabel>
                <Input
                  id="judge-model"
                  value={form.eval_model}
                  onChange={(e) =>
                    setForm({ ...form, eval_model: e.target.value })
                  }
                  required
                />
                <FieldDescription>
                  DeepEval uses this model to score answers.
                </FieldDescription>
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
                  <TableCell className="capitalize">{name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {connected ? "Configured" : "Missing key"}
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
              Archived versions keep their original embedding identity and cannot be used with a different index.
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
  async function save(path: string, method: string, body: unknown, message: string) {
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
    : queue ? (queue.failed || 0) + (queue.uncertain || 0) : null;
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
        {
          title: "Reply worker",
          ready: data.worker_running,
          detail: data.worker_running
            ? "The local inbox worker is running."
            : "The reply worker is stopped. Keep the backend running with the WAHA provider enabled.",
        },
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
                {data.worker_running
                  ? "Reply worker running"
                  : "Reply worker stopped"}
              </span>
            </div>
            <Field orientation="horizontal" className="mt-4" data-disabled={saving || data.bot_replies_enabled === undefined}>
              <FieldContent>
                <FieldLabel htmlFor={compact ? "dashboard-bot-replies" : "providers-bot-replies"}>Bot replies</FieldLabel>
                <FieldDescription id={compact ? "dashboard-bot-help" : "providers-bot-help"}>
                  {data.bot_replies_enabled === false
                    ? "Off. New messages are saved without an automatic reply."
                    : "On. New WhatsApp messages receive automatic replies."}
                </FieldDescription>
              </FieldContent>
              <div className="flex min-h-11 shrink-0 items-center gap-2">
                {saving && <Spinner aria-label="Saving WhatsApp settings" />}
                <Switch
                  id={compact ? "dashboard-bot-replies" : "providers-bot-replies"}
                  checked={data.bot_replies_enabled === true}
                  aria-describedby={compact ? "dashboard-bot-help" : "providers-bot-help"}
                  disabled={saving || data.bot_replies_enabled === undefined}
                  onCheckedChange={(enabled) => void save("/whatsapp/replies", "PUT",
                    { enabled }, enabled ? "Bot replies turned on" : "Bot replies turned off")}
                />
              </div>
            </Field>
            <p className="help-copy mt-2">
              Turning replies back on only answers new messages. Playground stays available.
              A reply already being sent may still arrive.
            </p>
            {saveError && <div className="mt-4"><ErrorNotice error={saveError} /></div>}
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
                    {data.attention?.failed ?? queue?.failed ?? 0} failed · {data.attention?.uncertain ?? queue?.uncertain ?? 0} delivery
                    uncertain. Check WhatsApp before retrying an uncertain delivery.
                  </span>
                  <span>Ignoring this warning keeps the message history. New failures will still appear.</span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={saving || !data.attention?.items.length}
                    onClick={() => void save("/whatsapp/attention/ignore", "POST",
                      { items: data.attention?.items }, "Warning ignored")}
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
    preparing: "Preparing the selected version and dataset",
    answering: "Generating the current case answer",
    indexing: "Indexing the selected knowledge version",
    generating: "Generating conversation candidates from indexed knowledge",
    scoring: "Scoring the answer against its reference",
    reporting: "Saving scores and uploading the report",
    running: "The worker is processing this task",
    completed: "Results saved",
    failed: "Task failed",
    interrupted: "Task interrupted by a backend restart",
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
            ? `${completed} of ${total} cases recorded`
            : job.status === "queued"
              ? "One local worker processes jobs in order"
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
              {["Prepare", "Answer", "Score", "Report"][index]}
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
  if (job.result_case_count != null) return `${job.result_case_count} cases saved`;
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
  if (job.error)
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="help-copy">{job.error}</p>
        {select && (
          <Button variant="outline" size="sm" onClick={() => select(job)}>
            View progress
          </Button>
        )}
      </div>
    );
  if (job.result_case_count != null && inspect)
    return (
      <Button variant="ghost" size="sm" onClick={() => inspect(job)}>
        Inspect results
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
              <strong>{jobName(job.kind)}</strong>
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
              <TableCell className="capitalize">{jobName(job.kind)}</TableCell>
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
    versions = useResource<{ versions: Version[]; published: string }>(
      "/versions",
      true,
    ),
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
  const [selected, setSelected] = useState(""),
    [kind, setKind] = useState("legacy"),
    [limit, setLimit] = useState(10),
    [resultJobId, setResultJobId] = useState(""),
    [datasetOpen, setDatasetOpen] = useState(false),
    [datasetKind, setDatasetKind] = useState("conversations"),
    [busy, setBusy] = useState(false),
    [selectedJobId, setSelectedJobId] = useState(""),
    [resultFilter, setResultFilter] = useState("all");
  const resultResource = useResource<Job>(
    resultJobId ? `/jobs/${resultJobId}` : null,
    false,
  );
  const result = resultResource.data?.result;
  const reviewData = datasetKind === "audited" ? qa.data : dataset.data;
  const evaluationJobs = (resources.data || []).filter((job) =>
    ["evaluate", "generate", "report"].includes(job.kind),
  );
  const activeJobs = evaluationJobs.filter((job) =>
    ["queued", "running"].includes(job.status),
  );
  const focusedJob = evaluationJobs.find((job) => job.id === selectedJobId);
  const visibleJobs = activeJobs.length
    ? activeJobs
    : focusedJob
      ? [focusedJob]
      : [];
  const selectedVersion = versions.data?.versions.find(
    (version) => version.id === (selected || versions.data?.published),
  );
  const referenceReady = kind === "legacy" || (kind === "audited"
    ? qa.data?.reviewed : dataset.data?.reviewed);
  const needsAttention = (row: EvaluationResult["cases"][number]) =>
    !!row.error ||
    row.metrics.some((metric) => metric.error || metric.passed === false);
  const resultCases =
    result?.cases.filter(
      (row) => resultFilter === "all" || needsAttention(row),
    ) || [];
  const run = async () => {
    if (!selectedVersion || !referenceReady) return;
    setBusy(true);
    try {
      const job = await api<{ job_id: string }>("/evaluations", {
        method: "POST",
        body: jsonBody({
          version_id: selectedVersion.id,
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
    <div className="flex flex-col gap-6">
      {[resources, versions, dataset, qa, providers].map((resource, index) =>
        resource.error ? <ErrorNotice key={index} error={resource.error} retry={resource.reload} /> : null,
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
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel
          title="Run an evaluation"
          description="Choose a ready version and a reference dataset. This run calls your configured model APIs."
        >
          {!versions.data ? <Loading label="Loading knowledge versions…" /> : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run();
            }}
            className="flex flex-col gap-6"
          >
            <FieldGroup>
              <Field>
                <FieldLabel>Knowledge version</FieldLabel>
                <VersionSelect
                  versions={versions.data.versions}
                  readyOnly
                  value={selected || versions.data.published}
                  onChange={setSelected}
                />
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
                    Reviewed QA references ({qa.data ? `${qa.data.count} cases` : "loading…"})
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
                Version {selectedVersion?.id.slice(-6) || "Not selected"} ·{" "}
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
                Answer: {providers.data?.openrouter_model || "Loading model…"}
              </p>
              <p>
                Scoring:{" "}
                {providers.data?.eval_model || "Loading scoring model…"}
              </p>
            </div>
            <Button
              type="submit"
              disabled={
                busy ||
                !referenceReady ||
                !selectedVersion ||
                !selectedVersion.compatible || !["ready", "published"].includes(selectedVersion.status) ||
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
          </form>)}
        </Panel>
        <Panel
          title="Conversation scenarios"
          description="Generate candidates from business knowledge, then review their expected outcomes."
        >
          {!dataset.data ? <Loading label="Loading conversation references…" /> : (
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
                disabled={!selectedVersion}
                onClick={() =>
                  action(
                    () =>
                      api("/evaluations/generate", {
                        method: "POST",
                        body: jsonBody({
                          base_id: selectedVersion?.id,
                        }),
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
                onClick={() => {
                  setDatasetKind("conversations");
                  setDatasetOpen(true);
                }}
              >
                Review dataset
              </Button>
            )}
          </div>)}
        </Panel>
      </div>
      <Panel
        title="QA reference review"
        description="Review required facts and clarification guidance before comparing chunking configurations."
      >
        {!qa.data ? <Loading label="Loading QA references…" /> : <>
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="outline">{qa.data.count} candidate cases</Badge>
          <Badge variant="outline">
            {qa.data.held_count} held for business confirmation
          </Badge>
          <Status value={qa.data.reviewed ? "reviewed" : "awaiting review"} />
          <Button
            variant="outline"
            onClick={() => {
              setDatasetKind("audited");
              setDatasetOpen(true);
            }}
          >
            Review QA references
          </Button>
        </div>
        <p className="help-copy mt-4">
          Held cases are excluded. Changes to the reference file invalidate its
          review. The original benchmark remains available separately.
        </p>
        </>}
      </Panel>
      <Panel
        title="Evaluation history"
        description="Inspect case scores, download results, and open the corresponding LangSmith experiment."
      >
        {!resources.data ? <Loading label="Loading evaluation history…" /> : evaluationJobs.length ? (
          <JobTable
            jobs={evaluationJobs}
            inspect={(job) => {
              setResultJobId(job.id);
              setResultFilter("all");
            }}
            select={(job) => {
              setSelectedJobId(job.id);
              window.scrollTo({ top: 0, behavior: "instant" });
            }}
          />
        ) : (
          <NoItems
            title="No evaluation runs yet"
            description="Run the original questions to establish an answer quality reference."
            icon={FlaskConical}
          />
        )}
      </Panel>
      {resultResource.error && (
        <ErrorNotice error={resultResource.error} retry={resultResource.reload} />
      )}
      {resultJobId && !result && !resultResource.error && (
        <Loading label="Loading saved evaluation results…" />
      )}
      {result && (
        <Panel
          title="Evaluation results"
          description={`${result.cases.length} cases · ${result.model} · Judge: ${result.judge}${result.chunking ? ` · Chunking ${result.chunking.chunk_size}/${result.chunking.chunk_overlap}` : " · Historical configuration"}`}
          action={
            <Button variant="outline" size="sm" asChild>
              <a href={`/admin/api/evaluations/${result.id}/export`} download>
                Export JSON
              </a>
            </Button>
          }
        >
          <div className="flex flex-wrap gap-4">
            {Object.entries(result.averages || {}).map(([name, score]) => (
              <div className="evaluation-average" key={name}>
                <strong>{percentage(score)}</strong>
                <span>{name}</span>
              </div>
            ))}
          </div>
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
                  <span>{row.input || row.scenario || row.id}</span>
                  <Badge variant="outline">
                    {row.error
                      ? "Answer error"
                      : row.metrics.some((metric) => metric.error)
                        ? "Scoring error"
                        : row.metrics.length === 0
                          ? "Not scored"
                          : `${row.metrics.filter((metric) => metric.passed).length}/${row.metrics.length} metrics passed`}
                  </Badge>
                </summary>
                {row.answer && (
                  <p className="passage-text">{displayAnswer(row.answer)}</p>
                )}
                {(row.expected_output || row.expected_outcome) && (
                  <div className="metric-detail">
                    <strong>Reference answer / expected outcome</strong>
                    <p>{row.expected_output || row.expected_outcome}</p>
                  </div>
                )}
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
                          : percentage(metric.score)}
                      </Badge>
                    </summary>
                    <p>{metric.reason || metric.error}</p>
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
                    ? "Every scored metric in this run passed its configured threshold and no answer or scoring errors were recorded."
                    : "This run did not record case results. Inspect its progress and error details before starting another run."
                }
                icon={Check}
              />
            )}
          </div>
        </Panel>
      )}
      {reviewData && <Dialog open={datasetOpen} onOpenChange={setDatasetOpen}>
        <DialogContent className="sm:max-w-4xl">
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
              locally if corrections are needed; changes invalidate the review.
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
              disabled={datasetKind === "conversations" && dataset.data?.stale}
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
      </Dialog>}
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
      Knowledge: "/versions",
      Playground: "/versions",
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
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
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
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
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
    [page, setPage] = useState(readPage),
    [workspaceVersion, setWorkspaceVersion] = useState("");
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
  const signedIn = user ? true : auth === null ||
    (session.error instanceof ApiError && session.error.status === 401) ? false : null;
  const username = user?.username || "";
  const clearSession = () => {
    queryClient.clear();
    setCsrf("");
    setWorkspaceVersion("");
    setAuth(null);
  };
  const navigate = (name: string) => {
    if (window.location.pathname !== adminPagePath(name))
      window.history.pushState(null, "", adminPagePath(name));
    setPage(name);
    window.scrollTo(0, 0);
  };
  useEffect(() => {
    const expired = () => clearSession();
    const change = () => {
      const name = readPage();
      if (window.location.pathname !== "/admin/login")
        window.history.replaceState(null, "", adminPagePath(name) + window.location.search);
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
            <ErrorNotice error={session.error.message} retry={() => void session.refetch()} />
          ) : <Loading label={session.isPaused
            ? "You're offline. Your workspace will reconnect when you're back online."
            : session.failureCount
              ? "Reconnecting to your workspace. Retrying automatically…"
              : "Loading workspace data…"} />}
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
                <Knowledge
                  versionId={workspaceVersion}
                  onVersionChange={setWorkspaceVersion}
                  testVersion={(id) => {
                    setWorkspaceVersion(id);
                    navigate("Playground");
                  }}
                />
              ) : title === "Playground" ? (
                <Playground
                  versionId={workspaceVersion}
                  onVersionChange={setWorkspaceVersion}
                />
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
