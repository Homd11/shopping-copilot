import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function identityConfig() {
  const path = resolve(
    dirname(fileURLToPath(import.meta.url)),
    "../../work/local-identity.json",
  );
  const saved = existsSync(path)
    ? (JSON.parse(readFileSync(path, "utf8")) as { secret?: string })
    : {};
  const secret = process.env.COPILOT_SERVICE_SECRET ?? saved.secret ?? "";
  if (secret.length < 32)
    throw new Error(
      "Run scripts/init_local_identity.py before starting services.",
    );
  const origin = process.env.COPILOT_STORE_ORIGIN ?? "http://localhost:4000";
  const panelOrigin =
    process.env.COPILOT_PANEL_ORIGIN ?? "http://localhost:4100";
  for (const raw of [origin, panelOrigin]) {
    const value = new URL(raw);
    const local = ["localhost", "127.0.0.1", "[::1]"].includes(value.hostname);
    if (
      value.origin !== raw ||
      value.username ||
      value.password ||
      !["http:", "https:"].includes(value.protocol) ||
      (value.protocol === "http:" &&
        (!local || process.env.COPILOT_ENV === "production"))
    )
      throw new Error("Invalid configured public origin");
  }
  return {
    serviceSecret: secret,
    origin,
    panelOrigin,
    evaluation: process.env.COPILOT_EVALUATION === "1",
  };
}
