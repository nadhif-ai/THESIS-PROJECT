import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { RefreshCcw, Upload } from "lucide-react";
import { toast } from "sonner";
import { api, jsonBody } from "@/lib/api";
import type { Job, Version } from "@/lib/api";
import { useResource } from "@/hooks/use-resource";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  FieldGroup,
  Field,
  FieldLabel,
  FieldDescription,
} from "@/components/ui/field";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

type Source = {
  id: string;
  name: string;
  format: string;
  enabled: boolean;
  size_bytes: number;
  page_count: number;
  updated_at: string;
};
export type KnowledgeCatalog = {
  sources: Source[];
  chunking: {
    chunk_size: number;
    chunk_overlap: number;
    preprocessing?: string;
  };
  active: Version | null;
  pending: boolean;
  initialized: boolean;
  sync_job: string | null;
  revision: number;
  applied_revision: number;
};
type Preview = {
  name: string;
  format: string;
  url: string;
  text: string;
  navigation_only: boolean;
  chunk_count: number;
  chunks: { text: string; metadata: { page?: number } }[];
};

export function KnowledgePage({
  testKnowledge,
}: {
  testKnowledge: () => void;
}) {
  const resource = useResource<KnowledgeCatalog>("/knowledge");
  const jobs = useResource<Job[]>("/jobs");
  const data = resource.data;
  const [busy, setBusy] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [failure, setFailure] = useState("");
  const [size, setSize] = useState(1000),
    [overlap, setOverlap] = useState(100);
  const [viewSource, setViewSource] = useState<Source | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [text, setText] = useState("");
  const [passagePage, setPassagePage] = useState(0);
  const [removing, setRemoving] = useState<Source | null>(null);
  const [replacement, setReplacement] = useState<Source | null>(null);
  const fileInput = useRef<HTMLInputElement>(null),
    replaceInput = useRef<HTMLInputElement>(null);
  const previewRequest = useRef(0);
  const dialogTrigger = useRef<HTMLElement | null>(null);
  function restoreFocus(event: Event) {
    event.preventDefault();
    const target = dialogTrigger.current;
    if (target?.isConnected) target.focus();
    else document.getElementById("workspace-content")?.focus();
  }
  const locked = busy || !!data?.sync_job;
  const syncJob =
    jobs.data?.find((job) => job.id === data?.sync_job) ||
    jobs.data?.find((job) => job.kind === "sync");
  useEffect(() => {
    if (data) {
      setSize(data.chunking.chunk_size);
      setOverlap(data.chunking.chunk_overlap);
    }
  }, [data?.chunking.chunk_size, data?.chunking.chunk_overlap]);

  async function mutate(work: () => Promise<unknown>, message: string) {
    setBusy(true);
    setFailure("");
    try {
      await work();
      toast.success(message);
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setBusy(false);
      resource.reload();
      jobs.reload();
    }
  }
  async function uploadFile(file: File, source?: Source) {
    if (
      file.size < 1 ||
      file.size > 10 * 1024 * 1024 ||
      !/\.(txt|pdf)$/i.test(file.name)
    )
      throw new Error(
        "Upload TXT or selectable-text PDF files, between 1 byte and 10 MB each.",
      );
    const ticket = await api<{
      upload_id: string;
      url: string;
      content_type: string;
    }>("/knowledge/uploads", {
      method: "POST",
      body: jsonBody({
        name: file.name,
        size_bytes: file.size,
        source_id: source?.id,
      }),
    });
    const response = await fetch(ticket.url, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": ticket.content_type },
      signal: AbortSignal.timeout(120_000),
    });
    if (!response.ok)
      throw new Error(
        "File upload failed. Check your connection and upload again.",
      );
    await api(`/knowledge/uploads/${ticket.upload_id}/complete`, {
      method: "POST",
      body: jsonBody({ source_id: source?.id }),
    });
  }
  async function uploadFiles(files: FileList | null, source?: Source) {
    if (!files?.length) return;
    const list = Array.from(files);
    await mutate(async () => {
      for (const [index, file] of list.entries()) {
        setUploadProgress(
          `Uploading ${index + 1} of ${list.length}: ${file.name}`,
        );
        await uploadFile(file, source);
      }
    }, "Sources saved. Sync knowledge to apply these changes.");
    setUploadProgress("");
    resource.reload();
    if (fileInput.current) fileInput.current.value = "";
    if (replaceInput.current) replaceInput.current.value = "";
  }
  async function openPreview(source: Source) {
    dialogTrigger.current = document.activeElement as HTMLElement | null;
    const request = ++previewRequest.current;
    setViewSource(source);
    setPreview(null);
    setPreviewError("");
    setPassagePage(0);
    try {
      const content = await api<Preview>(
        `/knowledge/sources/${source.id}/preview`,
      );
      if (request === previewRequest.current) {
        setPreview(content);
        setText(content.text);
      }
    } catch (error) {
      if (request === previewRequest.current)
        setPreviewError((error as Error).message);
    }
  }
  async function loadPassages(page: number) {
    if (!viewSource) return;
    try {
      const result = await api<Pick<Preview, "chunks" | "chunk_count">>(
        `/knowledge/sources/${viewSource.id}/chunks?page=${page}`,
      );
      setPreview((current) => (current ? { ...current, ...result } : current));
      setPassagePage(page);
    } catch (error) {
      toast.error((error as Error).message);
    }
  }
  async function configure(event: FormEvent) {
    event.preventDefault();
    await mutate(
      () =>
        api("/knowledge/chunking", {
          method: "PUT",
          body: jsonBody({ chunk_size: size, chunk_overlap: overlap }),
        }),
      "Chunking saved. Sync knowledge to apply it.",
    );
  }
  if (!data)
    return resource.error ? (
      <Alert variant="destructive">
        <AlertTitle>Knowledge could not load</AlertTitle>
        <AlertDescription>
          {resource.error}
          <Button variant="outline" onClick={resource.reload}>
            Try again
          </Button>
        </AlertDescription>
      </Alert>
    ) : (
      <p role="status">
        <Spinner className="inline" /> Loading knowledge…
      </p>
    );
  const configurationChanged =
    size !== data.chunking.chunk_size ||
    overlap !== data.chunking.chunk_overlap;
  return (
    <div className="flex min-w-0 flex-col gap-6">
      <section
        className="overview-proof"
        aria-label="Knowledge synchronization"
      >
        <div className="min-w-0">
          <h2>One knowledge base. Every conversation.</h2>
          <p className="help-copy">
            WhatsApp, Playground and new evaluations use the same synchronized
            knowledge.
          </p>
          <div className="proof-record mt-3">
            <Badge variant="outline">
              {data.pending ? "Changes to sync" : "Up to date"}
            </Badge>
            <span>
              {data.active?.manifest.files.length || 0} active sources
            </span>
            <span>{data.active?.chunk_count || 0} searchable passages</span>
            <span>
              {data.active
                ? `Last sync ${new Date(data.active.manifest.synced_at || data.active.created_at).toLocaleString()}`
                : "No knowledge synchronized yet"}
            </span>
          </div>
        </div>
        <Button
          disabled={locked || !data.initialized || configurationChanged}
          onClick={() =>
            void mutate(async () => {
              const result = await api<{ dispatch_pending?: boolean }>(
                "/knowledge/sync",
                { method: "POST" },
              );
              if (result.dispatch_pending)
                throw new Error(
                  "Synchronization is saved, but queue dispatch failed. Use Resume below.",
                );
            }, "Synchronization started. Current knowledge stays available until replacement succeeds.")
          }
        >
          {data.sync_job ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <RefreshCcw data-icon="inline-start" />
          )}
          Sync knowledge
        </Button>
      </section>
      {(failure || resource.error) && (
        <Alert variant="destructive">
          <AlertTitle>Action could not complete</AlertTitle>
          <AlertDescription>{failure || resource.error}</AlertDescription>
        </Alert>
      )}
      {!data.initialized && (
        <Alert>
          <AlertTitle>Source migration required</AlertTitle>
          <AlertDescription>
            Current bot knowledge is still available. Import its original
            sources before the first synchronization.
          </AlertDescription>
        </Alert>
      )}
      {data.pending && (
        <p className="help-copy">
          Source and configuration changes take effect after Sync knowledge
          succeeds. Running evaluations keep the knowledge captured when they
          started.
        </p>
      )}
      {syncJob && (
        <Card>
          <CardHeader>
            <CardTitle>Latest synchronization</CardTitle>
            <CardDescription>
              Recorded progress, with changes locked while work is running.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-3" role="status">
              <Badge variant="outline">{syncJob.status}</Badge>
              <span>
                {(
                  {
                    prepare: "Preparing source text",
                    embed: "Embedding passages",
                    verify: "Verifying search",
                    query_verify: "Checking retrieval",
                    activate: "Activating knowledge",
                    cleanup: "Finishing",
                    completed: "All passages verified",
                  } as Record<string, string>
                )[syncJob.progress?.phase || ""] ||
                  syncJob.progress?.phase ||
                  "Waiting for worker"}
              </span>
              {syncJob.progress?.total != null && (
                <span>
                  {syncJob.progress.completed || 0} / {syncJob.progress.total}{" "}
                  passages
                </span>
              )}
              {["failed", "interrupted", "queued", "running"].includes(
                syncJob.status,
              ) && (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() =>
                    void mutate(
                      () =>
                        api(`/jobs/${syncJob.id}/resume`, { method: "POST" }),
                      "Resuming from the saved checkpoint.",
                    )
                  }
                >
                  Resume
                </Button>
              )}
            </div>
            {syncJob.error && (
              <p className="mt-3 text-destructive">{syncJob.error}</p>
            )}
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <CardTitle>Knowledge sources</CardTitle>
            <CardDescription>
              TXT and selectable-text PDF · 10 MB per file · Stored privately
            </CardDescription>
          </div>
          <Button
            variant="outline"
            disabled={locked || !data.initialized}
            onClick={() => fileInput.current?.click()}
          >
            <Upload data-icon="inline-start" />
            Upload sources
          </Button>
          <input
            ref={fileInput}
            type="file"
            accept=".txt,.pdf,text/plain,application/pdf"
            multiple
            hidden
            onChange={(event) => void uploadFiles(event.target.files)}
          />
          <input
            ref={replaceInput}
            type="file"
            accept=".txt,.pdf,text/plain,application/pdf"
            hidden
            onChange={(event) =>
              void uploadFiles(event.target.files, replacement || undefined)
            }
          />
        </CardHeader>
        <CardContent>
          {uploadProgress && (
            <p className="mb-4 break-words" role="status">
              {uploadProgress}
            </p>
          )}
          {data.sync_job && (
            <p className="help-copy mb-4">
              Synchronization in progress. Editing will unlock when the job
              completes or fails.
            </p>
          )}
          {data.sources.length ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead>Use after sync</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.sources.map((source) => (
                  <TableRow key={source.id}>
                    <TableCell className="min-w-40 max-w-72 whitespace-normal">
                      <strong className="break-words">{source.name}</strong>
                      <p className="help-copy">
                        {source.format.toUpperCase()} ·{" "}
                        {(source.size_bytes / 1024).toFixed(1)} KB
                        {source.format === "pdf"
                          ? ` · ${source.page_count} ${source.page_count === 1 ? "page" : "pages"}`
                          : ""}
                      </p>
                      <p className="help-copy">
                        Updated {new Date(source.updated_at).toLocaleString()}
                      </p>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          aria-label={`Use ${source.name} after sync`}
                          checked={source.enabled}
                          disabled={locked}
                          onCheckedChange={(enabled) =>
                            void mutate(
                              () =>
                                api(`/knowledge/sources/${source.id}`, {
                                  method: "PATCH",
                                  body: jsonBody({ enabled }),
                                }),
                              "Source setting saved. Sync knowledge to apply it.",
                            )
                          }
                        />
                        <span>{source.enabled ? "On" : "Off"}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => void openPreview(source)}
                        >
                          Preview
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={locked}
                          onClick={() => {
                            setReplacement(source);
                            replaceInput.current?.click();
                          }}
                        >
                          Replace
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={locked}
                          onClick={() => {
                            dialogTrigger.current =
                              document.activeElement as HTMLElement | null;
                            setRemoving(source);
                          }}
                        >
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <Empty>
              <EmptyHeader>
                <EmptyTitle>Add your first source</EmptyTitle>
                <EmptyDescription>
                  Upload a TXT or selectable-text PDF, review the extracted
                  text, then sync. Without searchable knowledge the bot uses a
                  general fallback.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Passage configuration</CardTitle>
          <CardDescription>
            {data.chunking.preprocessing === "legacy"
              ? "Sizes use characters. Current splitting follows heading and paragraph breaks. Saving new settings enables section headings on each passage."
              : "Sizes use characters. Headings stay with passages; overlap applies within a section and PDF page."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={configure} className="flex flex-col gap-4">
            <FieldGroup className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="global-chunk-size">Chunk size</FieldLabel>
                <Input
                  id="global-chunk-size"
                  type="number"
                  min={400}
                  max={2000}
                  step={1}
                  required
                  disabled={locked}
                  value={size}
                  onChange={(event) => setSize(Number(event.target.value))}
                />
                <FieldDescription>
                  400–2,000 characters per passage.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="global-chunk-overlap">Overlap</FieldLabel>
                <Input
                  id="global-chunk-overlap"
                  type="number"
                  min={0}
                  max={Math.min(400, Math.floor(size / 2))}
                  step={1}
                  required
                  disabled={locked}
                  value={overlap}
                  onChange={(event) => setOverlap(Number(event.target.value))}
                />
                <FieldDescription>
                  0–400 characters, at most half the chunk size.
                </FieldDescription>
              </Field>
            </FieldGroup>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                type="submit"
                disabled={locked || !configurationChanged}
              >
                Save configuration
              </Button>
              <Button variant="ghost" type="button" onClick={testKnowledge}>
                Open Playground
              </Button>
            </div>
            {configurationChanged && (
              <p className="help-copy">
                Save these settings before synchronizing.
              </p>
            )}
          </form>
        </CardContent>
      </Card>
      <Dialog
        open={!!viewSource}
        onOpenChange={(open) => {
          if (!open) {
            setViewSource(null);
            ++previewRequest.current;
          }
        }}
      >
        <DialogContent
          onCloseAutoFocus={restoreFocus}
          className="max-h-[90dvh] overflow-y-auto sm:max-w-4xl"
        >
          <DialogHeader>
            <DialogTitle className="break-all">{viewSource?.name}</DialogTitle>
            <DialogDescription>
              Preview the staged source with the saved passage configuration.
              Sync to use changes in conversations.
            </DialogDescription>
          </DialogHeader>
          {previewError ? (
            <Alert variant="destructive">
              <AlertTitle>Preview unavailable</AlertTitle>
              <AlertDescription>
                {previewError}
                <Button
                  variant="outline"
                  onClick={() => viewSource && void openPreview(viewSource)}
                >
                  Try again
                </Button>
              </AlertDescription>
            </Alert>
          ) : !preview ? (
            <p role="status">Loading preview…</p>
          ) : (
            <Tabs defaultValue={preview.format === "pdf" ? "original" : "text"}>
              <TabsList>
                <TabsTrigger value="original">Original</TabsTrigger>
                <TabsTrigger value="text">Text</TabsTrigger>
                <TabsTrigger value="chunks">
                  Passages ({preview.navigation_only ? 0 : preview.chunk_count})
                </TabsTrigger>
              </TabsList>
              <TabsContent value="original">
                {preview.format === "pdf" ? (
                  <iframe
                    title={`Original ${preview.name}`}
                    src={preview.url}
                    className="h-[55dvh] w-full rounded-md border"
                  />
                ) : (
                  <pre className="max-h-[55dvh] overflow-y-auto whitespace-pre-wrap break-words p-3 text-sm">
                    {preview.text}
                  </pre>
                )}
                <a
                  href={preview.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block underline"
                >
                  Open original file (link expires in 5 minutes)
                </a>
              </TabsContent>
              <TabsContent value="text">
                <Field>
                  <FieldLabel htmlFor="source-text">
                    {preview.format === "txt"
                      ? "Source text"
                      : "Extracted PDF text"}
                  </FieldLabel>
                  <Textarea
                    id="source-text"
                    className="min-h-72"
                    readOnly={preview.format !== "txt" || locked}
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                  />
                  <FieldDescription>
                    Check prices, tables and units. PDF text is read-only; use
                    Replace to upload a corrected original.
                  </FieldDescription>
                </Field>
                {preview.format === "txt" && (
                  <Button
                    className="mt-4"
                    disabled={locked || text === preview.text || !text.trim()}
                    onClick={() =>
                      viewSource &&
                      void mutate(async () => {
                        await uploadFile(
                          new File([text], preview.name, {
                            type: "text/plain",
                          }),
                          viewSource,
                        );
                        setViewSource(null);
                      }, "Text saved. Sync knowledge to apply it.")
                    }
                  >
                    Save text
                  </Button>
                )}
              </TabsContent>
              <TabsContent value="chunks">
                {preview.navigation_only ? (
                  <p className="help-copy">
                    This source provides the numbered navigation menu. It is not
                    embedded as factual knowledge.
                  </p>
                ) : (
                  <div className="flex flex-col gap-4">
                    {preview.chunks.map((chunk, i) => (
                      <article key={i} className="rounded-md border p-4">
                        <p className="help-copy">
                          Passage {passagePage * 10 + i + 1}
                          {chunk.metadata.page
                            ? ` · Page ${chunk.metadata.page}`
                            : ""}{" "}
                          · {chunk.text.length} characters
                        </p>
                        <p className="mt-2 whitespace-pre-wrap break-words">
                          {chunk.text}
                        </p>
                      </article>
                    ))}
                    <div className="flex items-center justify-between gap-3">
                      <Button
                        variant="outline"
                        disabled={passagePage === 0}
                        onClick={() => void loadPassages(passagePage - 1)}
                      >
                        Previous
                      </Button>
                      <span className="help-copy">
                        Page {passagePage + 1} of{" "}
                        {Math.max(1, Math.ceil(preview.chunk_count / 10))}
                      </span>
                      <Button
                        variant="outline"
                        disabled={(passagePage + 1) * 10 >= preview.chunk_count}
                        onClick={() => void loadPassages(passagePage + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!removing}
        onOpenChange={(open) => {
          if (!open) setRemoving(null);
        }}
      >
        <DialogContent onCloseAutoFocus={restoreFocus}>
          <DialogHeader>
            <DialogTitle>Delete this source?</DialogTitle>
            <DialogDescription>
              <span className="break-all">{removing?.name}</span> will leave the
              source list. Current bot knowledge changes only after a successful
              sync. Original files are cleaned up when no longer needed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemoving(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={locked}
              onClick={() =>
                removing &&
                void mutate(async () => {
                  await api(`/knowledge/sources/${removing.id}`, {
                    method: "DELETE",
                  });
                  setRemoving(null);
                }, "Source deleted. Sync knowledge to apply it.")
              }
            >
              Delete source
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
