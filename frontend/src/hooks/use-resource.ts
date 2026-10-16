import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Job, Version } from "@/lib/api";
import { invalidateAdmin, queryClient, resourceKey } from "@/lib/query-client";

function jobsIn(path: string | null, data: unknown): Job[] {
  if (path === "/jobs") return (data as Job[] | undefined) || [];
  if (path === "/overview") return (data as { jobs?: Job[] } | undefined)?.jobs || [];
  return [];
}

function resourceOptions<T>(path: string) {
  return {
    queryKey: resourceKey(path),
    queryFn: async ({ signal }: { signal: AbortSignal }) => {
      const previous = queryClient.getQueryData<T>(resourceKey(path));
      const data = await api<T>(path, { signal });
      const before = jobsIn(path, previous);
      const finished = previous != null && jobsIn(path, data).some((job) =>
        ["completed", "failed", "interrupted"].includes(job.status) &&
        before.find((old) => old.id === job.id)?.status !== job.status,
      );
      if (finished) {
        void invalidateAdmin(...[
          "/versions", "/evaluations/dataset", "/conversations", "/overview", "/jobs/",
        ].filter((route) => route !== path));
      }
      return data;
    },
  };
}

let prefetching = false;
export async function prefetchResource(path: string) {
  if (prefetching) return;
  prefetching = true;
  try {
    await queryClient.query(resourceOptions(path));
  } catch {
    // The mounted section owns error feedback and retry.
  } finally {
    prefetching = false;
  }
}

export function useResource<T>(path: string | null, poll = true) {
  const query = useQuery<T>({
    ...resourceOptions<T>(path || ""),
    enabled: path !== null,
    refetchInterval: poll ? (query) => {
      const data = query.state.data;
      const active = jobsIn(path, data).some((job) => ["queued", "running"].includes(job.status));
      const indexing = path === "/versions" && (data as { versions: Version[] } | undefined)
        ?.versions.some((version) => version.status === "indexing");
      return active || indexing ? 3_000 : 20_000;
    } : false,
  });
  const reload = useCallback(() => {
    if (path) void queryClient.invalidateQueries({ queryKey: resourceKey(path) }, { cancelRefetch: false });
  }, [path]);
  return {
    data: query.data ?? null,
    error: query.error?.message || "",
    reload,
    refreshing: query.isFetching,
    updatedAt: query.dataUpdatedAt ? new Date(query.dataUpdatedAt).toISOString() : null,
  };
}
