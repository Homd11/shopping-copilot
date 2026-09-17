import type { Action, ActionResult, Snapshot } from "../../bridge/src/types.js";

import {
  AGENT_EVENT_TYPES,
  PanelController,
  parseAgentEvent,
  type AgentEvent,
  type AgentTransport,
  type StorefrontChannel,
  type StorefrontMessage,
  type SessionPersistence,
  type SessionView,
} from "./panel.js";
import "./styles.css";

const AGENT_ORIGIN = "http://localhost:8000";
const STOREFRONT_ORIGIN = "http://localhost:4000";

class HttpAgentTransport implements AgentTransport {
  readonly #tabId: string;

  constructor(tabId: string) {
    this.#tabId = tabId;
  }

  async createSession(tabId = this.#tabId): Promise<string> {
    const response = await fetch(`${AGENT_ORIGIN}/sessions`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-tab-id": this.#tabId,
      },
      body: JSON.stringify({ tab_id: tabId }),
    });
    const payload = (await response.json()) as { session_id: string };
    return payload.session_id;
  }

  subscribe(
    sessionId: string,
    handler: (event: AgentEvent) => void,
    after = 0,
    onCursor?: (cursor: number) => void,
  ): () => void {
    const source = new EventSource(
      `${AGENT_ORIGIN}/sessions/${sessionId}/events?after=${after}&tab_id=${encodeURIComponent(this.#tabId)}`,
    );
    for (const type of AGENT_EVENT_TYPES)
      source.addEventListener(type, (event) => {
        const message = event as MessageEvent<string>;
        const cursor = Number(message.lastEventId);
        if (Number.isSafeInteger(cursor)) onCursor?.(cursor);
        handler(parseAgentEvent(type, JSON.parse(message.data)));
      });
    return () => source.close();
  }

  async restoreSession(sessionId: string, tabId: string): Promise<SessionView> {
    const response = await fetch(
      `${AGENT_ORIGIN}/sessions/${sessionId}/state?tab_id=${encodeURIComponent(tabId)}`,
    );
    if (!response.ok)
      throw new Error(`Session restore failed with ${response.status}`);
    return (await response.json()) as SessionView;
  }

  async reconcile(
    sessionId: string,
    tabId: string,
    snapshot: Snapshot,
  ): Promise<SessionView> {
    return this.#postForView(
      `/sessions/${sessionId}/reconcile`,
      { snapshot },
      tabId,
    );
  }

  async takeover(sessionId: string, tabId: string): Promise<SessionView> {
    return this.#postForView(
      `/sessions/${sessionId}/takeover`,
      { tab_id: tabId },
      tabId,
    );
  }

  async submitMessage(
    sessionId: string,
    text: string,
    snapshot: Snapshot,
  ): Promise<void> {
    await this.#post(`/sessions/${sessionId}/messages`, { text, snapshot });
  }

  async submitActionResult(
    sessionId: string,
    result: ActionResult,
  ): Promise<void> {
    await this.#post(`/sessions/${sessionId}/action-results`, result);
  }

  async submitAnswer(
    sessionId: string,
    taskId: string,
    questionId: string,
    text: string,
    snapshot: Snapshot,
  ): Promise<void> {
    await this.#post(`/sessions/${sessionId}/tasks/${taskId}/answers`, {
      question_id: questionId,
      text,
      snapshot,
    });
  }

  async stop(sessionId: string): Promise<void> {
    await this.#post(`/sessions/${sessionId}/stop`, {});
  }

  async #post(path: string, body: object): Promise<void> {
    const response = await fetch(`${AGENT_ORIGIN}${path}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-tab-id": this.#tabId,
      },
      body: JSON.stringify(body),
    });
    if (!response.ok)
      throw new Error(`Agent request failed with ${response.status}`);
  }

  async #postForView(
    path: string,
    body: object,
    tabId: string,
  ): Promise<SessionView> {
    const response = await fetch(`${AGENT_ORIGIN}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-tab-id": tabId },
      body: JSON.stringify(body),
    });
    if (!response.ok)
      throw new Error(`Agent request failed with ${response.status}`);
    return (await response.json()) as SessionView;
  }
}

class WindowStorefrontChannel implements StorefrontChannel {
  readonly #frame: HTMLIFrameElement;

  constructor(frame: HTMLIFrameElement) {
    this.#frame = frame;
    this.#frame.addEventListener("load", () => this.requestSnapshot());
  }

  sendAction(action: Action): void {
    this.#frame.contentWindow?.postMessage(
      { type: "action", action },
      STOREFRONT_ORIGIN,
    );
  }

  requestSnapshot(): void {
    this.#frame.contentWindow?.postMessage(
      { type: "request_snapshot" },
      STOREFRONT_ORIGIN,
    );
  }

  cancelTask(taskId: string): void {
    this.#frame.contentWindow?.postMessage(
      { type: "cancel_task", task_id: taskId },
      STOREFRONT_ORIGIN,
    );
  }
}

const root = document.querySelector<HTMLElement>("#app");
const frame = document.querySelector<HTMLIFrameElement>("#storefront-frame");
if (root === null || frame === null)
  throw new Error("Panel shell is incomplete");

const SESSION_KEY = "shopping-copilot.session-id";
const CURSOR_KEY = "shopping-copilot.event-cursor";
const TAB_KEY = "shopping-copilot.tab-id";
let tabId = window.sessionStorage.getItem(TAB_KEY);
if (tabId === null) {
  tabId = crypto.randomUUID();
  window.sessionStorage.setItem(TAB_KEY, tabId);
}
const persistence: SessionPersistence = {
  loadSessionId: () => window.localStorage.getItem(SESSION_KEY) ?? undefined,
  saveSessionId: (sessionId) =>
    window.localStorage.setItem(SESSION_KEY, sessionId),
  clearSession: () => {
    window.localStorage.removeItem(SESSION_KEY);
    window.localStorage.removeItem(CURSOR_KEY);
  },
  loadEventCursor: () => Number(window.localStorage.getItem(CURSOR_KEY) ?? "0"),
  saveEventCursor: (cursor) =>
    window.localStorage.setItem(CURSOR_KEY, String(cursor)),
};

const controller = new PanelController(
  root,
  new HttpAgentTransport(tabId),
  new WindowStorefrontChannel(frame),
  { persistence, tabId },
);
window.addEventListener("message", (event) => {
  if (
    event.origin !== STOREFRONT_ORIGIN ||
    event.source !== frame.contentWindow
  )
    return;
  const message = event.data as StorefrontMessage;
  if (message.type === "snapshot" || message.type === "action_result") {
    controller.receiveStorefront(message);
  }
});
void controller.start();
