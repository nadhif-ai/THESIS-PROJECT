import { useEffect, useState, type FormEvent } from "react";
import { ImagePlus, Pencil, Download, Search } from "lucide-react";
import { toast } from "sonner";
import { api, jsonBody, type Answer } from "@/lib/api";
import { providerModelLabel } from "@/lib/provider-models";
import { useResource } from "@/hooks/use-resource";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Field,
  FieldLabel,
  FieldDescription,
  FieldGroup,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from "@/components/ui/empty";

export type CatalogAsset = {
  asset_id: string;
  revision: number;
  category_id: string;
  product_type: string;
  covered_product_types: string[];
  role: string;
  enabled: boolean;
  aliases: string[];
  description: string;
  alt_text: string;
  caption: string;
  depicted_variants: string[];
  visual_attributes?: Partial<Record<"size" | "material" | "finish" | "type" | "shape", string[]>>;
  source_only_variants: string[];
  retrieval_keywords: string[];
  negative_retrieval_keywords: string[];
  url: string;
  width: number;
  height: number;
  sha256: string;
  is_ai_generated: boolean;
};
type Catalog = {
  assets: CatalogAsset[];
  revision: number;
  enabled: boolean;
  categories: Record<string, string>;
  products: Record<string, string[]>;
};
const roles: Record<string, string> = {
  hero: "Product hero",
  material_comparison: "Material comparison",
  form_comparison: "Form comparison",
  finishing_comparison: "Finish comparison",
  finishing_detail: "Finishing detail",
};
const editable = [
  "asset_id",
  "category_id",
  "product_type",
  "covered_product_types",
  "role",
  "enabled",
  "aliases",
  "description",
  "alt_text",
  "caption",
  "depicted_variants",
  "visual_attributes",
  "source_only_variants",
  "retrieval_keywords",
  "negative_retrieval_keywords",
] as const;
const blank = (): CatalogAsset => ({
  asset_id: "",
  revision: 0,
  category_id: "banner-spanduk",
  product_type: "banner-spanduk",
  covered_product_types: ["banner-spanduk"],
  role: "hero",
  enabled: true,
  aliases: [],
  description: "",
  alt_text: "",
  caption: "Ilustrasi produk.",
  depicted_variants: [],
  source_only_variants: [],
  retrieval_keywords: [],
  negative_retrieval_keywords: [],
  url: "",
  width: 0,
  height: 0,
  sha256: "",
  is_ai_generated: false,
});

export function CatalogPage() {
  const { data, error, reload } = useResource<Catalog>("/catalog", true);
  const [category, setCategory] = useState("");
  const [product, setProduct] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<CatalogAsset | null>(null);
  const [busy, setBusy] = useState(false);
  const [question, setQuestion] = useState("");
  const [preview, setPreview] = useState<Answer | null>(null);
  const [failure, setFailure] = useState("");
  const [previewSession] = useState(() => crypto.randomUUID());
  if (!data)
    return error ? (
      <Alert variant="destructive">
        <AlertTitle>Catalog unavailable</AlertTitle>
        <AlertDescription>
          {error}
          <Button variant="outline" onClick={reload}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    ) : (
      <Skeleton className="h-80 w-full" />
    );
  const assets = data.assets.filter(
    (a) =>
      (!category || a.category_id === category) &&
      (!product || a.covered_product_types.includes(product)) &&
      (!role || a.role === role) &&
      (!status || String(a.enabled) === status) &&
      `${a.asset_id} ${a.description} ${a.aliases.join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  async function feature(enabled: boolean) {
    setBusy(true);
    setFailure("");
    try {
      await api("/catalog/feature", {
        method: "PUT",
        body: jsonBody({ enabled }),
      });
      reload();
      toast.success(
        enabled
          ? "Catalog attachments enabled"
          : "Catalog attachments disabled",
      );
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function exportCatalog() {
    try {
      const result = await api("/catalog/export");
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(result, null, 2)], {
          type: "application/json",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "product-catalog.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setFailure((e as Error).message);
    }
  }
  async function tryPreview(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      setPreview(
        await api<Answer>("/playground", {
          method: "POST",
          body: jsonBody({ question, session_id: "catalog_" + previewSession }),
        }),
      );
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-medium">Product image catalog</h2>
          <p className="help-copy">
            {data.assets.length} images · seven printing groups · illustrations
            shown at their full proportions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={exportCatalog}>
            <Download data-icon="inline-start" />
            Export metadata
          </Button>
          <Button onClick={() => setEditing(blank())}>
            <ImagePlus data-icon="inline-start" />
            Add image
          </Button>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Requested catalog images</CardTitle>
          <CardDescription>
            Images only on request: one image, then price and product details. Playground previews
            never send WhatsApp messages.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Field orientation="horizontal">
            <FieldLabel htmlFor="catalog-feature">
              {data.enabled ? "Enabled" : "Disabled"}
            </FieldLabel>
            <Switch
              id="catalog-feature"
              checked={data.enabled}
              disabled={busy}
              onCheckedChange={feature}
            />
          </Field>
        </CardContent>
      </Card>
      {(failure || error) && (
        <Alert variant="destructive">
          <AlertTitle>Action could not be completed</AlertTitle>
          <AlertDescription>{failure || error}</AlertDescription>
        </Alert>
      )}
      <FieldGroup className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Field>
          <FieldLabel htmlFor="catalog-search">
            <Search aria-hidden="true" className="inline size-3" /> Search
          </FieldLabel>
          <Input
            id="catalog-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Product or description"
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="catalog-category">Group</FieldLabel>
          <NativeSelect
            id="catalog-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <NativeSelectOption value="">All groups</NativeSelectOption>
            {Object.entries(data.categories).map(([id, label]) => (
              <NativeSelectOption key={id} value={id}>
                {label}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="catalog-product">Product</FieldLabel>
          <NativeSelect
            id="catalog-product"
            value={product}
            onChange={(e) => setProduct(e.target.value)}
          >
            <NativeSelectOption value="">All products</NativeSelectOption>
            {Object.entries(data.products).map(([id, aliases]) => (
              <NativeSelectOption key={id} value={id}>
                {aliases[0]}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="catalog-role">Image purpose</FieldLabel>
          <NativeSelect
            id="catalog-role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <NativeSelectOption value="">All purposes</NativeSelectOption>
            {Object.entries(roles).map(([id, label]) => (
              <NativeSelectOption key={id} value={id}>
                {label}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="catalog-status">Status</FieldLabel>
          <NativeSelect
            id="catalog-status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <NativeSelectOption value="">All images</NativeSelectOption>
            <NativeSelectOption value="true">Enabled</NativeSelectOption>
            <NativeSelectOption value="false">Disabled</NativeSelectOption>
          </NativeSelect>
        </Field>
      </FieldGroup>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {assets.map((a) => (
          <Card key={a.asset_id} className="overflow-hidden">
            <CardContent className="p-0">
              <img
                src={a.url}
                alt={a.alt_text}
                loading="lazy"
                className="aspect-square w-full object-contain"
              />
            </CardContent>
            <CardHeader>
              <div className="flex flex-wrap gap-2">
                <Badge variant={a.enabled ? "secondary" : "outline"}>
                  {a.enabled ? "Enabled" : "Disabled"}
                </Badge>
                <Badge variant="outline">{roles[a.role]}</Badge>
              </div>
              <CardTitle>{a.alt_text}</CardTitle>
              <CardDescription>
                {data.categories[a.category_id]}
              </CardDescription>
            </CardHeader>
            <CardFooter className="justify-between">
              <span className="help-copy">
                {a.is_ai_generated ? "AI illustration" : "Catalog image"}
              </span>
              <Button variant="outline" size="sm" onClick={() => setEditing(a)}>
                <Pencil data-icon="inline-start" />
                Edit image
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      {assets.length === 0 && (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No matching images</EmptyTitle>
            <EmptyDescription>
              Change the filters or add an approved product image.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Preview a customer inquiry</CardTitle>
          <CardDescription>
            Uses active business knowledge and the same image selector as
            WhatsApp. Explicit image requests can be repeated in this preview conversation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={tryPreview}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="catalog-preview">
                  Customer question
                </FieldLabel>
                <Input
                  id="catalog-preview"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Lihat gambar perbandingan X-banner dan roll up dong"
                  required
                  maxLength={6000}
                />
              </Field>
              <Button type="submit" disabled={busy || !question.trim()}>
                Preview reply
              </Button>
            </FieldGroup>
          </form>
          {preview && (
            <div className="mt-4 flex flex-col gap-3" aria-live="polite">
              <MediaPreview answer={preview} />
              <p className="whitespace-pre-wrap">{preview.answer}</p>
            </div>
          )}
        </CardContent>
      </Card>
      {editing && (
        <AssetEditor
          key={editing.asset_id}
          asset={editing}
          catalog={data}
          close={() => setEditing(null)}
          saved={() => {
            setEditing(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

export function MediaPreview({ answer, diagnostics = true }: { answer: Answer; diagnostics?: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      {diagnostics && <p className="help-copy">
        Image decision:{" "}
        {answer.media_decision?.reason?.replaceAll("_", " ") ||
          "No image for this reply"}
      </p>}
      {diagnostics && answer.media_decision?.intent_resolution && (
        <details className="help-copy">
          <summary>Image selection details</summary>
          <div className="mt-2 grid gap-1 break-all">
            <p>Intent: {answer.media_decision.intent_resolution}</p>
            <p>Product: {answer.media_decision.product_ids?.join(", ") || "Unresolved"}</p>
            <p>Asset: {answer.media_decision.asset_id || "None"} · Catalog revision: {answer.media_decision.catalog_revision ?? "—"}</p>
            <p>Intent model: {answer.media_decision.intent_model ? providerModelLabel(answer.media_decision.intent_model) : "Not recorded"} · {answer.media_decision.intent_latency_seconds}s</p>
            <p>Prompt: {answer.media_decision.intent_prompt_sha256?.slice(0, 12)}</p>
            <p>App: {answer.media_decision.application_version}</p>
            <p>Answer check: {answer.media_decision.answer_validation || "Not required"}</p>
          </div>
        </details>
      )}
      {answer.media_selection && answer.media_url && (
        <figure>
          <img
            src={answer.media_url}
            alt={answer.media_selection.alt_text}
            className="max-h-80 w-full object-contain"
          />
          <figcaption className="help-copy">
            {answer.media_selection.caption} · Preview only
          </figcaption>
        </figure>
      )}
    </div>
  );
}

function AssetEditor({
  asset,
  catalog,
  close,
  saved,
}: {
  asset: CatalogAsset;
  catalog: Catalog;
  close: () => void;
  saved: () => void;
}) {
  const [draft, setDraft] = useState(asset);
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState("");
  useEffect(
    () => () => {
      if (filePreview) URL.revokeObjectURL(filePreview);
    },
    [filePreview],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const dirty =
    file !== null || JSON.stringify(draft) !== JSON.stringify(asset);
  function change<K extends keyof CatalogAsset>(
    key: K,
    value: CatalogAsset[K],
  ) {
    setDraft((d) => ({ ...d, [key]: value }));
  }
  function requestClose() {
    if (!busy && (!dirty || window.confirm("Discard unsaved image changes?")))
      close();
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      let upload_id: string | undefined;
      if (file) {
        if (
          !["image/png", "image/jpeg"].includes(file.type) ||
          file.size > 10 * 1024 * 1024
        )
          throw new Error("Choose a PNG or JPEG image up to 10 MB.");
        const ticket = await api<{ upload_id: string; url: string }>(
          "/catalog/uploads",
          {
            method: "POST",
            body: jsonBody({ mime_type: file.type, size_bytes: file.size }),
          },
        );
        const response = await fetch(ticket.url, {
          method: "PUT",
          headers: { "Content-Type": file.type },
          body: file,
        });
        if (!response.ok)
          throw new Error(
            "Image upload failed. The active image has not changed.",
          );
        upload_id = ticket.upload_id;
      }
      const fields = Object.fromEntries(
        editable.map((key) => [key, draft[key]]),
      );
      await api("/catalog/assets/" + draft.asset_id, {
        method: "PUT",
        body: jsonBody({
          ...fields,
          expected_revision: asset.revision,
          upload_id,
        }),
      });
      toast.success("Saved. This image setting is active.");
      saved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) requestClose();
      }}
    >
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {asset.revision ? "Edit catalog image" : "Add catalog image"}
          </DialogTitle>
          <DialogDescription>
            Save confirms this image for customer use and activates the changes
            immediately.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={save}>
          <FieldGroup>
            {(filePreview || asset.url) && (
              <img
                src={filePreview || asset.url}
                alt={asset.alt_text}
                className="max-h-64 w-full object-contain"
              />
            )}
            <Field>
              <FieldLabel htmlFor="asset-file">
                {asset.revision ? "Replace image (optional)" : "Product image"}
              </FieldLabel>
              <Input
                id="asset-file"
                type="file"
                accept="image/png,image/jpeg"
                required={!asset.revision}
                onChange={(e) => {
                  const next = e.target.files?.[0] || null;
                  setFile(next);
                  setFilePreview(next ? URL.createObjectURL(next) : "");
                }}
              />
              <FieldDescription>
                Still PNG/JPEG, up to 10 MB. Full image proportions are
                preserved.
              </FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="asset-id">Catalog identifier</FieldLabel>
              <Input
                id="asset-id"
                required
                pattern="[a-z0-9][a-z0-9-]{2,99}"
                value={draft.asset_id}
                disabled={asset.revision > 0}
                onChange={(e) => change("asset_id", e.target.value)}
                placeholder="roll-up-studio-hero"
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="asset-category">Group</FieldLabel>
              <NativeSelect
                id="asset-category"
                value={draft.category_id}
                onChange={(e) => change("category_id", e.target.value)}
              >
                {Object.entries(catalog.categories).map(([id, label]) => (
                  <NativeSelectOption key={id} value={id}>
                    {label}
                  </NativeSelectOption>
                ))}
              </NativeSelect>
            </Field>
            <Field>
              <FieldLabel htmlFor="asset-product">Primary product</FieldLabel>
              <NativeSelect
                id="asset-product"
                value={draft.product_type}
                onChange={(e) => {
                  change("product_type", e.target.value);
                  change("covered_product_types", [e.target.value]);
                }}
              >
                {Object.entries(catalog.products).map(([id, aliases]) => (
                  <NativeSelectOption key={id} value={id}>
                    {aliases[0]}
                  </NativeSelectOption>
                ))}
                <NativeSelectOption value="standing-banner-comparison">
                  Standing banner comparison
                </NativeSelectOption>
              </NativeSelect>
            </Field>
            <Field>
              <FieldLabel htmlFor="asset-role">Image purpose</FieldLabel>
              <NativeSelect
                id="asset-role"
                value={draft.role}
                onChange={(e) => change("role", e.target.value)}
              >
                {Object.entries(roles).map(([id, label]) => (
                  <NativeSelectOption key={id} value={id}>
                    {label}
                  </NativeSelectOption>
                ))}
              </NativeSelect>
            </Field>
            <Field>
              <FieldLabel htmlFor="asset-coverage">
                Products shown together
              </FieldLabel>
              <NativeSelect
                id="asset-coverage"
                multiple
                className="h-36"
                value={draft.covered_product_types}
                onChange={(e) =>
                  change(
                    "covered_product_types",
                    Array.from(e.target.selectedOptions, (o) => o.value),
                  )
                }
              >
                {Object.entries(catalog.products).map(([id, aliases]) => (
                  <NativeSelectOption key={id} value={id}>
                    {aliases[0]}
                  </NativeSelectOption>
                ))}
              </NativeSelect>
              <FieldDescription>
                For comparisons, select every depicted product. Use Ctrl/Command
                to select several.
              </FieldDescription>
            </Field>
            {(["description", "alt_text", "caption"] as const).map((key) => (
              <Field key={key}>
                <FieldLabel htmlFor={"asset-" + key}>
                  {
                    {
                      description: "Description",
                      alt_text: "Image description for accessibility",
                      caption: "WhatsApp caption",
                    }[key]
                  }
                </FieldLabel>
                <Textarea
                  id={"asset-" + key}
                  required
                  maxLength={
                    key === "caption" ? 240 : key === "alt_text" ? 400 : 2500
                  }
                  value={draft[key]}
                  onChange={(e) => change(key, e.target.value)}
                />
              </Field>
            ))}
            {(
              [
                "aliases",
                "depicted_variants",
                "source_only_variants",
                "retrieval_keywords",
                "negative_retrieval_keywords",
              ] as const
            ).map((key) => (
              <Field key={key}>
                <FieldLabel htmlFor={"asset-" + key}>
                  {
                    {
                      aliases: "Alternative product names",
                      depicted_variants: "Visibly depicted variants",
                      source_only_variants: "Available variants not depicted",
                      retrieval_keywords: "Matching terms",
                      negative_retrieval_keywords: "Exclusion hints",
                    }[key]
                  }
                </FieldLabel>
                <Textarea
                  id={"asset-" + key}
                  value={draft[key].join("\n")}
                  onChange={(e) => change(key, e.target.value.split("\n"))}
                />
                <FieldDescription>
                  One term per line. Images do not establish exact stock or
                  prices.
                </FieldDescription>
              </Field>
            ))}
            {(["size", "material", "finish", "type", "shape"] as const).map((attribute) => (
              <Field key={attribute}>
                <FieldLabel htmlFor={"visual-" + attribute}>
                  Verified visual {attribute}
                </FieldLabel>
                <Textarea id={"visual-" + attribute}
                  value={(draft.visual_attributes?.[attribute] || []).join("\n")}
                  onChange={(e) => change("visual_attributes", {...draft.visual_attributes,
                    [attribute]: e.target.value.split("\n").filter((v) => v.trim())})} />
                <FieldDescription>One verified value per line. Leave empty when the illustration cannot establish this property.</FieldDescription>
              </Field>
            ))}
            <Field orientation="horizontal">
              <FieldLabel htmlFor="asset-enabled">
                Eligible for customer replies
              </FieldLabel>
              <Switch
                id="asset-enabled"
                checked={draft.enabled}
                onCheckedChange={(v) => change("enabled", v)}
              />
            </Field>
            {asset.revision > 0 && (
              <p className="help-copy">
                Revision {asset.revision} · {asset.width} × {asset.height} ·{" "}
                {asset.is_ai_generated ? "AI illustration" : "Catalog image"}
              </p>
            )}
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Image not saved</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div className="flex items-center justify-between gap-3">
              <p className="help-copy" aria-live="polite">
                {busy
                  ? "Saving…"
                  : dirty
                    ? "Unsaved changes"
                    : "No unsaved changes"}
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={requestClose}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={busy || (!dirty && asset.revision > 0)}
                >
                  Save image
                </Button>
              </div>
            </div>
          </FieldGroup>
        </form>
      </DialogContent>
    </Dialog>
  );
}
