import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import {
  PanelController,
  type AgentEvent,
  type AgentTransport,
  type StorefrontChannel,
  type SessionPersistence,
  type SessionView,
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

function setup(options?: {
  savedSessionId?: string;
  restoredState?: SessionView;
  restoreError?: Error;
}) {
  const dom = new JSDOM('<!doctype html><div id="app"></div>');
  const submitted: Array<{
    sessionId: string;
    text: string;
    snapshot: unknown;
  }> = [];
  const results: unknown[] = [];
  const stopped: string[] = [];
  const answers: unknown[] = [];
  const reconciliations: unknown[] = [];
  const takeovers: unknown[] = [];
  let eventHandler: ((event: AgentEvent) => void) | undefined;
  const agent: AgentTransport = {
    createSession: async () => "session-1",
    restoreSession: async () => {
      if (options?.restoreError !== undefined) throw options.restoreError;
      return (
        options?.restoredState ?? {
          session_id: options?.savedSessionId ?? "session-1",
          lease: "owned",
          event_cursor: 0,
          conversation: [],
          requires_reconciliation: false,
          task: null,
        }
      );
    },
    reconcile: async (sessionId, _tabId, currentSnapshot) => {
      reconciliations.push({ sessionId, snapshot: currentSnapshot });
      return {
        session_id: sessionId,
        lease: "owned",
        event_cursor: 4,
        conversation: options?.restoredState?.conversation ?? [],
        requires_reconciliation: false,
        task: options?.restoredState?.task ?? null,
      };
    },
    takeover: async (sessionId, tabId) => {
      takeovers.push({ sessionId, tabId });
      return { ...options!.restoredState!, lease: "owned" };
    },
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
    submitAnswer: async (
      sessionId,
      taskId,
      questionId,
      text,
      currentSnapshot,
    ) => {
      answers.push({
        sessionId,
        taskId,
        questionId,
        text,
        snapshot: currentSnapshot,
      });
    },
    stop: async (sessionId) => {
      stopped.push(sessionId);
    },
  };
  const actions: unknown[] = [];
  const cancelledTasks: string[] = [];
  let snapshotRequests = 0;
  const storefront: StorefrontChannel = {
    sendAction: (action) => actions.push(action),
    cancelTask: (taskId) => cancelledTasks.push(taskId),
    requestSnapshot: () => snapshotRequests++,
  };
  const root = dom.window.document.querySelector<HTMLElement>("#app")!;
  let savedSessionId = options?.savedSessionId;
  let savedCursor = 0;
  const persistence: SessionPersistence = {
    loadSessionId: () => savedSessionId,
    saveSessionId: (sessionId) => {
      savedSessionId = sessionId;
    },
    clearSession: () => {
      savedSessionId = undefined;
      savedCursor = 0;
    },
    loadEventCursor: () => savedCursor,
    saveEventCursor: (cursor) => {
      savedCursor = cursor;
    },
  };
  const controller = new PanelController(root, agent, storefront, {
    persistence,
    tabId: "tab-1",
  });
  return {
    dom,
    root,
    controller,
    submitted,
    results,
    stopped,
    answers,
    actions,
    cancelledTasks,
    reconciliations,
    takeovers,
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

  it("renders a Shopper question and resumes it from a matching option", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.emit({ type: "task_started", data: { task_id: "task-1" } });
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "ask_shopper",
          task_id: "task-1",
          action_id: "question-1",
          sequence_number: 1,
          narration: "I need an EGP amount.",
          question: "What is your budget in EGP?",
          options: ["2000 EGP", "No budget"],
        },
      },
    });

    const option = context.root.querySelector<HTMLButtonElement>(
      '[data-question-option="2000 EGP"]',
    )!;
    expect(option).not.toBeNull();
    option.click();
    await Promise.resolve();

    expect(context.actions).toEqual([]);
    expect(context.answers).toEqual([
      {
        sessionId: "session-1",
        taskId: "task-1",
        questionId: "question-1",
        text: "2000 EGP",
        snapshot,
      },
    ]);
  });

  it("accepts a typed answer when a Shopper question has no options", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.emit({ type: "task_started", data: { task_id: "task-typed" } });
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "ask_shopper",
          task_id: "task-typed",
          action_id: "question-typed",
          sequence_number: 1,
          narration: "I need an EGP amount.",
          question: "What is your budget in EGP?",
          options: [],
        },
      },
    });
    const input = context.root.querySelector<HTMLInputElement>(
      "#question-answer-input",
    )!;
    input.value = "2000 EGP";
    context.root
      .querySelector<HTMLFormElement>("#question-answer-form")!
      .dispatchEvent(
        new context.dom.window.Event("submit", {
          bubbles: true,
          cancelable: true,
        }),
      );
    await Promise.resolve();

    expect(context.answers[0]).toMatchObject({
      taskId: "task-typed",
      questionId: "question-typed",
      text: "2000 EGP",
    });
  });

  it("retires the active task immediately when Stop is pressed", async () => {
    const context = setup();
    await context.controller.start();
    context.emit({ type: "task_started", data: { task_id: "task-stop" } });

    context.root.querySelector<HTMLButtonElement>("#stop-task")!.click();
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "navigate",
          task_id: "task-stop",
          action_id: "late-action",
          sequence_number: 1,
          narration: "Too late.",
          url: "/c/shoes",
        },
      },
    });
    await Promise.resolve();

    expect(context.cancelledTasks).toEqual(["task-stop"]);
    expect(context.actions).toEqual([]);
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

  it("restores conversation only after reconciling a fresh Snapshot", async () => {
    const restoredState: SessionView = {
      session_id: "session-restored",
      lease: "owned",
      event_cursor: 3,
      conversation: [
        { role: "shopper", text: "Show me running shoes" },
        { role: "copilot", text: "I was applying your filters." },
      ],
      requires_reconciliation: true,
      task: {
        task_id: "task-restored",
        status: "awaiting_action_result",
        pending_question: null,
      },
    };
    const context = setup({
      savedSessionId: "session-restored",
      restoredState,
    });

    await context.controller.start();
    expect(context.root.querySelector("#task-status")?.textContent).toBe(
      "Reconnecting…",
    );
    expect(
      context.root.querySelector<HTMLInputElement>("#shopper-message")
        ?.disabled,
    ).toBe(true);

    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    await Promise.resolve();
    await Promise.resolve();

    expect(context.reconciliations).toEqual([
      { sessionId: "session-restored", snapshot },
    ]);
    expect(context.root.querySelector("#conversation")?.textContent).toContain(
      "Show me running shoes",
    );
  });

  it("requires explicit takeover before another tab can reconnect", async () => {
    const restoredState: SessionView = {
      session_id: "session-owned-elsewhere",
      lease: "takeover_required",
      event_cursor: 2,
      conversation: [],
      requires_reconciliation: true,
      task: {
        task_id: "task-1",
        status: "awaiting_action_result",
        pending_question: null,
      },
    };
    const context = setup({
      savedSessionId: "session-owned-elsewhere",
      restoredState,
    });

    await context.controller.start();
    const takeover =
      context.root.querySelector<HTMLButtonElement>("#takeover-session");
    expect(takeover).not.toBeNull();
    takeover!.click();
    await Promise.resolve();

    expect(context.takeovers).toEqual([
      { sessionId: "session-owned-elsewhere", tabId: "tab-1" },
    ]);
  });

  it("starts a fresh session when the saved session has expired", async () => {
    const context = setup({
      savedSessionId: "session-expired",
      restoreError: new Error("Session restore failed with 410"),
    });

    await context.controller.start();

    expect(context.snapshotRequests()).toBe(1);
    expect(context.root.querySelector("#task-status")?.textContent).toBe(
      "بانتظار اتصال المتجر…",
    );
  });

  it.each(["completed", "cancelled"])(
    "restores a %s task without locking Shopper input",
    async (status) => {
      const restoredState: SessionView = {
        session_id: "session-finished",
        lease: "owned",
        event_cursor: 6,
        conversation: [{ role: "copilot", text: "Finished earlier." }],
        requires_reconciliation: false,
        task: {
          task_id: "task-finished",
          status,
          pending_question: null,
        },
      };
      const context = setup({
        savedSessionId: "session-finished",
        restoredState,
      });

      await context.controller.start();
      context.controller.receiveStorefront({ type: "snapshot", snapshot });
      await Promise.resolve();
      await Promise.resolve();

      expect(
        context.root.querySelector<HTMLInputElement>("#shopper-message")
          ?.disabled,
      ).toBe(false);
      expect(context.root.querySelector("#pending-question")?.textContent).toBe(
        "",
      );
    },
  );
});
