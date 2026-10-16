import assert from "node:assert/strict";
import test from "node:test";
import { adminPagePath, readAdminPage } from "../frontend/src/lib/admin-navigation.ts";

for (const name of ["Dashboard", "Knowledge", "Playground", "Conversations", "Providers", "Evaluations"]) {
  test(`${name}: clean URL, direct load and legacy bookmark`, () => {
    const path = adminPagePath(name);
    assert.ok(path.startsWith("/admin/") && !path.includes("#"));
    assert.equal(readAdminPage({ pathname: path, hash: "" }), name);
    assert.equal(readAdminPage({ pathname: path + "/", hash: "" }), name);
    assert.equal(readAdminPage({ pathname: "/admin/", hash: "#" + name }), name);
    assert.equal(readAdminPage({ pathname: "/admin/", hash: "#" + name.toLowerCase() }), name);
  });
}

test("history uses the approved path and malformed hashes cannot break navigation", () => {
  assert.equal(adminPagePath("Conversations"), "/admin/history");
  assert.equal(adminPagePath("toString"), "/admin/dashboard");
  assert.equal(readAdminPage({ pathname: "/admin/", hash: "#%broken" }), "Dashboard");
  assert.equal(readAdminPage({ pathname: "/admin/login", hash: "" }), "Dashboard");
  assert.equal(readAdminPage({ pathname: "/admin/evaluations", hash: "#workspace-content" }), "Evaluations");
});
