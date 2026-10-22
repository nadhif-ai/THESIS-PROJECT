const paths: Record<string, string> = {
  Dashboard: "/admin/dashboard",
  Knowledge: "/admin/knowledge",
  Catalog: "/admin/catalog",
  Playground: "/admin/playground",
  Conversations: "/admin/history",
  Providers: "/admin/providers",
  Evaluations: "/admin/evaluations",
};

export function adminPagePath(name: string) {
  return Object.hasOwn(paths, name) ? paths[name] : paths.Dashboard;
}

export function readAdminPage(location: Pick<Location, "pathname" | "hash">) {
  const pathname = location.pathname.replace(/\/$/, "");
  if (["/admin", "/admin/login"].includes(pathname)) {
    try {
      const legacy = decodeURIComponent(location.hash.slice(1));
      const name = Object.keys(paths).find(
        (name) => name.toLowerCase() === legacy.toLowerCase(),
      );
      if (name) return name;
    } catch {
      return "Dashboard";
    }
  }
  return (
    Object.keys(paths).find((name) => paths[name] === pathname) || "Dashboard"
  );
}
