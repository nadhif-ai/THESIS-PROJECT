import { useCallback, useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
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
  Printer,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { api, jsonBody, setCsrf } from "@/lib/api";
import type {
  Version,
  Answer,
  Job,
  Conversation,
  EvaluationResult,
  Providers,
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
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  FieldGroup,
  Field,
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
  value == null ? "—" : `${Math.round(value * 100)}%`;
function displayAnswer(text: string) {
  return text
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|li)>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&nbsp;/g, " ");
}
function Status({ value }: { value: string }) {
  return (
    <Badge
      variant={
        ["published", "completed", "ready"].includes(value)
          ? "default"
          : value === "failed"
            ? "destructive"
            : "outline"
      }
    >
      {value === "published" ? <Check data-icon="inline-start" /> : null}
      {value}
    </Badge>
  );
}
function ErrorNotice({ error }: { error: string }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Action needed</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
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
        <div className="flex items-start justify-between gap-4">
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
function useResource<T>(path: string, poll = false) {
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision((r) => r + 1), []);
  useEffect(() => {
    let live = true;
    const fetchData = () =>
      api<T>(path)
        .then((d) => {
          if (live) {
            setData(d);
            setError("");
          }
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    void fetchData();
    const timer = poll ? window.setInterval(fetchData, 4000) : null;
    return () => {
      live = false;
      if (timer) clearInterval(timer);
    };
  }, [path, poll, revision]);
  return { data, error, reload };
}
function Loading() {
  return (
    <div className="flex flex-col gap-5">
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

function Login({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("admin"),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await api<{ csrf: string }>("/login", {
        method: "POST",
        body: jsonBody({ username, password }),
      });
      setCsrf(user.csrf);
      onLogin();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="brand-mark">
            <Printer />
          </div>
          <CardTitle>Asia Visual Grafika</CardTitle>
          <CardDescription>Sign in to your chatbot workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="username">Username</FieldLabel>
                <Input
                  id="username"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="password">Password</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
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
        </CardContent>
        <CardFooter>
          <p className="help-copy">
            For the first local login, use the credentials saved in{" "}
            <code>data/admin-credentials.txt</code>.
          </p>
        </CardFooter>
      </Card>
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
  const { data, error } = useResource<Overview>("/overview", true);
  if (error) return <ErrorNotice error={error} />;
  if (!data) return <Loading />;
  return (
    <div className="flex flex-col gap-6">
      <div className="overview-banner">
        <div>
          <Badge variant="outline">WhatsApp knowledge</Badge>
          <h2>
            Published guidance for
            <br className="hidden lg:block" /> printing customers.
          </h2>
          <p>
            {data.published.manifest.files.length} documents and{" "}
            {data.published.chunk_count} searchable passages are published.
          </p>
          <Button onClick={() => navigate("Playground")}>
            Test an answer
            <ArrowUpRight data-icon="inline-end" />
          </Button>
        </div>
        <div className="publication-rail">
          <div>
            <span className="rail-icon">
              <FileText />
            </span>
            <span>Business documents</span>
          </div>
          <ChevronRight />
          <div>
            <span className="rail-icon">
              <Database />
            </span>
            <span>Indexed knowledge</span>
          </div>
          <ChevronRight />
          <div>
            <span className="rail-icon">
              <MessageSquare />
            </span>
            <span>Live on WhatsApp</span>
          </div>
        </div>
      </div>
      <div className="stat-strip">
        <div>
          <span>Customer messages</span>
          <strong>{data.whatsapp_messages}</strong>
        </div>
        <div>
          <span>Recorded replies</span>
          <strong>{data.conversations}</strong>
        </div>
        <div>
          <span>Average response time</span>
          <strong>
            {data.average_latency ? `${data.average_latency}s` : "—"}
          </strong>
        </div>
        <div>
          <span>Knowledge status</span>
          <Status value={data.published.status} />
        </div>
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <Panel
          title="Recent conversations"
          description="Customer, playground, and API activity"
          action={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("Conversations")}
            >
              View history
              <ArrowUpRight data-icon="inline-end" />
            </Button>
          }
        >
          {data.recent.length ? (
            <Table>
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
        <Panel
          title="Captured retrieval baseline"
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
            <ArrowUpRight data-icon="inline-end" />
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
        .filter((v) => !readyOnly || ["ready", "published"].includes(v.status))
        .map((v) => (
          <NativeSelectOption key={v.id} value={v.id}>
            {v.status === "published"
              ? "Published"
              : v.status === "ready"
                ? "Ready"
                : "Draft"}{" "}
            · {date(v.created_at)} · {v.id.slice(-6)}
            {v.chunking && ` · ${v.chunking.chunk_size}/${v.chunking.chunk_overlap}`}
          </NativeSelectOption>
        ))}
    </NativeSelect>
  );
}
function ChunkingSettings({ version, reload }: { version: Version; reload: () => void }) {
  const [size, setSize] = useState(version.chunking.chunk_size),
    [overlap, setOverlap] = useState(version.chunking.chunk_overlap),
    [busy, setBusy] = useState(false);
  const editable = ["draft", "failed"].includes(version.status);
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    await action(
      () => api(`/versions/${version.id}/chunking`, {
        method: "PUT", body: jsonBody({ chunk_size: size, chunk_overlap: overlap }),
      }),
      "Chunking saved. Index this draft to apply it.", reload,
    );
    setBusy(false);
  }
  return <Panel title="Passage configuration" description="Sizes use characters. New indexing preserves section headings and checks the E5 token limit.">
    <form onSubmit={save} className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field><FieldLabel htmlFor="chunk-size">Chunk size</FieldLabel>
          <Input id="chunk-size" type="number" min={400} max={2000} value={size} disabled={!editable} onChange={e => setSize(Number(e.target.value))} />
        </Field>
        <Field><FieldLabel htmlFor="chunk-overlap">Overlap</FieldLabel>
          <Input id="chunk-overlap" type="number" min={0} max={Math.min(400, size - 1)} value={overlap} disabled={!editable} onChange={e => setOverlap(Number(e.target.value))} />
        </Field>
      </div>
      <p className="help-copy">{version.chunking.preprocessing === "legacy" ? "Historical passages use the original splitting process. Create a draft to use section-based splitting." : "Overlap applies within each section. Product headings are retained in each passage."}
        {version.manifest.index_statistics && ` Maximum indexed passage: ${version.manifest.index_statistics.max_tokens} tokens (limit 512).`}
      </p>
      {editable && <Button type="submit" disabled={busy} className="self-start">{busy && <Spinner />}Save chunking</Button>}
    </form>
  </Panel>;
}

function Knowledge() {
  const { data, error, reload } = useResource<{
    versions: Version[];
    published: string;
  }>("/versions", true);
  const [selected, setSelected] = useState(""),
    [file, setFile] = useState<{
      name: string;
      content: string | null;
      editable: boolean;
    } | null>(null),
    [editOpen, setEditOpen] = useState(false),
    [newName, setNewName] = useState(""),
    [saving, setSaving] = useState(false),
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
  if (error) return <ErrorNotice error={error} />;
  if (!data || !current) return <Loading />;
  const editable = ["draft", "failed"].includes(current.status);
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <VersionSelect
          versions={data.versions}
          value={current.id}
          onChange={(id) => {
            setSelected(id);
            setFile(null);
          }}
        />
        <div className="flex flex-wrap gap-2">
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
          {current.status === "ready" && (
            <Button
              onClick={() =>
                action(
                  () =>
                    api(`/versions/${current.id}/publish`, { method: "POST" }),
                  "Knowledge published",
                  reload,
                )
              }
            >
              <Check data-icon="inline-start" />
              Publish to WhatsApp
            </Button>
          )}
        </div>
      </div>
      <Alert>
        <Database />
        <AlertTitle>
          {current.status === "published"
            ? "Customers use this knowledge"
            : "A separate draft for review"}
        </AlertTitle>
        <AlertDescription>
          {editable
            ? "Add or edit documents, index the draft, then test it in the playground before publishing."
            : current.status === "ready"
              ? "Indexing is complete. Test this version in the playground or publish it."
              : current.status === "indexing"
                ? "Indexing is running. The previous published version remains available."
                : "Create a draft to update documents. You can return to this published version later."}
        </AlertDescription>
      </Alert>
      {current.error && <ErrorNotice error={current.error} />}
      <ChunkingSettings key={current.id} version={current} reload={reload} />
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
        <Table>
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
                  <div className="flex items-center gap-3">
                    <FileText className="size-4" />
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
                          if (window.confirm(`Remove ${name} from this draft?`))
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
      </Panel>
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

function Playground() {
  const { data, error } = useResource<{
    versions: Version[];
    published: string;
  }>("/versions", true);
  const [selected, setSelected] = useState(""),
    [session, setSession] = useState(() => crypto.randomUUID()),
    [question, setQuestion] = useState(""),
    [busy, setBusy] = useState(false),
    [failure, setFailure] = useState(""),
    [history, setHistory] = useState<
      { role: string; text: string; response?: Answer }[]
    >([]),
    [inspect, setInspect] = useState<Answer | null>(null);
  const version = selected || data?.published || "";
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
  if (error) return <ErrorNotice error={error} />;
  if (!data) return <Loading />;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <VersionSelect
          versions={data.versions}
          value={version}
          readyOnly
          onChange={(id) => {
            setSelected(id);
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
          disabled={busy}
        >
          <RefreshCcw data-icon="inline-start" />
          New conversation
        </Button>
      </div>
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
                            description="Try “File untuk cetak harus format apa?” or ask about prices and materials."
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
            <p className="help-copy">
              Enter to send. Shift + Enter for a new line.
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
    [selected, setSelected] = useState<Conversation | null>(null);
  const { data, error } = useResource<Conversation[]>(
    `/conversations${channel ? "?channel=" + channel : ""}`,
    true,
  );
  if (error) return <ErrorNotice error={error} />;
  if (!data) return <Loading />;
  const rows = data.filter((r) =>
    (r.question + " " + r.answer).toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <div className="flex flex-col gap-5">
      <FieldGroup className="md:flex-row">
        <Field className="max-w-sm">
          <FieldLabel htmlFor="conversation-search">Search messages</FieldLabel>
          <Input
            id="conversation-search"
            placeholder="Find a question or answer"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </Field>
        <Field className="max-w-52">
          <FieldLabel htmlFor="channel">Channel</FieldLabel>
          <NativeSelect
            id="channel"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
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
        description={`${rows.length} recent replies`}
      >
        {rows.length ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer question</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>Response time</TableHead>
                <TableHead>Received</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <Button
                      variant="ghost"
                      className="max-w-96 justify-start truncate"
                      onClick={() => setSelected(row)}
                    >
                      {row.question}
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{row.channel}</Badge>
                  </TableCell>
                  <TableCell>
                    {row.latency ? `${row.latency.toFixed(1)}s` : "—"}
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
            title="No matching conversations"
            description="Try another channel or ask a question in the playground."
            icon={MessageSquare}
          />
        )}
      </Panel>
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
            <p className="whitespace-pre-wrap">
              <strong>Customer</strong>
              <br />
              {selected?.question}
            </p>
            <p className="whitespace-pre-wrap">
              <strong>Chatbot</strong>
              <br />
              {selected ? displayAnswer(selected.answer) : ""}
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
  if (error) return <ErrorNotice error={error} />;
  if (!form) return <Loading />;
  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    await action(
      () => api("/settings", { method: "PUT", body: jsonBody(form) }),
      "Provider settings saved",
      reload,
    );
    setSaving(false);
  }
  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
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
              <FieldLabel htmlFor="judge-model">Evaluation judge</FieldLabel>
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
            </Field>
          </FieldGroup>
          <Button type="submit" disabled={saving}>
            {saving && <Spinner data-icon="inline-start" />}Save settings
          </Button>
        </form>
      </Panel>
      <div className="flex flex-col gap-6">
        <Panel
          title="Provider connections"
          description="Credentials are configured on the backend."
        >
          <Table>
            <TableBody>
              {Object.entries(form.providers).map(([name, connected]) => (
                <TableRow key={name}>
                  <TableCell className="capitalize">{name}</TableCell>
                  <TableCell>
                    <Badge variant={connected ? "secondary" : "outline"}>
                      {connected ? "Configured" : "Missing key"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Panel>
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
            Changing embeddings requires a compatible index and reindexing. The
            current E5 model is preserved for the migration comparison.
          </p>
        </Panel>
      </div>
    </div>
  );
}

function JobTable({
  jobs,
  inspect,
}: {
  jobs: Job[];
  inspect?: (result: EvaluationResult) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Task</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Started</TableHead>
          <TableHead>Result</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow key={job.id}>
            <TableCell className="capitalize">
              {job.kind === "evaluate"
                ? "Evaluation"
                : job.kind === "generate"
                  ? "Dataset generation"
                  : job.kind}
            </TableCell>
            <TableCell>
              <Status value={job.status} />
            </TableCell>
            <TableCell className="whitespace-nowrap">
              {date(job.created_at)}
            </TableCell>
            <TableCell>
              {job.error ? (
                <span className="help-copy">{job.error}</span>
              ) : job.result?.cases && inspect ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => inspect(job.result!)}
                >
                  Inspect results
                  <ArrowUpRight data-icon="inline-end" />
                </Button>
              ) : (
                "—"
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
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
    }>("/evaluations/dataset", true),
    qa = useResource<{ exists: boolean; reviewed: boolean; count: number; held_count: number; cases?: unknown[] }>("/evaluations/dataset?kind=audited", true);
  const [selected, setSelected] = useState(""),
    [kind, setKind] = useState("legacy"),
    [limit, setLimit] = useState(10),
    [result, setResult] = useState<EvaluationResult | null>(null),
    [datasetOpen, setDatasetOpen] = useState(false),
    [datasetKind, setDatasetKind] = useState("conversations"),
    [busy, setBusy] = useState(false);
  const error = resources.error || versions.error || dataset.error || qa.error;
  if (error) return <ErrorNotice error={error} />;
  if (!resources.data || !versions.data || !dataset.data || !qa.data) return <Loading />;
  const reviewData = datasetKind === "audited" ? qa.data : dataset.data;
  const run = async () => {
    setBusy(true);
    await action(
      () =>
        api("/evaluations", {
          method: "POST",
          body: jsonBody({
            version_id: selected || versions.data!.published,
            dataset: kind,
            limit,
          }),
        }),
      "Evaluation queued",
      resources.reload,
    );
    setBusy(false);
  };
  return (
    <div className="flex flex-col gap-6">
      <Alert>
        <FlaskConical />
        <AlertTitle>Compare answers using the same evidence</AlertTitle>
        <AlertDescription>
          DeepEval scores each case. LangSmith keeps the execution traces and
          experiment results. Runs use your configured model APIs.
        </AlertDescription>
      </Alert>
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel
          title="Run an evaluation"
          description="Start with the original 10 questions, then evaluate reviewed conversations."
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
                <NativeSelectOption value="audited" disabled={!qa.data.reviewed}>
                  Reviewed QA references ({qa.data.count} cases)
                </NativeSelectOption>
                <NativeSelectOption
                  value="conversations"
                  disabled={!dataset.data.reviewed}
                >
                  Reviewed conversation scenarios
                </NativeSelectOption>
                <NativeSelectOption
                  value="heldout"
                  disabled={!dataset.data.reviewed}
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
              />
              <FieldDescription>
                One run, with bounded concurrency. Metric failures appear
                separately from quality scores.
              </FieldDescription>
            </Field>
          </FieldGroup>
          <Button onClick={run} disabled={busy} className="mt-6">
            {busy ? (
              <Spinner data-icon="inline-start" />
            ) : (
              <FlaskConical data-icon="inline-start" />
            )}
            Run evaluation
          </Button>
        </Panel>
        <Panel
          title="Conversation scenarios"
          description="Generate candidates from business knowledge, then review their expected outcomes."
        >
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Badge variant="outline">{dataset.data.count} scenarios</Badge>
              <Status
                value={
                  dataset.data.reviewed
                    ? "ready"
                    : dataset.data.stale
                      ? "needs reference update"
                    : dataset.data.exists
                      ? "awaiting review"
                      : "not generated"
                }
              />
            </div>
            <p className="help-copy">
              {dataset.data.stale && "These candidates include superseded business facts. Correct or regenerate their contexts and expected outcomes before review. "}
              A reserved portion is held out from development runs. Generated
              labels need a human check before scoring.
            </p>
            {!dataset.data.exists ? (
              <Button
                variant="outline"
                onClick={() =>
                  action(
                    () =>
                      api("/evaluations/generate", {
                        method: "POST",
                        body: jsonBody({
                          base_id: selected || versions.data!.published,
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
              <Button variant="outline" onClick={() => { setDatasetKind("conversations"); setDatasetOpen(true); }}>
                Review dataset
                <ArrowUpRight data-icon="inline-end" />
              </Button>
            )}
          </div>
        </Panel>
      </div>
      <Panel title="QA reference review" description="Review required facts and clarification guidance before comparing chunking configurations.">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="outline">{qa.data.count} candidate cases</Badge>
          <Badge variant="outline">{qa.data.held_count} held for business confirmation</Badge>
          <Status value={qa.data.reviewed ? "ready" : "awaiting review"} />
          <Button variant="outline" onClick={() => { setDatasetKind("audited"); setDatasetOpen(true); }}>Review QA references</Button>
        </div>
        <p className="help-copy mt-4">Held cases are excluded. Changes to the reference file invalidate its review. The original benchmark remains available separately.</p>
      </Panel>
      <Panel
        title="Evaluation history"
        description="Inspect case scores, download results, and open the corresponding LangSmith experiment."
      >
        {resources.data.length ? (
          <JobTable jobs={resources.data} inspect={setResult} />
        ) : (
          <NoItems
            title="No evaluation runs yet"
            description="Run the original questions to establish an answer quality reference."
            icon={FlaskConical}
          />
        )}
      </Panel>
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
            {result.cases.map((row) => (
              <details className="evaluation-case" key={row.id}>
                <summary>
                  <span>{row.input || row.scenario || row.id}</span>
                  <Badge variant="outline">
                    {row.metrics.filter((m) => m.passed).length}/
                    {row.metrics.length} passed
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
                  <div className="metric-detail" key={metric.name}>
                    <div>
                      <strong>{metric.name}</strong>
                      <Badge variant={metric.error ? "destructive" : "outline"}>
                        {metric.error
                          ? "Scoring error"
                          : percentage(metric.score)}
                      </Badge>
                    </div>
                    <p>{metric.reason || metric.error}</p>
                  </div>
                ))}
              </details>
            ))}
          </div>
        </Panel>
      )}
      <Dialog open={datasetOpen} onOpenChange={setDatasetOpen}>
        <DialogContent className="sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>{datasetKind === "audited" ? "Review QA references" : "Review conversation scenarios"}</DialogTitle>
            <DialogDescription>
              Check business facts and expected outcomes. Edit
              {datasetKind === "audited" ? " testing/evals/qa-reference-candidates.json" : " testing/evals/.dataset.json"} locally if corrections are needed;
              changes invalidate the review.
            </DialogDescription>
          </DialogHeader>
          <pre className="dataset-preview">
            {JSON.stringify(reviewData.cases, null, 2)}
          </pre>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDatasetOpen(false)}>
              Close
            </Button>
            <Button
              disabled={datasetKind === "conversations" && dataset.data.stale}
              onClick={() =>
                action(
                  () => api(`/evaluations/dataset/review?kind=${datasetKind}`, { method: "POST" }),
                  "Dataset marked reviewed",
                  () => {
                    dataset.reload();
                    qa.reload();
                    setDatasetOpen(false);
                  },
                )
              }
            >
              {datasetKind === "audited" ? "I reviewed the non-held references" : "I reviewed these scenarios"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function App() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null),
    [page, setPage] = useState(
      () => decodeURIComponent(location.hash.slice(1)) || "Dashboard",
    );
  const navigate = (name: string) => {
    window.history.pushState(null, "", "#" + encodeURIComponent(name));
    setPage(name);
  };
  useEffect(() => {
    api<{ csrf: string }>("/me")
      .then((user) => {
        setCsrf(user.csrf);
        setSignedIn(true);
      })
      .catch(() => setSignedIn(false));
    const expired = () => setSignedIn(false);
    const change = () =>
      setPage(decodeURIComponent(location.hash.slice(1)) || "Dashboard");
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
  const descriptions: Record<string, string> = {
    Dashboard:
      "Your business knowledge and customer conversations, in one place.",
    Knowledge: "Prepare, test, and publish the information your chatbot uses.",
    Playground: "Test answers before they reach a customer.",
    Conversations:
      "Review the questions customers ask and the replies they receive.",
    Providers: "Manage answering models, evaluation models, and retrieval.",
    Evaluations: "Measure answer quality and compare reproducible runs.",
  };
  return (
    <TooltipProvider>
      <Toaster richColors />
      {signedIn === null ? (
        <main className="p-12">
          <Loading />
        </main>
      ) : !signedIn ? (
        <Login onLogin={() => setSignedIn(true)} />
      ) : (
        <SidebarProvider>
          <Sidebar>
            <SidebarHeader>
              <a className="workspace-brand" href="#Dashboard">
                <span className="brand-mark">
                  <Printer />
                </span>
                <span>
                  <strong>Asia Visual Grafika</strong>
                  <small>Chatbot workspace</small>
                </span>
              </a>
            </SidebarHeader>
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupLabel>Workspace</SidebarGroupLabel>
                <SidebarMenu>
                  {pages.map((p) => (
                    <SidebarMenuItem key={p.name}>
                      <SidebarMenuButton
                        isActive={title === p.name}
                        onClick={() => navigate(p.name)}
                        tooltip={p.name}
                      >
                        <p.icon />
                        <span>{p.name}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroup>
            </SidebarContent>
            <SidebarFooter>
              <div className="sidebar-note">
                <MessageSquare />
                <div>
                  <strong>WhatsApp customer support</strong>
                  <p>
                    Review knowledge here.
                    <br />
                    Customers chat in WhatsApp.
                  </p>
                </div>
              </div>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() =>
                      action(
                        () => api("/logout", { method: "POST" }),
                        "Signed out",
                        () => setSignedIn(false),
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
              <SidebarTrigger />
              <span>Chatbot administration</span>
              <Badge variant="outline">Asia Visual Grafika</Badge>
            </header>
            <main className="workspace-main">
              <div className="page-intro">
                <h1>{title}</h1>
                <p>{descriptions[title]}</p>
              </div>
              {title === "Dashboard" ? (
                <Dashboard navigate={navigate} />
              ) : title === "Knowledge" ? (
                <Knowledge />
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
