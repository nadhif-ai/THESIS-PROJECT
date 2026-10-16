import { QueryClient } from "@tanstack/react-query";

export function isTransientReadError(error: Error) {
  return error instanceof TypeError || error.name === "TimeoutError" ||
    [502, 503, 504].includes((error as Error & { status?: number }).status || 0);
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 20_000,
      gcTime: Infinity,
      retry: (failures, error) => failures < 2 && isTransientReadError(error),
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 15_000),
      refetchIntervalInBackground: false,
    },
  },
});

export function resourceKey(path: string) {
  const [route, search = ""] = path.split("?");
  return ["admin", route, search] as const;
}

export function invalidateAdmin(...paths: string[]) {
  return queryClient.invalidateQueries(
    {
      predicate: (query) => {
        const [scope, route] = query.queryKey;
        return scope === "admin" && typeof route === "string" && paths.some(
          (path) => route === path || route.startsWith(path.endsWith("/") ? path : path + "/"),
        );
      },
    },
    { cancelRefetch: false },
  );
}
