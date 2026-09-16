import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import { executeAction } from "../src/actions.js";
import { SnapshotBuilder } from "../src/snapshot.js";
import type { NavigateAction, TypeAction } from "../src/types.js";

function actionBase() {
  return {
    v: 1 as const,
    task_id: "task-1",
    action_id: "action-1",
    sequence_number: 1,
    narration: "Applying the filters.",
  };
}

describe("executeAction", () => {
  it("blocks off-origin navigation at the execution boundary", async () => {
    const dom = new JSDOM("<!doctype html><title>Store</title>", {
      url: "http://localhost:4000/",
    });
    const builder = new SnapshotBuilder(dom.window.document, {
      isVisible: () => true,
    });
    const action: NavigateAction = {
      ...actionBase(),
      type: "navigate",
      url: "https://attacker.example/leave",
    };

    const result = await executeAction(action, {
      builder,
      currentUrl: () => "http://localhost:4000/",
      navigate: async () => undefined,
      settle: async () => undefined,
    });

    expect(result.status).toBe("blocked");
    expect(result.snapshot.url).toBe("http://localhost:4000/");
  });

  it("refuses to type into a Sensitive Field", async () => {
    const dom = new JSDOM(
      `<!doctype html><html><body>
      <label for="card">Card number</label>
      <input id="card" autocomplete="cc-number" value="">
    </body></html>`,
      { url: "http://localhost:4000/checkout" },
    );
    const builder = new SnapshotBuilder(dom.window.document, {
      isVisible: () => true,
    });
    const sensitive = builder.build().elements[0];
    const action: TypeAction = {
      ...actionBase(),
      type: "type",
      id: sensitive.id,
      text: "4111111111111111",
      submit: false,
    };

    const result = await executeAction(action, {
      builder,
      currentUrl: () => "http://localhost:4000/checkout",
      navigate: async () => undefined,
      settle: async () => undefined,
    });

    expect(result.status).toBe("blocked");
    expect(dom.window.document.querySelector("input")?.value).toBe("");
  });

  it("returns a fresh filtered Snapshot after same-origin navigation", async () => {
    const dom = new JSDOM(
      '<!doctype html><html lang="ar"><title>الرئيسية</title><body></body></html>',
      {
        url: "http://localhost:4000/",
      },
    );
    let currentUrl = "http://localhost:4000/";
    const builder = new SnapshotBuilder(dom.window.document, {
      isVisible: () => true,
      url: () => currentUrl,
    });
    const action: NavigateAction = {
      ...actionBase(),
      type: "navigate",
      url: "/c/shoes?type=running&max_price=2000",
    };

    const result = await executeAction(action, {
      builder,
      currentUrl: () => currentUrl,
      navigate: async (url) => {
        currentUrl = url.href;
        dom.window.document.title = "الأحذية";
        dom.window.document.body.innerHTML = "<main><h1>3 منتجات</h1></main>";
      },
      settle: async () => undefined,
    });

    expect(result.status).toBe("navigated");
    expect(result.snapshot.url).toContain("type=running&max_price=2000");
    expect(result.snapshot.elements).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ role: "heading", name: "3 منتجات" }),
      ]),
    );
  });
});
