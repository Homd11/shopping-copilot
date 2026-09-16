import { executeAction } from "./actions.js";
import { SnapshotBuilder, type SnapshotBuilderOptions } from "./snapshot.js";
import { parseAction, type Action, type ActionResult } from "./types.js";

const PENDING_NAVIGATION_KEY = "shopping-copilot.pending-navigation";
const ACTION_LEDGER_KEY = "shopping-copilot.action-ledger";

export interface StorageLike {
  getItem(key: string): string | null;
  removeItem(key: string): void;
  setItem(key: string, value: string): void;
}

export interface BridgeRuntimeOptions extends SnapshotBuilderOptions {
  document: Document;
  panelOrigin: string;
  storage: StorageLike;
  currentUrl: () => string;
  navigate: (url: URL) => void;
  post: (message: unknown) => void;
  settle?: () => Promise<void>;
}

type BridgeMessage =
  | { type: "action"; action: unknown }
  | { type: "request_snapshot" };

interface ActionLedger {
  activeTaskId: string | null;
  completedActionIds: string[];
  highestSequenceByTask: Record<string, number>;
  retiredTaskIds: string[];
}

function emptyLedger(): ActionLedger {
  return {
    activeTaskId: null,
    completedActionIds: [],
    highestSequenceByTask: {},
    retiredTaskIds: [],
  };
}

function isBridgeMessage(value: unknown): value is BridgeMessage {
  if (typeof value !== "object" || value === null || !("type" in value))
    return false;
  if (value.type === "request_snapshot") return true;
  return value.type === "action" && "action" in value;
}

async function settleDocument(document: Document): Promise<void> {
  const view = document.defaultView;
  if (view === null) return;
  await new Promise<void>((resolve) =>
    view.requestAnimationFrame(() => resolve()),
  );
  await new Promise<void>((resolve) =>
    view.requestAnimationFrame(() => resolve()),
  );
  await new Promise<void>((resolve) => view.setTimeout(resolve, 300));
}

function readLedger(storage: StorageLike): ActionLedger {
  const stored = storage.getItem(ACTION_LEDGER_KEY);
  if (stored === null) return emptyLedger();
  try {
    const parsed = JSON.parse(stored) as Partial<ActionLedger>;
    const highestSequenceByTask = parsed.highestSequenceByTask ?? {};
    const knownTaskIds = Object.keys(highestSequenceByTask);
    return {
      activeTaskId: parsed.activeTaskId ?? knownTaskIds.at(-1) ?? null,
      completedActionIds: parsed.completedActionIds ?? [],
      highestSequenceByTask,
      retiredTaskIds: parsed.retiredTaskIds ?? knownTaskIds.slice(0, -1),
    };
  } catch {
    return emptyLedger();
  }
}

function acceptAction(storage: StorageLike, action: Action): boolean {
  const ledger = readLedger(storage);
  if (ledger.retiredTaskIds.includes(action.task_id)) return false;
  if (ledger.activeTaskId === null) {
    if (action.sequence_number !== 1) return false;
    ledger.activeTaskId = action.task_id;
  } else if (ledger.activeTaskId !== action.task_id) {
    if (action.sequence_number !== 1) return false;
    ledger.retiredTaskIds = [...ledger.retiredTaskIds, ledger.activeTaskId];
    ledger.activeTaskId = action.task_id;
  }
  const highestSequence = ledger.highestSequenceByTask[action.task_id] ?? 0;
  if (
    ledger.completedActionIds.includes(action.action_id) ||
    action.sequence_number <= highestSequence
  ) {
    return false;
  }
  ledger.highestSequenceByTask[action.task_id] = action.sequence_number;
  ledger.completedActionIds = [
    ...ledger.completedActionIds.slice(-99),
    action.action_id,
  ];
  storage.setItem(ACTION_LEDGER_KEY, JSON.stringify(ledger));
  return true;
}

export class BridgeRuntime {
  readonly #options: BridgeRuntimeOptions;
  readonly #builder: SnapshotBuilder;

  constructor(options: BridgeRuntimeOptions) {
    this.#options = options;
    this.#builder = new SnapshotBuilder(options.document, options);
  }

  start(): void {
    const pending = this.#options.storage.getItem(PENDING_NAVIGATION_KEY);
    if (pending === null) {
      this.#options.post({ type: "snapshot", snapshot: this.#builder.build() });
      return;
    }

    this.#options.storage.removeItem(PENDING_NAVIGATION_KEY);
    const action = parseAction(JSON.parse(pending));
    const result: ActionResult = {
      v: 1,
      task_id: action.task_id,
      action_id: action.action_id,
      sequence_number: action.sequence_number,
      status: "navigated",
      snapshot: this.#builder.build(),
    };
    this.#options.post({ type: "action_result", result });
  }

  async receive(origin: string, payload: unknown): Promise<void> {
    if (origin !== this.#options.panelOrigin || !isBridgeMessage(payload))
      return;
    if (payload.type === "request_snapshot") {
      this.#options.post({ type: "snapshot", snapshot: this.#builder.build() });
      return;
    }
    const action = parseAction(payload.action);
    if (!acceptAction(this.#options.storage, action)) {
      const staleResult: ActionResult = {
        v: 1,
        task_id: action.task_id,
        action_id: action.action_id,
        sequence_number: action.sequence_number,
        status: "stale",
        snapshot: this.#builder.build(),
      };
      this.#options.post({ type: "action_result", result: staleResult });
      return;
    }
    let navigationStarted = false;
    const result = await executeAction(action, {
      builder: this.#builder,
      currentUrl: this.#options.currentUrl,
      navigate: async (url) => {
        navigationStarted = true;
        this.#options.storage.setItem(
          PENDING_NAVIGATION_KEY,
          JSON.stringify(action),
        );
        this.#options.navigate(url);
      },
      settle:
        this.#options.settle ?? (() => settleDocument(this.#options.document)),
    });
    if (!navigationStarted)
      this.#options.post({ type: "action_result", result });
  }

  snapshot() {
    return this.#builder.build();
  }
}

declare global {
  interface Window {
    __copilot?: {
      snapshot: () => ReturnType<BridgeRuntime["snapshot"]>;
      run: (action: Action) => Promise<void>;
    };
  }
}

if (typeof window !== "undefined" && window.parent !== window) {
  const panelOrigin = "http://localhost:4100";
  const runtime = new BridgeRuntime({
    document,
    panelOrigin,
    storage: window.sessionStorage,
    currentUrl: () => window.location.href,
    navigate: (url) => window.location.assign(url),
    post: (message) => window.parent.postMessage(message, panelOrigin),
  });
  window.addEventListener("message", (event) => {
    if (event.source !== window.parent) return;
    void runtime.receive(event.origin, event.data);
  });
  window.__copilot = {
    snapshot: () => runtime.snapshot(),
    run: (action) => runtime.receive(panelOrigin, { type: "action", action }),
  };
  runtime.start();
}
