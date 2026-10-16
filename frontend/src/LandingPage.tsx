import { useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";
import { Expand, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Spinner } from "@/components/ui/spinner";
import brandMark from "@/assets/brand-mark.png";
import printingDesk from "@/assets/printing-desk.jpg";
import dashboardImage from "@/assets/landing/dashboard.png";
import knowledgeImage from "@/assets/landing/knowledge.png";
import playgroundImage from "@/assets/landing/playground.png";
import conversationsImage from "@/assets/landing/conversations.png";
import providersImage from "@/assets/landing/providers.png";
import evaluationsImage from "@/assets/landing/evaluations.png";
import resultsImage from "@/assets/landing/evaluation-results.png";
import "./landing.css";

const captures = [
  { name: "Dashboard", src: dashboardImage, alt: "Dashboard showing published knowledge, recorded activity, and observed WhatsApp status", note: "Published knowledge, recent activity, and work that needs attention." },
  { name: "Knowledge", src: knowledgeImage, alt: "Knowledge workspace with a ready version, source documents, and publication controls", note: "A ready knowledge version, with its source documents and publication controls." },
  { name: "Playground", src: playgroundImage, alt: "Playground showing a saved print-file answer and the retrieved source passage beside it", note: "A saved benchmark reply, replayed in the Playground with its original source evidence." },
  { name: "Conversations", src: conversationsImage, alt: "Conversation history filtered to recorded evaluation questions and replies", note: "The Evaluation channel is shown here. Customer identities are not included." },
  { name: "Providers", src: providersImage, alt: "Provider settings with separate answering and scoring models and WhatsApp connection checks", note: "Answering and scoring models beside an observed WAHA session." },
  { name: "Evaluations", src: evaluationsImage, alt: "Evaluations workspace with dataset selection, reference review, and saved run history", note: "Dataset selection, reference review, and the history of saved evaluation runs." },
] as const;
type Capture = { name: string; src: string; alt: string; note: string };
const resultsCapture: Capture = {
  name: "Evaluation results",
  src: resultsImage,
  alt: "Saved evaluation results showing metric averages and individual cases with passes and scoring errors",
  note: "Saved metric scores and individual cases, including those that need attention.",
};
const workspaceHref = (name: string) => `/admin/#${encodeURIComponent(name === "Evaluation results" ? "Evaluations" : name)}`;

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <Button variant="ghost" size="icon" aria-label={`Switch to ${dark ? "light" : "dark"} theme`} onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
    </Button>
  );
}

function Screenshot({ capture, onEnlarge, priority = false, caption = true }: {
  capture: Capture;
  onEnlarge: (capture: Capture, trigger: HTMLElement) => void;
  priority?: boolean;
  caption?: boolean;
}) {
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  return (
    <figure className="landing-screenshot">
      <div className="landing-screenshot-frame">
        {state === "error" ? (
          <div className="landing-preview-error" role="alert">
            <strong>This workspace preview isn’t available.</strong>
            <p>You can retry the image or open the workspace to see this page.</p>
            <div className="landing-actions">
              <Button variant="outline" onClick={() => { setAttempt(attempt + 1); setState("loading"); }}>Retry preview</Button>
              <Button asChild><a href={workspaceHref(capture.name)}>Open {capture.name}</a></Button>
            </div>
          </div>
        ) : (
          <button className="landing-screenshot-button" onClick={event => onEnlarge(capture, event.currentTarget)} aria-label={`Enlarge the ${capture.name} workspace screenshot`} disabled={state !== "ready"}>
            <img
              key={attempt}
              src={capture.src + (attempt ? `?retry=${attempt}` : "")}
              alt={capture.alt}
              width={1440}
              height={1000}
              loading="eager"
              fetchPriority={priority ? "high" : "auto"}
              onLoad={() => setState("ready")}
              onError={() => setState("error")}
            />
            {state === "loading" && <span className="landing-preview-loading" role="status"><Spinner /> Loading the {capture.name} preview…</span>}
            <span className="landing-screenshot-toolbar"><span>{capture.name}</span><span>View full screen <Expand aria-hidden="true" /></span></span>
          </button>
        )}
      </div>
      {caption && <figcaption>{capture.note}</figcaption>}
    </figure>
  );
}

function DetailList({ items }: { items: { title: string; text: string }[] }) {
  return <dl className="landing-details">{items.map(item => <div key={item.title}><dt>{item.title}</dt><dd>{item.text}</dd></div>)}</dl>;
}

export default function LandingPage() {
  const [preview, setPreview] = useState<Capture | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const previewTrigger = useRef<HTMLElement | null>(null);
  const enlarge = (capture: Capture, trigger: HTMLElement) => {
    previewTrigger.current = trigger;
    setPreview(capture);
  };
  useEffect(() => {
    document.title = "Asia Visual Grafika · Printing support, ready for review";
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setMenuOpen(false); menuButton.current?.focus(); }
    };
    if (menuOpen) window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [menuOpen]);
  const navLinks = <>
    <a href="#workspace" onClick={() => setMenuOpen(false)}>The workspace</a>
    <a href="#capabilities" onClick={() => setMenuOpen(false)}>What you can do</a>
    <a href="#workflow" onClick={() => setMenuOpen(false)}>The workflow</a>
  </>;
  return (
    <div className="landing-page" id="top">
      <a className="skip-link" href="#landing-main" onClick={(event) => { event.preventDefault(); document.getElementById("landing-main")?.focus(); }}>Skip to content</a>
      <header className="landing-header">
        <div className="landing-header-inner">
          <a className="landing-brand" href="/" aria-label="Asia Visual Grafika home"><img src={brandMark} width={40} height={40} alt="" /><span><strong>Asia Visual Grafika</strong><small>Chatbot workspace</small></span></a>
          <nav className="landing-desktop-nav" aria-label="Page sections">{navLinks}</nav>
          <div className="landing-header-actions"><ThemeToggle /><a className="landing-sign-in" href="/admin/login">Sign in</a><Button asChild className="landing-header-cta"><a href="/admin/dashboard">Open dashboard</a></Button><Button ref={menuButton} variant="outline" className="landing-menu-toggle" aria-expanded={menuOpen} aria-controls="landing-mobile-nav" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? "Close" : "Menu"}</Button></div>
        </div>
        <nav className="landing-mobile-nav" id="landing-mobile-nav" aria-label="Mobile page navigation" hidden={!menuOpen}>{navLinks}<a href="/admin/login">Sign in</a><a href="/admin/dashboard">Open dashboard</a></nav>
      </header>

      <main id="landing-main" tabIndex={-1}>
        <section className="landing-hero landing-container" aria-labelledby="hero-title">
          <div className="landing-hero-copy">
            <h1 id="hero-title">Good answers begin with <span>your knowledge.</span></h1>
            <p>The workspace behind Asia Visual Grafika’s WhatsApp support. Prepare printing guidance, check the evidence behind an answer, and review what customers receive.</p>
            <div className="landing-actions"><Button asChild><a href="/admin/dashboard">Open your workspace</a></Button><a className="landing-text-link" href="#workflow">See the workflow</a></div>
            <p className="landing-access-note">Built for administrators. Customers stay on WhatsApp.</p>
          </div>
          <div className="landing-hero-preview" id="workspace">
            <div className="landing-preview-heading"><h2>Inside the workspace</h2><span>Actual product captures</span></div>
            <Tabs defaultValue="Playground" className="landing-preview-tabs">
              <TabsList aria-label="Choose a workspace preview" className="landing-tabs-list" variant="line">{captures.map(capture => <TabsTrigger key={capture.name} value={capture.name}>{capture.name}</TabsTrigger>)}</TabsList>
              {captures.map(capture => <TabsContent key={capture.name} value={capture.name}><Screenshot capture={capture} onEnlarge={enlarge} priority={capture.name === "Playground"} /></TabsContent>)}
            </Tabs>
            <p className="landing-capture-date">Captured 14 October 2026. Values and connection states reflect that snapshot.</p>
          </div>
        </section>

        <nav className="landing-chapters landing-container" aria-label="Workspace capabilities">
          <span>One answer pipeline.<br />Every stage in view.</span>
          <a href="#knowledge">Knowledge</a><a href="#playground">Playground</a><a href="#conversations">Conversations</a><a href="#providers">Providers & WhatsApp</a><a href="#evaluations">Evaluations</a>
        </nav>

        <div id="capabilities" className="landing-capabilities">
          <section className="landing-feature landing-container" id="knowledge" aria-labelledby="knowledge-title">
            <div className="landing-feature-copy">
              <h2 id="knowledge-title">Knowledge you can keep current.</h2>
              <p>Start with what the shop actually knows: materials, finishing, file requirements, prices, and policies. Prepare changes in a draft before putting them in front of customers.</p>
              <DetailList items={[
                { title: "Prepare the source", text: "Upload TXT, Markdown, PDF, and CSV documents; edit text-based files. Text-based PDFs can be read directly." },
                { title: "Inspect what gets retrieved", text: "Configure passage size and overlap, index the version, and inspect the passages behind future answers." },
                { title: "Publish after review", text: "Test a ready version, then publish it to WhatsApp. A previous ready version can be published again when you need to roll back." },
              ]} />
              <a className="landing-text-link" href={workspaceHref("Knowledge")}>Open Knowledge</a>
            </div>
            <div className="landing-feature-visual"><Screenshot capture={captures[1]} onEnlarge={enlarge} /><p className="landing-proof-note">Draft preparation and customer publication are separate steps.</p></div>
          </section>

          <section className="landing-playground" id="playground" aria-labelledby="playground-title">
            <div className="landing-container landing-feature landing-feature-reverse">
              <div className="landing-feature-copy">
                <h2 id="playground-title">A Playground with the evidence in view.</h2>
                <p>Ask the way a customer would. The Playground uses the same answer pipeline as WhatsApp, with room to examine the reply before publishing your changes.</p>
                <DetailList items={[
                  { title: "Choose what you’re testing", text: "Try a ready or published knowledge version in a separate workspace conversation." },
                  { title: "Read behind the reply", text: "See retrieved passages and their source files alongside the answer. Inspect response time, token usage, and available LangSmith traces." },
                ]} />
                <a className="landing-text-link" href={workspaceHref("Playground")}>Open Playground</a>
              </div>
              <div className="landing-feature-visual"><Screenshot capture={captures[2]} onEnlarge={enlarge} /><div className="landing-source-footnote"><span>Question</span><p>“File yang dikirim pakenya format apa? jpeg bisa?”</p><span>Retrieved source</span><p>Print-ready file guidance</p></div></div>
            </div>
          </section>

          <section className="landing-conversations landing-container" id="conversations" aria-labelledby="conversations-title">
            <div className="landing-section-heading"><h2 id="conversations-title">Conversations, with the reply still attached.</h2><div><p>Find the question, read the answer, and see where it came from. Filter WhatsApp, Playground, API, or evaluation activity, then search the message text.</p><a className="landing-text-link" href={workspaceHref("Conversations")}>Open Conversations</a></div></div>
            <div className="landing-ledger-visual"><Screenshot capture={captures[3]} onEnlarge={enlarge} /></div>
            <div className="landing-ledger-note"><strong>A record you can inspect.</strong><p>Question and answer previews, channel, response time, and received time stay together. Open a reply to read the full exchange.</p></div>
          </section>

          <section className="landing-providers landing-container" id="providers" aria-labelledby="providers-title">
            <div className="landing-provider-intro"><h2 id="providers-title">Keep Providers and WhatsApp in view.</h2><p>Choose the models that answer and score. Then follow the connection from the incoming customer message to the reply and its delivery receipt.</p></div>
            <div className="landing-provider-body"><div><DetailList items={[
              { title: "Model configuration", text: "Set the answering model, evaluation judge, and number of retrieved passages independently." },
              { title: "Observed connection", text: "Check the WAHA session, webhook configuration, reply worker, and the time the status was checked." },
              { title: "Message delivery", text: "Inspect queued and processing work, sent replies, and the latest received message and acknowledgement." },
            ]} /><a className="landing-text-link" href={workspaceHref("Providers")}>Open Providers</a><p className="landing-proof-note">Configured credentials and a live connection are distinct states.</p></div><Screenshot capture={captures[4]} onEnlarge={enlarge} /></div>
          </section>

          <section className="landing-evaluations" id="evaluations" aria-labelledby="evaluations-title">
            <div className="landing-container">
              <div className="landing-section-heading"><h2 id="evaluations-title">Evaluations that show their working.</h2><div><p>Review the reference answers and conversation scenarios, run a selected knowledge version, then inspect each case’s scores and reasons.</p><a className="landing-text-link" href={workspaceHref("Evaluations")}>Open Evaluations</a></div></div>
              <div className="landing-evaluation-body"><div className="landing-evaluation-notes"><DetailList items={[
                { title: "Review the references", text: "Check required facts, acceptable clarification, and expected outcomes. Changed references need another review." },
                { title: "Follow recorded progress", text: "See the current stage and completed cases and metrics as the run records them." },
                { title: "Read the case, not just the average", text: "Inspect faithfulness, relevancy, contextual precision and recall, and business correctness. Scoring errors are reported separately." },
                { title: "Keep the result", text: "Export saved results as JSON or open the linked LangSmith experiment for further inspection." },
              ]} /></div><Screenshot capture={resultsCapture} onEnlarge={enlarge} /></div>
            </div>
          </section>
        </div>

        <section className="landing-workflow landing-container" id="workflow" aria-labelledby="workflow-title">
          <div className="landing-workflow-intro"><h2 id="workflow-title">A review cycle you can repeat.</h2><p>Make changes in a draft, test the answer pipeline customers use, and publish when the knowledge is ready.</p><figure><img src={printingDesk} alt="Illustrative paper samples, a blue print proof, and a straightedge on a worktable" width={1200} height={800} loading="lazy" /><figcaption>Paper and proof, an illustrative composition.</figcaption></figure></div>
          <ol className="landing-workflow-steps">
            <li><span aria-hidden="true">01</span><div><h3>Prepare a draft</h3><p>Create a version and upload or edit the shop’s source documents.</p></div></li>
            <li><span aria-hidden="true">02</span><div><h3>Index and inspect</h3><p>Set the passage configuration, run indexing, and review the resulting sources.</p></div></li>
            <li><span aria-hidden="true">03</span><div><h3>Test the answers</h3><p>Ask customer questions in the Playground and evaluate against reviewed references.</p></div></li>
            <li><span aria-hidden="true">04</span><div><h3>Publish the ready version</h3><p>Activate the reviewed knowledge for WhatsApp customer replies.</p></div></li>
            <li><span aria-hidden="true">05</span><div><h3>Keep reviewing</h3><p>Follow the connection, inspect conversations, and bring changes into the next draft.</p></div></li>
          </ol>
        </section>

        <section className="landing-workspace-cta landing-container" aria-labelledby="workspace-cta-title"><h2 id="workspace-cta-title">Give the next answer<br /><span>a good place to start.</span></h2><div><p>Prepare a knowledge version, test a customer question, or pick up a reply that needs review.</p><div className="landing-actions"><Button asChild><a href="/admin/dashboard">Enter the workspace</a></Button><a className="landing-text-link" href="/admin/login">Sign in to your account</a></div><p className="landing-access-note">Administrator access. Orders and payments stay with the shop team.</p></div></section>
      </main>

      <footer className="landing-footer landing-container"><div><strong>Asia Visual Grafika</strong><span>Printing guidance, ready for review.</span></div><a href="#top">Back to top</a></footer>

      {preview && <Dialog open onOpenChange={open => { if (!open) setPreview(null); }}>
        <DialogContent className="landing-preview-dialog" onCloseAutoFocus={event => { event.preventDefault(); previewTrigger.current?.focus(); }}>
          <DialogHeader><DialogTitle>{preview?.name} workspace preview</DialogTitle><DialogDescription>{preview?.note} Captured 14 October 2026.</DialogDescription></DialogHeader>
          {preview && <div className="landing-dialog-image" role="region" aria-label="Workspace screenshot. Scroll to inspect the full capture." tabIndex={0}><img src={preview.src} alt={preview.alt} width={1440} height={1000} /></div>}
          <div className="landing-dialog-footer"><span>Light-theme capture. Scroll within the image to inspect the full capture.</span>{preview && <Button asChild><a href={workspaceHref(preview.name)}>Open {preview.name}</a></Button>}</div>
        </DialogContent>
      </Dialog>}
    </div>
  );
}
