import { useEffect, useRef, useState } from "react";
import { api, jsonBody } from "@/lib/api";
import { useResource } from "@/hooks/use-resource";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Field, FieldLabel, FieldDescription } from "@/components/ui/field";

type PromptSetting = {
  prompt: string;
  default_prompt: string;
  prompt_sha256: string;
  max_length: number;
};

export function PromptEditor() {
  const resource = useResource<PromptSetting>("/knowledge/prompt", false);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Global system prompt</CardTitle>
        <CardDescription>
          Set the bot’s conversational Indonesian. Save applies to new requests immediately;
          knowledge synchronization is separate. Running evaluations keep their captured prompt.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {resource.data ? <PromptForm initial={resource.data} /> : (
          <div role={resource.error ? "alert" : "status"}>
            {resource.error || "Loading conversational instructions…"}
            {resource.error && <Button variant="outline" onClick={resource.reload}>Try again</Button>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PromptForm({ initial }: { initial: PromptSetting }) {
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial.prompt);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);
  const returnFocus = useRef(false);
  const dirty = draft !== saved.prompt;
  const validation = !draft.trim()
    ? "Enter conversational instructions before saving."
    : draft.length > saved.max_length
      ? "Use at most 12,000 characters."
      : [...draft].some((character) => {
          const code = character.codePointAt(0)!;
          return (code < 32 && ![9, 10, 13].includes(code)) || (code >= 127 && code <= 159) || (code >= 0xd800 && code <= 0xdfff);
        })
        ? "Remove unsupported control characters."
        : "";

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  useEffect(() => {
    if (!busy && returnFocus.current) {
      textarea.current?.focus({ preventScroll: true });
      returnFocus.current = false;
    }
  }, [busy]);

  async function save() {
    if (validation || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api<PromptSetting>("/knowledge/prompt", {
        method: "PUT", body: jsonBody({ prompt: draft }),
      });
      setSaved(result);
      setDraft(result.prompt);
      setNotice("Saved. New WhatsApp and Playground requests use these instructions.");
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Prompt could not be saved. Try again.");
    } finally {
      returnFocus.current = true;
      setBusy(false);
    }
  }

  return (
          <form className="flex flex-col gap-4" onSubmit={(event) => { event.preventDefault(); void save(); }}>
            <Field>
              <FieldLabel htmlFor="global-system-prompt">Conversational instructions</FieldLabel>
              <Textarea
                id="global-system-prompt"
                ref={textarea}
                value={draft}
                disabled={busy}
                required
                className="min-h-80"
                aria-describedby="prompt-boundaries prompt-count prompt-validation"
                aria-invalid={!!validation}
                onChange={(event) => { setDraft(event.target.value); setNotice(""); setError(""); }}
              />
              <FieldDescription id="prompt-boundaries">
                Edit tone, brevity, examples and clarification style here. Business facts and prices
                come from knowledge. Grounding, safety, calculation rules and WhatsApp text formatting
                remain protected. Greetings, menu, reset and brief acknowledgements use built-in replies.
              </FieldDescription>
              <FieldDescription id="prompt-count">
                {draft.length.toLocaleString()} / {saved.max_length.toLocaleString()} characters
              </FieldDescription>
            </Field>
            <p id="prompt-validation" className="text-sm text-destructive" role="alert">{validation || error}</p>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={busy || !dirty || !!validation}>{busy ? "Saving…" : "Save"}</Button>
              <Button type="button" variant="outline" disabled={busy || draft === saved.default_prompt}
                onClick={() => { setDraft(saved.default_prompt); setNotice("Default instructions loaded. Save to apply them."); setError(""); }}>
                Restore Default
              </Button>
              {dirty && <Button type="button" variant="ghost" disabled={busy}
                onClick={() => { setDraft(saved.prompt); setNotice(""); setError(""); }}>Discard changes</Button>}
            </div>
            <p className="help-copy" role="status" aria-live="polite">
              {notice || (dirty ? "Unsaved changes. Save before leaving this page." : "All changes saved.")}
            </p>
          </form>
  );
}
