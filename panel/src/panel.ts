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
  "suggestions",
  "done",
  "cancelled",
  "error",
] as const;

export type AgentEvent =
  | { type: "task_started"; data: { task_id: string } }
  | { type: "narration"; data: { text: string } }
  | { type: "action"; data: { action: Action } }
  | { type: "suggestions"; data: SuggestionResult }
  | { type: "done"; data: { summary: string; language: "ar" | "en" } }
  | { type: "cancelled"; data: Record<string, never> }
  | { type: "error"; data: { message: string } };

export interface Suggestion {
  id: string;
  label: "exact_match" | "alternative" | "styling_suggestion";
  name: string;
  price: string;
  currency: "EGP";
  reason: string;
  unmet: string[];
}

export interface SuggestionResult {
  exact_count: number;
  suggestions: Suggestion[];
}

function parseSuggestionResult(
  data: Record<string, unknown>,
): SuggestionResult {
  if (
    !Number.isSafeInteger(data.exact_count) ||
    (data.exact_count as number) < 0
  )
    throw new TypeError("Invalid exact match count");
  if (!Array.isArray(data.suggestions) || data.suggestions.length > 3)
    throw new TypeError("Invalid suggestion list");
  const suggestions = data.suggestions.map((value: unknown) => {
    const item = eventData(value);
    const label = eventString(item, "label");
    if (!["exact_match", "alternative", "styling_suggestion"].includes(label))
      throw new TypeError("Invalid suggestion label");
    if (eventString(item, "currency") !== "EGP")
      throw new TypeError("Invalid suggestion currency");
    if (
      !Array.isArray(item.unmet) ||
      !item.unmet.every((part) => typeof part === "string")
    )
      throw new TypeError("Invalid unmet requirements");
    return {
      id: eventString(item, "id"),
      label: label as Suggestion["label"],
      name: eventString(item, "name"),
      price: eventString(item, "price"),
      currency: "EGP" as const,
      reason: eventString(item, "reason"),
      unmet: item.unmet as string[],
    };
  });
  return { exact_count: data.exact_count as number, suggestions };
}

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
    case "suggestions":
      return { type, data: parseSuggestionResult(data) };
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

export interface SessionView {
  session_id: string;
  lease: "owned" | "takeover_required";
  event_cursor: number;
  conversation: Array<{ role: "shopper" | "copilot"; text: string }>;
  requires_reconciliation: boolean;
  task: {
    task_id: string;
    status: string;
    pending_question: unknown | null;
    suggestions?: SuggestionResult | null;
    pause_message?: string | null;
  } | null;
}

export interface SessionPersistence {
  loadSessionId(): string | undefined;
  saveSessionId(sessionId: string): void;
  clearSession(): void;
  loadEventCursor(): number;
  saveEventCursor(cursor: number): void;
}

export interface AgentTransport {
  createSession(tabId?: string): Promise<string>;
  restoreSession(sessionId: string, tabId: string): Promise<SessionView>;
  reconcile(
    sessionId: string,
    tabId: string,
    snapshot: Snapshot,
  ): Promise<SessionView>;
  takeover(sessionId: string, tabId: string): Promise<SessionView>;
  subscribe(
    sessionId: string,
    handler: (event: AgentEvent) => void,
    after?: number,
    onCursor?: (cursor: number) => void,
  ): () => void;
  submitMessage(
    sessionId: string,
    text: string,
    snapshot: Snapshot,
  ): Promise<void>;
  submitActionResult(sessionId: string, result: ActionResult): Promise<void>;
  submitAnswer(
    sessionId: string,
    taskId: string,
    questionId: string,
    text: string,
    snapshot: Snapshot,
  ): Promise<"resumed" | "awaiting_login">;
  stop(sessionId: string): Promise<void>;
  retry(sessionId: string, taskId: string): Promise<void>;
}

export interface StorefrontChannel {
  sendAction(action: Action): void;
  cancelTask(taskId: string): void;
  requestSnapshot(): void;
}

export class PanelController {
  readonly #root: HTMLElement;
  readonly #agent: AgentTransport;
  readonly #storefront: StorefrontChannel;
  readonly #persistence: SessionPersistence | undefined;
  readonly #tabId: string;
  #sessionId: string | undefined;
  #snapshot: Snapshot | undefined;
  #unsubscribe: (() => void) | undefined;
  #activeTaskId: string | undefined;
  #submitting = false;
  readonly #cancelledTaskIds = new Set<string>();
  readonly #questionActionIds = new Set<string>();
  #reconnecting = false;
  #waitingForLoginUrl: string | undefined;

  constructor(
    root: HTMLElement,
    agent: AgentTransport,
    storefront: StorefrontChannel,
    options?: { persistence?: SessionPersistence; tabId?: string },
  ) {
    this.#root = root;
    this.#agent = agent;
    this.#storefront = storefront;
    this.#persistence = options?.persistence;
    this.#tabId = options?.tabId ?? "tab-local";
    this.#render();
  }

  async start(): Promise<void> {
    const savedSessionId = this.#persistence?.loadSessionId();
    if (savedSessionId !== undefined) {
      this.#sessionId = savedSessionId;
      this.#reconnecting = true;
      this.#setInputEnabled(false);
      this.#setStatus("Reconnecting…");
      let state: SessionView;
      try {
        state = await this.#agent.restoreSession(savedSessionId, this.#tabId);
      } catch (error) {
        if (
          !(error instanceof Error) ||
          !/^Session restore failed with (404|410)$/.test(error.message)
        )
          throw error;
        this.#persistence?.clearSession();
        this.#reconnecting = false;
        await this.#startFreshSession();
        this.#appendMessage(
          "copilot",
          "انتهت جلسة المساعد السابقة. بدأت جلسة جديدة.",
        );
        return;
      }
      if (state.lease === "takeover_required") {
        this.#renderTakeover();
        this.#setStatus("This task is active in another tab");
        return;
      }
      this.#storefront.requestSnapshot();
      return;
    }
    await this.#startFreshSession();
  }

  async #startFreshSession(): Promise<void> {
    this.#sessionId = await this.#agent.createSession(this.#tabId);
    this.#persistence?.saveSessionId(this.#sessionId);
    this.#subscribe(this.#persistence?.loadEventCursor() ?? 0);
    this.#storefront.requestSnapshot();
    this.#setStatus("بانتظار اتصال المتجر…");
  }

  dispose(): void {
    this.#unsubscribe?.();
  }

  receiveStorefront(message: StorefrontMessage): void {
    if (message.type === "snapshot") {
      this.#snapshot = message.snapshot;
      if (
        this.#waitingForLoginUrl !== undefined &&
        message.snapshot.url !== this.#waitingForLoginUrl
      ) {
        this.#waitingForLoginUrl = undefined;
        const continueButton = this.#root.querySelector<HTMLButtonElement>(
          '[data-question-option="Continue"]',
        );
        if (continueButton !== null) continueButton.disabled = false;
        this.#root.querySelector("#login-wait-hint")?.remove();
        this.#setStatus(
          "اتغيرت صفحة المتجر. اختر متابعة للتحقق من سجل الطلبات.",
        );
      }
      if (this.#reconnecting && this.#sessionId !== undefined) {
        void this.#completeRecovery(message.snapshot);
        return;
      }
      if (this.#activeTaskId === undefined && !this.#submitting) {
        this.#setInputEnabled(true);
        this.#setStatus("جاهز لاستقبال طلبك");
      }
      return;
    }
    this.#snapshot = message.result.snapshot;
    const questionKey = `${message.result.task_id}:${message.result.action_id}`;
    if (this.#questionActionIds.delete(questionKey)) return;
    if (this.#sessionId !== undefined) {
      void this.#agent.submitActionResult(this.#sessionId, message.result);
    }
  }

  async #completeRecovery(snapshot: Snapshot): Promise<void> {
    if (this.#sessionId === undefined) return;
    const state = await this.#agent.reconcile(
      this.#sessionId,
      this.#tabId,
      snapshot,
    );
    this.#restoreView(state);
    this.#subscribe(state.event_cursor);
    this.#reconnecting = false;
  }

  #subscribe(after: number): void {
    if (this.#sessionId === undefined) return;
    this.#unsubscribe?.();
    this.#unsubscribe = this.#agent.subscribe(
      this.#sessionId,
      (event) => this.#receiveAgent(event),
      after,
      (cursor) => this.#persistence?.saveEventCursor(cursor),
    );
  }

  #restoreView(state: SessionView): void {
    const conversation =
      this.#root.querySelector<HTMLOListElement>("#conversation");
    conversation?.replaceChildren();
    this.#root
      .querySelector<HTMLElement>("#pending-question")
      ?.replaceChildren();
    for (const message of state.conversation)
      this.#appendMessage(message.role, message.text);
    this.#renderSuggestions(state.task?.suggestions ?? null);
    const taskIsActive =
      state.task !== null &&
      state.task.status !== "completed" &&
      state.task.status !== "cancelled";
    this.#activeTaskId = taskIsActive ? state.task?.task_id : undefined;
    if (state.task?.status === "paused") this.#renderRetry();
    if (
      taskIsActive &&
      state.task?.pending_question !== null &&
      state.task?.pending_question !== undefined
    ) {
      const question = parseAction(state.task.pending_question);
      if (question.type === "ask_shopper") {
        this.#registerQuestion(question);
        this.#renderQuestion(question);
      }
    }
    this.#setStatus(
      state.task?.status === "paused" && state.task.pause_message
        ? state.task.pause_message
        : taskIsActive
          ? "Reconnected"
          : "Ready",
    );
    this.#setTaskState(state.task?.status ?? "idle");
    this.#setInputEnabled(!taskIsActive);
  }

  #renderTakeover(): void {
    const container =
      this.#root.querySelector<HTMLElement>("#pending-question");
    if (container === null) return;
    const button = this.#root.ownerDocument.createElement("button");
    button.id = "takeover-session";
    button.type = "button";
    button.textContent = "Take over this task";
    button.addEventListener("click", () => {
      if (this.#sessionId === undefined) return;
      void this.#agent.takeover(this.#sessionId, this.#tabId).then(() => {
        container.replaceChildren();
        this.#setStatus("Reconnecting…");
        this.#storefront.requestSnapshot();
      });
    });
    container.replaceChildren(button);
  }

  #receiveAgent(event: AgentEvent): void {
    if (event.type === "task_started") {
      this.#setTaskState("active");
      this.#renderSuggestions(null);
      this.#submitting = false;
      this.#activeTaskId = event.data.task_id;
      this.#setInputEnabled(false);
    } else if (event.type === "narration") {
      this.#setStatus(event.data.text);
      this.#appendMessage("copilot", event.data.text);
    } else if (event.type === "suggestions") {
      this.#renderSuggestions(event.data);
    } else if (event.type === "action") {
      if (this.#cancelledTaskIds.has(event.data.action.task_id)) return;
      if (event.data.action.type === "ask_shopper") {
        this.#registerQuestion(event.data.action);
        this.#renderQuestion(event.data.action);
      } else {
        this.#storefront.sendAction(event.data.action);
      }
    } else if (event.type === "done") {
      this.#setTaskState("completed");
      this.#root
        .querySelector<HTMLElement>("#pending-question")
        ?.replaceChildren();
      this.#setStatus(
        event.data.language === "ar" ? "اكتملت المهمة" : "Task complete",
      );
      this.#appendMessage("copilot", event.data.summary);
      this.#activeTaskId = undefined;
      this.#setInputEnabled(true);
    } else if (event.type === "cancelled") {
      this.#setTaskState("cancelled");
      this.#root
        .querySelector<HTMLElement>("#pending-question")
        ?.replaceChildren();
      this.#setStatus("تم إيقاف المهمة");
      this.#activeTaskId = undefined;
      this.#setInputEnabled(true);
    } else if (event.type === "error") {
      this.#setTaskState("paused");
      this.#setStatus(event.data.message);
      this.#renderRetry();
      this.#setInputEnabled(false);
    }
  }

  #renderRetry(): void {
    const container =
      this.#root.querySelector<HTMLElement>("#pending-question");
    if (container === null || this.#activeTaskId === undefined) return;
    const button = this.#root.ownerDocument.createElement("button");
    button.id = "retry-task";
    button.type = "button";
    button.textContent = "حاول تاني / Retry";
    button.addEventListener("click", () => {
      if (this.#sessionId === undefined || this.#activeTaskId === undefined)
        return;
      container.replaceChildren();
      this.#setStatus("بحاول تاني…");
      void this.#agent.retry(this.#sessionId, this.#activeTaskId);
    });
    container.replaceChildren(button);
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
        <section id="suggestions" class="suggestions" aria-label="اقتراحات المنتجات" aria-live="polite"></section>
        <div id="pending-question"></div>
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
        this.#submitting = true;
        this.#setInputEnabled(false);
        void this.#agent
          .submitMessage(this.#sessionId, text, this.#snapshot)
          .catch(() => {
            if (this.#activeTaskId !== undefined) return;
            this.#submitting = false;
            this.#setStatus("تعذر إرسال الطلب. حاول تاني.");
            this.#setInputEnabled(true);
          });
      });

    this.#root
      .querySelector<HTMLButtonElement>("#stop-task")
      ?.addEventListener("click", () => {
        if (this.#sessionId === undefined) return;
        if (this.#activeTaskId !== undefined) {
          this.#cancelledTaskIds.add(this.#activeTaskId);
          this.#storefront.cancelTask(this.#activeTaskId);
        }
        void this.#agent.stop(this.#sessionId);
      });
  }

  #renderQuestion(action: Extract<Action, { type: "ask_shopper" }>): void {
    const container =
      this.#root.querySelector<HTMLElement>("#pending-question");
    if (container === null) return;
    this.#waitingForLoginUrl = undefined;
    container.replaceChildren();
    const card = this.#root.ownerDocument.createElement("section");
    card.className =
      action.kind === "confirmation"
        ? "question-card confirmation-card"
        : "question-card";
    card.setAttribute(
      "aria-label",
      action.kind === "confirmation"
        ? action.options.includes("تأكيد")
          ? "تأكيد إجراء مؤثر"
          : "Confirm Guarded Mutation"
        : "سؤال من مساعد التسوّق",
    );
    const question = this.#root.ownerDocument.createElement("p");
    question.textContent = action.question;
    card.append(question);
    const submitAnswer = (text: string) => {
      if (this.#sessionId === undefined || this.#snapshot === undefined) return;
      const currentUrl = this.#snapshot.url;
      const buttons = Array.from(card.querySelectorAll("button"));
      for (const button of buttons) button.disabled = true;
      void this.#agent
        .submitAnswer(
          this.#sessionId,
          action.task_id,
          action.action_id,
          text,
          this.#snapshot,
        )
        .then((status) => {
          if (!container.contains(card)) return;
          if (status === "resumed") {
            container.replaceChildren();
            return;
          }
          if (this.#snapshot?.url !== currentUrl) {
            for (const button of buttons) button.disabled = false;
            this.#setStatus(
              "اتغيرت صفحة المتجر. اختر متابعة للتحقق من سجل الطلبات.",
            );
            return;
          }
          this.#waitingForLoginUrl = currentUrl;
          for (const button of buttons)
            button.disabled = button.dataset.questionOption === "Continue";
          let hint = card.querySelector<HTMLElement>("#login-wait-hint");
          if (hint === null) {
            hint = this.#root.ownerDocument.createElement("p");
            hint.id = "login-wait-hint";
            hint.setAttribute("role", "status");
            card.append(hint);
          }
          hint.textContent =
            "سجّل الدخول بنفسك في المتجر أولًا، وبعد انتقال الصفحة اختَر متابعة. لن أقرأ بيانات الدخول.";
        })
        .catch(() => {
          if (!container.contains(card)) return;
          for (const button of buttons) button.disabled = false;
          this.#setStatus("تعذر إرسال إجابتك. حاول تاني أو أوقف المهمة.");
        });
    };
    for (const optionText of action.options) {
      const option = this.#root.ownerDocument.createElement("button");
      option.type = "button";
      option.textContent = optionText;
      option.dataset.questionOption = optionText;
      option.addEventListener("click", () => submitAnswer(optionText));
      card.append(option);
    }
    if (action.options.length === 0) {
      const form = this.#root.ownerDocument.createElement("form");
      form.id = "question-answer-form";
      const input = this.#root.ownerDocument.createElement("input");
      input.id = "question-answer-input";
      input.required = true;
      input.setAttribute("aria-label", "Your answer");
      const submit = this.#root.ownerDocument.createElement("button");
      submit.type = "submit";
      submit.textContent = "Send answer";
      form.append(input, submit);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const text = input.value.trim();
        if (text !== "") submitAnswer(text);
      });
      card.append(form);
    }
    container.append(card);
  }

  #registerQuestion(action: Extract<Action, { type: "ask_shopper" }>): void {
    this.#questionActionIds.add(`${action.task_id}:${action.action_id}`);
    this.#storefront.sendAction(action);
  }

  #renderSuggestions(result: SuggestionResult | null): void {
    const container = this.#root.querySelector<HTMLElement>("#suggestions");
    if (container === null) return;
    container.replaceChildren();
    if (result === null) return;
    for (const suggestion of result.suggestions) {
      const article = this.#root.ownerDocument.createElement("article");
      article.className = `suggestion-card suggestion-${suggestion.label}`;
      article.dataset.productId = suggestion.id;
      article.dataset.matchKind = suggestion.label;
      const label = this.#root.ownerDocument.createElement("p");
      label.className = "suggestion-label";
      label.textContent = {
        exact_match: "مطابق / Exact Match",
        alternative: "بديل / Alternative",
        styling_suggestion: "تنسيق / Styling Suggestion",
      }[suggestion.label];
      const title = this.#root.ownerDocument.createElement("h2");
      title.textContent = suggestion.name;
      const price = this.#root.ownerDocument.createElement("p");
      price.textContent = `${suggestion.price} ${suggestion.currency}`;
      const reason = this.#root.ownerDocument.createElement("p");
      reason.textContent = suggestion.reason;
      article.append(label, title, price, reason);
      if (suggestion.unmet.length > 0) {
        const unmet = this.#root.ownerDocument.createElement("p");
        unmet.textContent = `غير متحقق / Unmet: ${suggestion.unmet.join(", ")}`;
        article.append(unmet);
      }
      container.append(article);
    }
  }

  #setStatus(message: string): void {
    const status = this.#root.querySelector<HTMLElement>("#task-status");
    if (status !== null) status.textContent = message;
  }

  #setTaskState(value: string): void {
    const status = this.#root.querySelector<HTMLElement>("#task-status");
    if (status !== null) status.dataset.taskState = value;
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
