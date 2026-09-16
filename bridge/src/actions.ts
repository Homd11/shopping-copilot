import { SnapshotBuilder } from "./snapshot.js";
import type { Action, ActionResult, ActionResultStatus } from "./types.js";

export interface ActionEnvironment {
  builder: SnapshotBuilder;
  currentUrl: () => string;
  navigate: (url: URL) => Promise<void>;
  settle: () => Promise<void>;
}

function result(
  action: Action,
  status: ActionResultStatus,
  builder: SnapshotBuilder,
): ActionResult {
  return {
    v: 1,
    task_id: action.task_id,
    action_id: action.action_id,
    sequence_number: action.sequence_number,
    status,
    snapshot: builder.build(),
  };
}

function scrollIntoView(element: Element): void {
  if (
    "scrollIntoView" in element &&
    typeof element.scrollIntoView === "function"
  ) {
    element.scrollIntoView({ block: "center" });
  }
}

function setElementValue(element: Element, value: string): boolean {
  const view = element.ownerDocument.defaultView;
  if (view === null) return false;
  if (element instanceof view.HTMLInputElement) {
    const setter = Object.getOwnPropertyDescriptor(
      view.HTMLInputElement.prototype,
      "value",
    )?.set;
    setter?.call(element, value);
  } else if (element instanceof view.HTMLTextAreaElement) {
    const setter = Object.getOwnPropertyDescriptor(
      view.HTMLTextAreaElement.prototype,
      "value",
    )?.set;
    setter?.call(element, value);
  } else {
    return false;
  }
  element.dispatchEvent(new view.Event("input", { bubbles: true }));
  element.dispatchEvent(new view.Event("change", { bubbles: true }));
  return true;
}

export async function executeAction(
  action: Action,
  environment: ActionEnvironment,
): Promise<ActionResult> {
  if (action.type === "navigate") {
    const current = new URL(environment.currentUrl());
    const destination = new URL(action.url, current);
    if (destination.origin !== current.origin) {
      return result(action, "blocked", environment.builder);
    }
    await environment.navigate(destination);
    await environment.settle();
    return result(action, "navigated", environment.builder);
  }

  if (action.type === "ask_shopper" || action.type === "done") {
    return result(action, "ok", environment.builder);
  }

  const registered = environment.builder.resolve(action.id);
  if (registered === undefined)
    return result(action, "not_found", environment.builder);
  const { element, sensitive } = registered;
  if (action.type === "type" && sensitive) {
    return result(action, "blocked", environment.builder);
  }

  scrollIntoView(element);
  let status: ActionResultStatus = "ok";
  if (action.type === "click") {
    if (element instanceof element.ownerDocument.defaultView!.HTMLElement)
      element.click();
    else status = "not_found";
  } else if (action.type === "type") {
    if (!setElementValue(element, action.text)) status = "not_found";
    else if (action.submit) {
      const form = element.closest("form");
      if (form !== null && "requestSubmit" in form) form.requestSubmit();
    }
  } else if (action.type === "select") {
    const view = element.ownerDocument.defaultView;
    if (view !== null && element instanceof view.HTMLSelectElement) {
      const option = [...element.options].find(
        (candidate) =>
          candidate.value === action.option || candidate.text === action.option,
      );
      if (option === undefined) status = "not_found";
      else {
        element.value = option.value;
        element.dispatchEvent(new view.Event("change", { bubbles: true }));
      }
    } else status = "not_found";
  } else if (action.type === "spotlight") {
    element.setAttribute("data-copilot-spotlight", action.message);
  }

  await environment.settle();
  return result(action, status, environment.builder);
}
