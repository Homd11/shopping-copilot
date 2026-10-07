import type { Action, ActionResult, Snapshot } from "../../bridge/src/types.js";

import {
  PanelController,
  type AgentEvent,
  type AgentTransport,
  type StorefrontChannel,
  type StorefrontMessage,
  type SessionPersistence,
  type SessionView,
} from "./panel.js";
import "./styles.css";
import { linkShopper } from "./shopper-link.js";
import { subscribeAgentStream } from "./event-stream.js";

const AGENT_ORIGIN = "http://localhost:8000";
const STOREFRONT_ORIGIN = "http://localhost:4000";

let browserCsrf = "";
let shopperContext = "";
async function agentFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers: { ...options.headers, "x-csrf-token": browserCsrf },
  });
  if (response.status === 401 || response.status === 403)
    controller.invalidateShopper();
  return response;
}

class HttpAgentTransport implements AgentTransport {
  readonly #tabId: string;

  constructor(tabId: string) {
    this.#tabId = tabId;
  }

  async createSession(tabId = this.#tabId): Promise<string> {
    const response = await agentFetch(`${AGENT_ORIGIN}/sessions`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-tab-id": this.#tabId,
      },
      body: JSON.stringify({ tab_id: tabId }),
    });
    if (!response.ok) throw new Error("Session creation failed");
    const payload = (await response.json()) as { session_id: string };
    return payload.session_id;
  }

  subscribe(
    sessionId: string,
    handler: (event: AgentEvent) => void,
    after = 0,
    onCursor?: (cursor: number) => void,
  ): () => void {
    return subscribeAgentStream(
      `${AGENT_ORIGIN}/sessions/${sessionId}/events?after=${after}&tab_id=${encodeURIComponent(this.#tabId)}`,
      handler,
      after,
      onCursor,
      undefined,
      () => controller.invalidateShopper(),
    );
  }

  async restoreSession(sessionId: string, tabId: string): Promise<SessionView> {
    const response = await agentFetch(
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

  async speechAvailable(): Promise<boolean> {
    const response = await agentFetch(`${AGENT_ORIGIN}/speech/availability`);
    if (!response.ok) return false;
    const result = (await response.json()) as { available: boolean };
    return result.available === true;
  }

  async transcribeSpeech(audio: Blob, language: "ar" | "en"): Promise<string> {
    const response = await agentFetch(
      `${AGENT_ORIGIN}/speech/transcribe?language=${language}`,
      {
        method: "POST",
        headers: { "content-type": "audio/webm" },
        body: audio,
      },
    );
    if (!response.ok)
      throw new Error(`Speech transcription failed with ${response.status}`);
    const result = (await response.json()) as { text: string };
    return result.text;
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
  ): Promise<"resumed" | "awaiting_login"> {
    const response = await agentFetch(
      `${AGENT_ORIGIN}/sessions/${sessionId}/tasks/${taskId}/answers`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-tab-id": this.#tabId,
        },
        body: JSON.stringify({ question_id: questionId, text, snapshot }),
      },
    );
    if (!response.ok)
      throw new Error(`Agent request failed with ${response.status}`);
    const result = (await response.json()) as {
      status: "resumed" | "awaiting_login";
    };
    return result.status;
  }

  async stop(sessionId: string): Promise<void> {
    await this.#post(`/sessions/${sessionId}/stop`, {});
  }

  async retry(
    sessionId: string,
    taskId: string,
    snapshot: Snapshot,
  ): Promise<void> {
    await this.#post(`/sessions/${sessionId}/tasks/${taskId}/retry`, {
      snapshot,
    });
  }

  async #post(path: string, body: object): Promise<void> {
    const response = await agentFetch(`${AGENT_ORIGIN}${path}`, {
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
    const response = await agentFetch(`${AGENT_ORIGIN}${path}`, {
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
      { type: "action", action, shopper_context: shopperContext },
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
const spaVariant = new URL(window.location.href).searchParams.get("spa");
const storefrontUrl =
  spaVariant === "url" || spaVariant === "component" || spaVariant === "off"
    ? `${STOREFRONT_ORIGIN}/?spa=${spaVariant}`
    : `${STOREFRONT_ORIGIN}/`;

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
  if (event.data?.type === "shopper_reset") {
    controller.invalidateShopper();
    return;
  }
  if (message.type === "snapshot" || message.type === "action_result") {
    if (!shopperContext) return;
    if (event.data.shopper_context !== shopperContext) {
      controller.invalidateShopper();
      return;
    }
    controller.receiveStorefront(message);
  }
});
async function startLinked() {
  try {
    const begin = async () => {
      // Serialize the first Storefront navigation too: cookies are shared across tabs.
      frame!.src = storefrontUrl;
      const linked = await linkShopper(frame!, AGENT_ORIGIN, STOREFRONT_ORIGIN);
      browserCsrf = linked.csrf;
      shopperContext = linked.context;
      await controller.start();
    };
    if (navigator.locks)
      await navigator.locks.request("copilot-shopper-link", begin);
    else throw new Error("A secure browser with Web Locks is required");
  } catch {
    const status = document.createElement("p");
    status.setAttribute("role", "alert");
    status.textContent =
      "تعذر ربط جلسة التسوق. أعد تحميل الصفحة للمحاولة. / Shopping session unavailable. Reload to retry.";
    root!.prepend(status);
  }
}
void startLinked();
