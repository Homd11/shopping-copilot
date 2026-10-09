import type { RequestHandler, Response } from "express";
import { timingSafeEqual } from "node:crypto";
import {
  ShopperRegistry,
  credentialDigest,
  type ShopperState,
} from "./shopper-state.js";

export function equalSecret(actual: unknown, expected: string): boolean {
  if (typeof actual !== "string" || !expected) return false;
  const a = Buffer.from(actual),
    b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}
export function cookieValue(header: string | undefined, name: string): string {
  const entries = (header ?? "")
    .split(";")
    .map((part) => part.trim())
    .filter((part) => part.startsWith(name + "="));
  return entries.length === 1 ? entries[0].slice(name.length + 1) : "";
}
export function shopper(response: Response): ShopperState {
  return response.locals.shopper as ShopperState;
}
export function shopperHttp(
  registry: ShopperRegistry,
  options: { origin: string; secure: boolean; evaluation: boolean },
): RequestHandler {
  return (request, response, next) => {
    if (
      request.path === "/__catalogue/v1/products" &&
      request.method === "GET"
    ) {
      next();
      return;
    }
    if (
      request.path.toLowerCase().startsWith("/__test/") &&
      !options.evaluation
    ) {
      response.sendStatus(404);
      return;
    }
    let state = registry.resolve(
      cookieValue(request.headers.cookie, "copilot_store"),
      false,
    );
    const safe = request.method === "GET" || request.method === "HEAD";
    // Only a navigation/bootstrap starts an identity, never a mutation or private read.
    if (
      !state &&
      safe &&
      (request.path === "/" ||
        request.path === "/__shopper" ||
        request.path.startsWith("/p/") ||
        request.path.startsWith("/c/"))
    ) {
      const created = registry.create();
      if (!created) {
        response.status(503).json({ error: "shopper_capacity" });
        return;
      }
      state = created.state;
      response.cookie("copilot_store", created.credential, {
        httpOnly: true,
        secure: options.secure,
        sameSite: "strict",
        path: "/",
      });
    }
    if (!state) {
      response.status(401).json({ error: "shopper_expired" });
      return;
    }
    if (
      !safe &&
      (request.headers.origin !== options.origin ||
        !equalSecret(
          request.headers["x-csrf-token"] ?? request.body?.copilot_csrf,
          state.csrf,
        ))
    ) {
      response.status(403).json({ error: "invalid_browser_authority" });
      return;
    }
    // Authenticated browser activity extends commerce expiry; private probes do not.
    registry.resolve(cookieValue(request.headers.cookie, "copilot_store"));
    response.locals.shopper = state;
    response.set("Cache-Control", "no-store");
    const send = response.send.bind(response);
    response.send = (body: unknown) => {
      if (typeof body === "string" && body.startsWith("<!doctype html>")) {
        body = body
          .replace(
            "</head>",
            '<meta name="copilot-csrf" content="' +
              state.csrf +
              '" /><meta name="copilot-context" content="' +
              credentialDigest(
                state.binding.shopper_id + ":" + state.binding.generation,
              ) +
              '" /></head>',
          )
          .replace(
            /(<form\b[^>]*\bmethod="post"[^>]*>)/gi,
            '$1<input type="hidden" name="copilot_csrf" data-sensitive="true" value="' +
              state.csrf +
              '" />',
          );
      }
      return send(body);
    };
    next();
  };
}
