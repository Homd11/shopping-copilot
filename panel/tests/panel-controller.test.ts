import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import {
  PanelController,
  type AgentEvent,
  type AgentTransport,
  type StorefrontChannel,
} from "../src/panel.js";

const snapshot = {
  v: 1 as const,
  url: "http://localhost:4000/",
  title: "المتجر التجريبي",
  lang: "ar",
  viewport: { w: 390, h: 844, scrollY: 0 },
  truncated: false,
  elements: [],
};

function setup() {
  const dom = new JSDOM('<!doctype html><div id="app"></div>');
  const submitted: Array<{
    sessionId: string;
    text: string;
    snapshot: unknown;
  }> = [];
  const results: unknown[] = [];
  const stopped: string[] = [];
  let eventHandler: ((event: AgentEvent) => void) | undefined;
  const agent: AgentTransport = {
    createSession: async () => "session-1",
    subscribe: (_sessionId, handler) => {
      eventHandler = handler;
      return () => undefined;
    },
    submitMessage: async (sessionId, text, currentSnapshot) => {
      submitted.push({ sessionId, text, snapshot: currentSnapshot });
    },
    submitActionResult: async (_sessionId, result) => {
      results.push(result);
    },
    stop: async (sessionId) => {
      stopped.push(sessionId);
    },
  };
  const actions: unknown[] = [];
  let snapshotRequests = 0;
  const storefront: StorefrontChannel = {
    sendAction: (action) => actions.push(action),
    requestSnapshot: () => snapshotRequests++,
  };
  const root = dom.window.document.querySelector<HTMLElement>("#app")!;
  const controller = new PanelController(root, agent, storefront);
  return {
    dom,
    root,
    controller,
    submitted,
    results,
    stopped,
    actions,
    snapshotRequests: () => snapshotRequests,
    emit: (event: AgentEvent) => eventHandler?.(event),
  };
}

describe("PanelController", () => {
  it("shows the task surface and submits a Shopper message with the current Snapshot", async () => {
    const context = setup();
    await context.controller.start();
    expect(context.snapshotRequests()).toBe(1);
    const input =
      context.root.querySelector<HTMLInputElement>("#shopper-message")!;
    expect(input.disabled).toBe(true);

    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    expect(input.disabled).toBe(false);

    input.value = "عاوز كوتشي للجري بأقل من ٢٠٠٠";
    context.root.querySelector<HTMLFormElement>("form")!.dispatchEvent(
      new context.dom.window.Event("submit", {
        bubbles: true,
        cancelable: true,
      }),
    );
    await Promise.resolve();

    expect(context.root.querySelector('[role="status"]')).not.toBeNull();
    expect(context.root.querySelector("#stop-task")).not.toBeNull();
    expect(context.submitted).toEqual([
      { sessionId: "session-1", text: input.value, snapshot },
    ]);
    expect(context.root.querySelector("#conversation")?.textContent).toContain(
      input.value,
    );
  });

  it("relays ordered Agent Actions and matching Bridge results", async () => {
    const context = setup();
    await context.controller.start();
    const action = {
      v: 1 as const,
      type: "navigate" as const,
      task_id: "task-1",
      action_id: "action-1",
      sequence_number: 1,
      narration: "هفلتر المنتجات.",
      url: "/c/shoes?type=running&max_price=2000",
    };

    context.emit({ type: "narration", data: { text: action.narration } });
    context.emit({ type: "action", data: { action } });
    context.controller.receiveStorefront({
      type: "action_result",
      result: {
        v: 1,
        task_id: "task-1",
        action_id: "action-1",
        sequence_number: 1,
        status: "navigated",
        snapshot,
      },
    });
    await Promise.resolve();

    expect(context.root.querySelector('[role="status"]')?.textContent).toBe(
      action.narration,
    );
    expect(context.actions).toEqual([action]);
    expect(context.results).toHaveLength(1);
  });

  it("keeps Stop reachable and sends it to the active session", async () => {
    const context = setup();
    await context.controller.start();

    context.root.querySelector<HTMLButtonElement>("#stop-task")!.click();
    await Promise.resolve();

    expect(context.stopped).toEqual(["session-1"]);
  });

  it("keeps English task completion in English", async () => {
    const context = setup();
    await context.controller.start();

    context.emit({
      type: "done",
      data: {
        summary: "Running shoes within your budget are now shown.",
        language: "en",
      },
    });

    expect(context.root.querySelector('[role="status"]')?.textContent).toBe(
      "Task complete",
    );
    expect(context.root.querySelector("#conversation")?.textContent).toContain(
      "Running shoes within your budget are now shown.",
    );
  });
});
