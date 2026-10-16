import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider } from "next-themes";
import "./index.css";
import AppEntry from "./AppEntry.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      storageKey="avg-workspace-theme"
      disableTransitionOnChange
    >
      <AppEntry />
    </ThemeProvider>
  </StrictMode>,
);
