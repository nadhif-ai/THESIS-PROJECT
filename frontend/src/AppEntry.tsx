import { lazy, Suspense } from "react";
import LandingPage from "./LandingPage";

const Workspace = lazy(() => import("./App"));

export default function AppEntry() {
  if (window.location.pathname === "/") return <LandingPage />;
  return (
    <Suspense fallback={<main className="p-12" role="status">Opening your workspace…</main>}>
      <Workspace />
    </Suspense>
  );
}
