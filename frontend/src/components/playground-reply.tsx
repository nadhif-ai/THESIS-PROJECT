import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import type { Answer } from "@/lib/api";
import { Button } from "@/components/ui/button";

// Adapted from loading-ui.com/r/typing.json; motion uses the workspace stylesheet.
export function Typing() {
  return (
    <span role="status" className="playground-typing">
      {[0, 1, 2].map((index) => (
        <span key={index} aria-hidden="true" style={{ "--dot-index": index } as CSSProperties} />
      ))}
      <span className="sr-only">Preparing a reply</span>
    </span>
  );
}

// Interior's completed-text reveal pattern, using native animation frames and existing controls.
export function ReplyText({ text }: { text: string }) {
  const [visible, setVisible] = useState(0);
  const [skipped, setSkipped] = useState(false);
  useEffect(() => {
    if (skipped) return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;
    let cursor = 0;
    let last = performance.now();
    const revealAll = () => {
      if (media.matches) {
        cancelAnimationFrame(frame);
        setVisible(text.length);
      }
    };
    if (media.matches) {
      frame = requestAnimationFrame(() => setVisible(text.length));
      return () => cancelAnimationFrame(frame);
    }
    const tick = (now: number) => {
      cursor = Math.min(text.length, cursor + Math.min(now - last, 64) * 0.096);
      last = now;
      // Do not split surrogate pairs while revealing Indonesian text and emoji.
      let end = Math.floor(cursor);
      if (end > 0 && /[\uD800-\uDBFF]/.test(text[end - 1])) end -= 1;
      setVisible(end);
      if (cursor < text.length) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    media.addEventListener("change", revealAll);
    return () => {
      cancelAnimationFrame(frame);
      media.removeEventListener("change", revealAll);
    };
  }, [text, skipped]);
  const done = skipped || visible >= text.length;
  return (
    <div className="playground-reveal" aria-busy={!done}>
      <p className="playground-reveal-text" aria-hidden="true">
        <span className="playground-reveal-measure">{text}</span>
        <span className="playground-reveal-visible">{done ? text : text.slice(0, visible)}{!done && <span className="playground-caret" />}</span>
      </p>
      <span className="sr-only" role="status">{done ? text : "Revealing reply"}</span>
      {!done && <Button variant="ghost" size="sm" onClick={() => setSkipped(true)}>Show full reply</Button>}
    </div>
  );
}

export function GenerationDetails({ answer }: { answer: Answer }) {
  const stages = Object.entries(answer.media_decision?.model_usage ?? {})
    .filter(([, usage]) => usage.model && usage.requests !== 0)
    .sort(([a], [b]) => Number(b === "answer") - Number(a === "answer"));
  return (
    <div className="playground-generation">
      {stages.length ? stages.map(([stage, usage]) => (
        <span key={stage} title={`${usage.prompt_tokens ?? 0} input tokens · ${usage.completion_tokens ?? 0} output tokens`}>
          {stage === "answer" ? "Answer" : stage === "intent" ? "Intent" : "Validation"}: {usage.model}
          {" · "}{((usage.prompt_tokens ?? 0) + (usage.completion_tokens ?? 0)).toLocaleString()} tokens
        </span>
      )) : <span>{answer.answer_source && answer.answer_source !== "naive_rag" ? "Automatic reply" : "Model details unavailable"}</span>}
      {stages.length > 1 && <span>{(answer.usage.prompt_tokens + answer.usage.completion_tokens).toLocaleString()} tokens total</span>}
    </div>
  );
}
