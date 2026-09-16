import {
  parseAction,
  type Action,
  type ActionResult,
  type Snapshot,
} from "../../bridge/src/types.js";

export const AGENT_EVENT_TYPES = [
  "task_started",
  "narration",
  "action",
  "done",
  "cancelled",
  "error",
] as const;

export type AgentEvent =
  | { type: "task_started"; data: { task_id: string } }
  | { type: "narration"; data: { text: string } }
  | { type: "action"; data: { action: Action } }
  | { type: "done"; data: { summary: string; language: "ar" | "en" } }
  | { type: "cancelled"; data: Record<string, never> }
  | { type: "error"; data: { message: string } };

function eventData(payload: unknown): Record<string, unknown> {
  if (typeof payload !== "object" || payload === null || Array.isArray(payload))
    throw new TypeError("Agent event data must be an object");
  return payload as Record<string, unknown>;
}

function eventString(data: Record<string, unknown>, key: string): string {
  const value = data[key];
  if (typeof value !== "string")
    throw new TypeError(`Agent event data.${key} must be a string`);
  return value;
}

export function parseAgentEvent(type: string, payload: unknown): AgentEvent {
  if (!(AGENT_EVENT_TYPES as readonly string[]).includes(type))
    throw new TypeError(
      `Agent event type ${JSON.stringify(type)} is not supported`,
    );
  const data = eventData(payload);
  switch (type) {
    case "task_started":
      return { type, data: { task_id: eventString(data, "task_id") } };
    case "narration":
      return { type, data: { text: eventString(data, "text") } };
    case "action":
      return { type, data: { action: parseAction(data.action) } };
    case "done": {
      const language = eventString(data, "language");
      if (language !== "ar" && language !== "en")
        throw new TypeError("Agent event data.language must be ar or en");
      return {
        type,
        data: { summary: eventString(data, "summary"), language },
      };
    }
    case "cancelled":
      return { type, data: {} };
    case "error":
      return { type, data: { message: eventString(data, "message") } };
    default:
      throw new TypeError(
        `Agent event type ${JSON.stringify(type)} is not supported`,
      );
  }
}

export type StorefrontMessage =
  | { type: "snapshot"; snapshot: Snapshot }
  | { type: "action_result"; result: ActionResult };

export interface AgentTransport {
  createSession(): Promise<string>;
  subscribe(
    sessionId: string,
    handler: (event: AgentEvent) => void,
  ): () => void;
  submitMessage(
    sessionId: string,
    text: string,
    snapshot: Snapshot,
  ): Promise<void>;
  submitActionResult(sessionId: string, result: ActionResult): Promise<void>;
  stop(sessionId: string): Promise<void>;
}

export interface StorefrontChannel {
  sendAction(action: Action): void;
  requestSnapshot(): void;
}

export class PanelController {
  readonly #root: HTMLElement;
  readonly #agent: AgentTransport;
  readonly #storefront: StorefrontChannel;
  #sessionId: string | undefined;
  #snapshot: Snapshot | undefined;
  #unsubscribe: (() => void) | undefined;

  constructor(
    root: HTMLElement,
    agent: AgentTransport,
    storefront: StorefrontChannel,
  ) {
    this.#root = root;
    this.#agent = agent;
    this.#storefront = storefront;
    this.#render();
  }

  async start(): Promise<void> {
    this.#sessionId = await this.#agent.createSession();
    this.#unsubscribe = this.#agent.subscribe(this.#sessionId, (event) => {
      this.#receiveAgent(event);
    });
    this.#storefront.requestSnapshot();
    this.#setStatus("بانتظار اتصال المتجر…");
  }

  dispose(): void {
    this.#unsubscribe?.();
  }

  receiveStorefront(message: StorefrontMessage): void {
    if (message.type === "snapshot") {
      this.#snapshot = message.snapshot;
      this.#setInputEnabled(true);
      this.#setStatus("جاهز لاستقبال طلبك");
      return;
    }
    this.#snapshot = message.result.snapshot;
    if (this.#sessionId !== undefined) {
      void this.#agent.submitActionResult(this.#sessionId, message.result);
    }
  }

  #receiveAgent(event: AgentEvent): void {
    if (event.type === "narration") {
      this.#setStatus(event.data.text);
      this.#appendMessage("copilot", event.data.text);
    } else if (event.type === "action") {
      this.#storefront.sendAction(event.data.action);
    } else if (event.type === "done") {
      this.#setStatus(
        event.data.language === "ar" ? "اكتملت المهمة" : "Task complete",
      );
      this.#appendMessage("copilot", event.data.summary);
    } else if (event.type === "cancelled") {
      this.#setStatus("تم إيقاف المهمة");
    } else if (event.type === "error") {
      this.#setStatus(event.data.message);
    }
  }

  #render(): void {
    this.#root.innerHTML = `
      <section class="copilot-panel" aria-labelledby="copilot-title" dir="rtl">
        <header class="panel-header">
          <div>
            <p class="store-mark">دليلك في المتجر</p>
            <h1 id="copilot-title">مساعد التسوّق</h1>
          </div>
          <button id="stop-task" class="stop-button" type="button">إيقاف</button>
        </header>
        <div id="task-status" class="status-ribbon" role="status" aria-live="polite">جاري الاتصال…</div>
        <ol id="conversation" class="conversation" aria-label="المحادثة"></ol>
        <form class="message-form">
          <label for="shopper-message">ماذا تبحث عنه؟</label>
          <div class="input-row">
            <input id="shopper-message" name="message" autocomplete="off" required disabled />
            <button type="submit">إرسال</button>
          </div>
        </form>
      </section>`;

    this.#root
      .querySelector<HTMLFormElement>("form")
      ?.addEventListener("submit", (event) => {
        event.preventDefault();
        const input =
          this.#root.querySelector<HTMLInputElement>("#shopper-message");
        const text = input?.value.trim() ?? "";
        if (
          text === "" ||
          this.#sessionId === undefined ||
          this.#snapshot === undefined
        )
          return;
        this.#appendMessage("shopper", text);
        this.#setStatus("أفهم طلبك الآن…");
        void this.#agent.submitMessage(this.#sessionId, text, this.#snapshot);
      });

    this.#root
      .querySelector<HTMLButtonElement>("#stop-task")
      ?.addEventListener("click", () => {
        if (this.#sessionId === undefined) return;
        void this.#agent.stop(this.#sessionId);
      });
  }

  #setStatus(message: string): void {
    const status = this.#root.querySelector<HTMLElement>("#task-status");
    if (status !== null) status.textContent = message;
  }

  #setInputEnabled(enabled: boolean): void {
    const input =
      this.#root.querySelector<HTMLInputElement>("#shopper-message");
    if (input !== null) input.disabled = !enabled;
  }

  #appendMessage(role: "shopper" | "copilot", message: string): void {
    const conversation =
      this.#root.querySelector<HTMLOListElement>("#conversation");
    if (conversation === null) return;
    const item = this.#root.ownerDocument.createElement("li");
    item.className = `message message-${role}`;
    item.textContent = message;
    conversation.append(item);
  }
}
