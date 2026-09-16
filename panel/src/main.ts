import type { Action, ActionResult, Snapshot } from "../../bridge/src/types.js";

import {
  AGENT_EVENT_TYPES,
  PanelController,
  parseAgentEvent,
  type AgentEvent,
  type AgentTransport,
  type StorefrontChannel,
  type StorefrontMessage,
} from "./panel.js";
import "./styles.css";

const AGENT_ORIGIN = "http://localhost:8000";
const STOREFRONT_ORIGIN = "http://localhost:4000";

class HttpAgentTransport implements AgentTransport {
  async createSession(): Promise<string> {
    const response = await fetch(`${AGENT_ORIGIN}/sessions`, {
      method: "POST",
    });
    const payload = (await response.json()) as { session_id: string };
    return payload.session_id;
  }

  subscribe(
    sessionId: string,
    handler: (event: AgentEvent) => void,
  ): () => void {
    const source = new EventSource(
      `${AGENT_ORIGIN}/sessions/${sessionId}/events`,
    );
    for (const type of AGENT_EVENT_TYPES)
      source.addEventListener(type, (event) => {
        const message = event as MessageEvent<string>;
        handler(parseAgentEvent(type, JSON.parse(message.data)));
      });
    return () => source.close();
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

  async stop(sessionId: string): Promise<void> {
    await this.#post(`/sessions/${sessionId}/stop`, {});
  }

  async #post(path: string, body: object): Promise<void> {
    const response = await fetch(`${AGENT_ORIGIN}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok)
      throw new Error(`Agent request failed with ${response.status}`);
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
}

const root = document.querySelector<HTMLElement>("#app");
const frame = document.querySelector<HTMLIFrameElement>("#storefront-frame");
if (root === null || frame === null)
  throw new Error("Panel shell is incomplete");

const controller = new PanelController(
  root,
  new HttpAgentTransport(),
  new WindowStorefrontChannel(frame),
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
