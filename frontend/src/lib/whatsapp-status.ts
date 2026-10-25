import type { WhatsAppStatus } from "./api";

export function replyProcessing(status: Pick<WhatsAppStatus, "execution_mode" | "worker_running">) {
  if (status.execution_mode === "vercel_queue") {
    return {
      title: "Reply processing",
      ready: undefined,
      detail: "Vercel Queues is configured; no local polling worker is required. Recent replies and delivery receipts confirm processing.",
    };
  }
  return {
    title: "Reply worker",
    ready: status.worker_running,
    detail: status.worker_running
      ? "The local inbox worker is running."
      : "The reply worker is stopped. Keep the backend running with the WAHA provider enabled.",
  };
}
