import type { Job, Version, WhatsAppStatus } from "./api";
import type { KnowledgeCatalog } from "@/components/knowledge-page";

type ReviewItem = { title: string; detail: string; action: string; page: string };

export function dashboardPriorities({ published, jobs, knowledge, whatsapp }: {
  published: Version | null;
  jobs: Job[];
  knowledge: KnowledgeCatalog | null;
  whatsapp: WhatsAppStatus | null;
}): ReviewItem[] {
  const items: ReviewItem[] = [];
  if (whatsapp?.provider === "waha") {
    const failed = whatsapp.attention?.failed ?? whatsapp.queue?.failed ?? 0;
    const uncertain = whatsapp.attention?.uncertain ?? whatsapp.queue?.uncertain ?? 0;
    if (failed + uncertain > 0) items.push({
      title: `${failed + uncertain} WhatsApp messages need review`,
      detail: `${failed} failed · ${uncertain} delivery uncertain. Inspect WhatsApp before retrying an uncertain send.`,
      action: "Review delivery", page: "Providers",
    });
    if (whatsapp.credentials_configured === false || whatsapp.webhook_configured === false) items.push({
      title: "WhatsApp configuration is incomplete",
      detail: "API credentials or the verified webhook callback are missing. A connected session alone does not confirm message intake.",
      action: "Review configuration", page: "Providers",
    });
    if (whatsapp.bot_replies_enabled === false) items.push({
      title: "Automatic WhatsApp replies are paused",
      detail: "New messages are recorded without a bot reply. Review the connection before turning replies on.",
      action: "Review WhatsApp", page: "Providers",
    });
    if (whatsapp.session_status && whatsapp.session_status !== "WORKING") items.push({
      title: whatsapp.session_status === "SCAN_QR_CODE" ? "WhatsApp needs a QR scan" : `WhatsApp session: ${whatsapp.session_status.replaceAll("_", " ").toLowerCase()}`,
      detail: "Open the connection checks for the current session and recovery steps.",
      action: "Check connection", page: "Providers",
    });
    if (whatsapp.execution_mode !== "vercel_queue" && !whatsapp.worker_running) items.push({
      title: "The reply worker is stopped",
      detail: "The local worker must be running to process incoming WhatsApp messages.",
      action: "Review processing", page: "Providers",
    });
  }
  const failedJobs = jobs.filter(job => ["failed", "interrupted"].includes(job.status));
  if (failedJobs.length) items.push({
    title: `${failedJobs.length} recent background ${failedJobs.length === 1 ? "task needs" : "tasks need"} review`,
    detail: "A recent task failed or was interrupted. Inspect its recorded error before resuming it.",
    action: "Review task", page: ["sync", "index"].includes(failedJobs[0].kind) ? "Knowledge" : "Evaluations",
  });
  if (!published?.chunk_count) items.push({
    title: knowledge?.sync_job ? "Initial knowledge sync is in progress" : "Customer knowledge is empty",
    detail: knowledge?.sync_job
      ? "Customer knowledge becomes available after the new snapshot is verified and activated."
      : "Factual questions have no active knowledge passages. Add sources and sync knowledge before testing shop guidance.",
    action: knowledge?.sync_job ? "View sync progress" : "Prepare knowledge", page: "Knowledge",
  });
  else if (published.compatible === false) items.push({
    title: "Active knowledge needs reindexing",
    detail: "The active snapshot does not match the configured embedding index. Review knowledge compatibility.",
    action: "Review knowledge", page: "Knowledge",
  });
  if (knowledge?.pending && !knowledge.sync_job) items.push({
    title: "Source changes are waiting to sync",
    detail: "Customer replies still use the previous active snapshot. Review changes and sync knowledge when ready.",
    action: "Review source changes", page: "Knowledge",
  });
  return items;
}
