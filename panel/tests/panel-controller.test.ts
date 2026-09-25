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
  answerStatus?: "resumed" | "awaiting_login";
  answerGate?: Promise<void>;
  reconcileGate?: Promise<void>;
  speechRecognition?: new () => {
    lang: string;
    onresult:
      | ((event: {
          results: ArrayLike<ArrayLike<{ transcript: string }>>;
        }) => void)
      | null;
    onerror: (() => void) | null;
    onend: (() => void) | null;
    start(): void;
    abort(): void;
  };
}) {
  const dom = new JSDOM('<!doctype html><div id="app"></div>');
  if (options?.speechRecognition)
    Object.defineProperty(dom.window, "SpeechRecognition", {
      value: options.speechRecognition,
    });
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
  const retries: unknown[] = [];
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
      await options?.reconcileGate;
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
      await options?.answerGate;
      return options?.answerStatus ?? "resumed";
    },
    stop: async (sessionId) => {
      stopped.push(sessionId);
    },
    retry: async (sessionId, taskId, currentSnapshot) => {
      retries.push({ sessionId, taskId, snapshot: currentSnapshot });
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
    retries,
    snapshotRequests: () => snapshotRequests,
    emit: (event: AgentEvent) => eventHandler?.(event),
  };
}

describe("PanelController", () => {
  it("shows labelled grounded suggestions and restores them without a browser Action", async () => {
    const suggestions = {
      exact_count: 0,
      suggestions: [
        {
          id: "shoe-07",
          label: "alternative" as const,
          name: "راحة يومية",
          price: "1350",
          currency: "EGP" as const,
          reason: "بديل؛ لا يمكن تأكيد مناسبة الفرح.",
          unmet: ["suitable_for: formal_events"],
        },
      ],
    };
    const context = setup();
    await context.controller.start();
    context.emit({ type: "task_started", data: { task_id: "task-1" } });
    context.emit({ type: "suggestions", data: suggestions });
    context.emit({
      type: "done",
      data: { summary: "No exact match", language: "ar" },
    });
    expect(context.actions).toHaveLength(0);
    expect(
      context.root.querySelector('[data-product-id="shoe-07"]')?.textContent,
    ).toContain("Alternative");
    expect(
      context.root.querySelector('[data-product-id="shoe-07"]')?.textContent,
    ).toContain("formal_events");
    expect(
      context.root
        .querySelector("#task-status")
        ?.getAttribute("data-task-state"),
    ).toBe("completed");

    const restored = setup({
      savedSessionId: "session-1",
      restoredState: {
        session_id: "session-1",
        lease: "owned",
        event_cursor: 3,
        conversation: [{ role: "copilot", text: "No exact match" }],
        requires_reconciliation: false,
        task: {
          task_id: "task-1",
          status: "completed",
          pending_question: null,
          suggestions,
        },
      },
    });
    await restored.controller.start();
    restored.controller.receiveStorefront({ type: "snapshot", snapshot });
    await Promise.resolve();
    await Promise.resolve();
    expect(restored.root.querySelectorAll(".suggestion-card")).toHaveLength(1);
    expect(restored.actions).toHaveLength(0);
  });
  it("keeps a failed interpretation active and offers Retry and Stop", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.emit({ type: "task_started", data: { task_id: "task-retry" } });
    context.emit({
      type: "error",
      data: { message: "Couldn't interpret the request." },
    });

    expect(
      context.root.querySelector<HTMLInputElement>("#shopper-message")
        ?.disabled,
    ).toBe(true);
    context.root.querySelector<HTMLButtonElement>("#retry-task")?.click();
    await Promise.resolve();
    expect(context.retries).toEqual([
      { sessionId: "session-1", taskId: "task-retry", snapshot },
    ]);
    expect(
      context.root.querySelector<HTMLButtonElement>("#stop-task"),
    ).not.toBeNull();
  });
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

    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    expect(input.disabled).toBe(true);

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
    expect(context.dom.window.document.activeElement).toBe(option);
    option.click();
    await Promise.resolve();

    expect(context.actions).toEqual([
      expect.objectContaining({
        type: "ask_shopper",
        task_id: "task-1",
        action_id: "question-1",
        sequence_number: 1,
      }),
    ]);
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

  it("shows a distinct exact-effect Confirmation card and sends the chosen option", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.emit({ type: "task_started", data: { task_id: "task-clear" } });
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "ask_shopper",
          kind: "confirmation",
          task_id: "task-clear",
          action_id: "confirmation-1234567890abcdef1234567890abcdef",
          sequence_number: 1,
          narration: "Confirm this action.",
          question:
            "Confirm this action: Remove every item from the current cart. Continue?",
          options: ["Confirm", "Stop"],
        },
      },
    });

    const card = context.root.querySelector<HTMLElement>(".confirmation-card");
    expect(card?.getAttribute("aria-label")).toBe("Confirm Guarded Mutation");
    expect(card?.textContent).toContain(
      "Remove every item from the current cart",
    );
    card
      ?.querySelector<HTMLButtonElement>('[data-question-option="Confirm"]')
      ?.click();
    await Promise.resolve();
    expect(context.answers).toEqual([
      expect.objectContaining({
        questionId: "confirmation-1234567890abcdef1234567890abcdef",
        text: "Confirm",
      }),
    ]);
  });

  it("keeps the sign-in handoff visible without repeating Continue until the page changes", async () => {
    const context = setup({ answerStatus: "awaiting_login" });
    await context.controller.start();
    const login = {
      ...snapshot,
      url: "http://localhost:4000/login?next=%2Faccount%2Forders",
    };
    context.controller.receiveStorefront({ type: "snapshot", snapshot: login });
    context.emit({ type: "task_started", data: { task_id: "task-orders" } });
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "ask_shopper",
          task_id: "task-orders",
          action_id: "question-login",
          sequence_number: 2,
          narration: "Sign in yourself first.",
          question: "After signing in, should I continue?",
          options: ["Continue", "Stop"],
        },
      },
    });

    context.root
      .querySelector<HTMLButtonElement>('[data-question-option="Continue"]')!
      .click();
    await Promise.resolve();
    await Promise.resolve();

    const continueButton = context.root.querySelector<HTMLButtonElement>(
      '[data-question-option="Continue"]',
    )!;
    expect(continueButton.disabled).toBe(true);
    expect(
      context.root.querySelector("#pending-question")?.textContent,
    ).toContain("سجّل الدخول");
    continueButton.click();
    expect(context.answers).toHaveLength(1);
    expect(
      context.root.querySelector<HTMLButtonElement>(
        '[data-question-option="Stop"]',
      )?.disabled,
    ).toBe(false);

    context.controller.receiveStorefront({
      type: "snapshot",
      snapshot: { ...snapshot, url: "http://localhost:4000/account/orders" },
    });
    expect(continueButton.disabled).toBe(false);
  });

  it("does not re-lock Continue if sign-in completes before the waiting response arrives", async () => {
    let releaseAnswer!: () => void;
    const answerGate = new Promise<void>((resolve) => {
      releaseAnswer = resolve;
    });
    const context = setup({ answerStatus: "awaiting_login", answerGate });
    await context.controller.start();
    context.controller.receiveStorefront({
      type: "snapshot",
      snapshot: {
        ...snapshot,
        url: "http://localhost:4000/login?next=%2Faccount%2Forders",
      },
    });
    context.emit({ type: "task_started", data: { task_id: "task-orders" } });
    context.emit({
      type: "action",
      data: {
        action: {
          v: 1,
          type: "ask_shopper",
          task_id: "task-orders",
          action_id: "question-login",
          sequence_number: 2,
          narration: "Sign in yourself first.",
          question: "After signing in, should I continue?",
          options: ["Continue", "Stop"],
        },
      },
    });
    const continueButton = context.root.querySelector<HTMLButtonElement>(
      '[data-question-option="Continue"]',
    )!;
    continueButton.click();
    context.controller.receiveStorefront({
      type: "snapshot",
      snapshot: { ...snapshot, url: "http://localhost:4000/account/orders" },
    });
    releaseAnswer();
    await Promise.resolve();
    await Promise.resolve();
    expect(continueButton.disabled).toBe(false);
  });

  it("registers a clarification in Bridge without treating its receipt as a Shopper answer", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.emit({ type: "task_started", data: { task_id: "task-cart" } });
    const question = {
      v: 1 as const,
      type: "ask_shopper" as const,
      task_id: "task-cart",
      action_id: "question-cart",
      sequence_number: 1,
      narration: "Which page?",
      question: "Which page should I open?",
      options: ["افتح السلة"],
    };
    context.emit({ type: "action", data: { action: question } });
    expect(context.actions).toEqual([question]);

    context.controller.receiveStorefront({
      type: "action_result",
      result: {
        v: 1,
        task_id: "task-cart",
        action_id: "question-cart",
        sequence_number: 1,
        status: "ok",
        snapshot,
      },
    });
    await Promise.resolve();
    expect(context.results).toHaveLength(0);

    const navigate = {
      v: 1 as const,
      type: "navigate" as const,
      task_id: "task-cart",
      action_id: "open-cart",
      sequence_number: 2,
      narration: "Opening cart",
      url: "/cart",
    };
    context.emit({ type: "action", data: { action: navigate } });
    expect(context.actions).toEqual([question, navigate]);
    context.controller.receiveStorefront({
      type: "action_result",
      result: {
        v: 1,
        task_id: "task-cart",
        action_id: "open-cart",
        sequence_number: 2,
        status: "navigated",
        snapshot,
      },
    });
    await Promise.resolve();
    expect(context.results).toEqual([
      expect.objectContaining({ action_id: "open-cart", status: "navigated" }),
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

  it("reconciles the latest Storefront Snapshot once when reload delivers overlapping snapshots", async () => {
    let release!: () => void;
    const reconcileGate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const context = setup({
      savedSessionId: "session-restored",
      reconcileGate,
    });
    await context.controller.start();
    const latest = { ...snapshot, url: "http://localhost:4000/cart" };
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.controller.receiveStorefront({
      type: "snapshot",
      snapshot: latest,
    });

    expect(context.reconciliations).toEqual([
      { sessionId: "session-restored", snapshot },
    ]);
    release();
    await Promise.resolve();
    await Promise.resolve();
    expect(context.reconciliations).toEqual([
      { sessionId: "session-restored", snapshot },
      { sessionId: "session-restored", snapshot: latest },
    ]);
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

  it("restores Retry for a paused model call after refresh", async () => {
    const restoredState: SessionView = {
      session_id: "session-paused",
      lease: "owned",
      event_cursor: 3,
      conversation: [{ role: "shopper", text: "عاوز حذاء" }],
      requires_reconciliation: false,
      task: {
        task_id: "task-paused",
        status: "paused",
        pending_question: null,
        pause_message: "The model service timed out. Retry or stop the task.",
      },
    };
    const context = setup({ savedSessionId: "session-paused", restoredState });
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    await Promise.resolve();
    await Promise.resolve();

    const retry = context.root.querySelector<HTMLButtonElement>("#retry-task");
    expect(retry).not.toBeNull();
    expect(context.root.querySelector("#task-status")?.textContent).toContain(
      "timed out",
    );
    const changed = {
      ...snapshot,
      url: "http://localhost:4000/c/shoes?type=running",
    };
    context.controller.receiveStorefront({
      type: "snapshot",
      snapshot: changed,
    });
    retry?.click();
    await Promise.resolve();
    expect(context.retries).toEqual([
      { sessionId: "session-paused", taskId: "task-paused", snapshot: changed },
    ]);
  });

  it.each([404, 410])(
    "starts a fresh session when saved session restore returns %i",
    async (status) => {
      const context = setup({
        savedSessionId: "session-expired",
        restoreError: new Error(`Session restore failed with ${status}`),
      });

      await context.controller.start();

      expect(context.snapshotRequests()).toBe(1);
      expect(context.root.querySelector("#task-status")?.textContent).toBe(
        "بانتظار اتصال المتجر…",
      );
      expect(
        context.root.querySelector("#conversation")?.textContent,
      ).toContain("بدأت جلسة جديدة");
      context.controller.receiveStorefront({ type: "snapshot", snapshot });
      expect(
        context.root.querySelector<HTMLInputElement>("#shopper-message")
          ?.disabled,
      ).toBe(false);
    },
  );

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

  it("keeps Stop available and disables speech when the browser lacks recognition", async () => {
    const context = setup();
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    expect(
      context.root.querySelector<HTMLButtonElement>("#stop-task")?.disabled,
    ).toBe(false);
    expect(
      context.root.querySelector<HTMLButtonElement>("#speech-input")?.disabled,
    ).toBe(true);
    context.root.querySelector<HTMLButtonElement>("#stop-task")?.click();
    expect(context.stopped).toEqual(["session-1"]);
  });

  it("transcribes selected Arabic or English speech into the editable input without submitting", async () => {
    const recognitions: Array<{
      lang: string;
      onresult:
        | ((event: {
            results: ArrayLike<ArrayLike<{ transcript: string }>>;
          }) => void)
        | null;
      onend: (() => void) | null;
      aborted: boolean;
    }> = [];
    class FakeSpeechRecognition {
      lang = "";
      onresult:
        | ((event: {
            results: ArrayLike<ArrayLike<{ transcript: string }>>;
          }) => void)
        | null = null;
      onerror: (() => void) | null = null;
      onend: (() => void) | null = null;
      aborted = false;
      constructor() {
        recognitions.push(this);
      }
      start() {
        /* browser mock */
      }
      abort() {
        this.aborted = true;
        this.onend?.();
      }
    }
    const context = setup({ speechRecognition: FakeSpeechRecognition });
    await context.controller.start();
    context.controller.receiveStorefront({ type: "snapshot", snapshot });
    context.root.querySelector<HTMLButtonElement>("#speech-input")?.click();
    expect(recognitions[0]?.lang).toBe("ar-EG");
    recognitions[0]?.onresult?.({
      results: [[{ transcript: "عايز كوتشي جري" }]],
    });
    expect(
      context.root.querySelector<HTMLInputElement>("#shopper-message")?.value,
    ).toBe("عايز كوتشي جري");
    expect(context.submitted).toEqual([]);
    context.root.querySelector<HTMLSelectElement>("#speech-language")!.value =
      "en-US";
    recognitions[0]?.onend?.();
    context.root.querySelector<HTMLButtonElement>("#speech-input")?.click();
    expect(recognitions[1]?.lang).toBe("en-US");
    context.root.querySelector<HTMLButtonElement>("#stop-task")?.click();
    expect(recognitions[1]?.aborted).toBe(true);
  });
});
