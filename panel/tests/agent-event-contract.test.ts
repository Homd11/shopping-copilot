import { describe, expect, it } from "vitest";

import { AGENT_EVENT_TYPES, parseAgentEvent } from "../src/panel.js";

describe("Agent event contract", () => {
  it("accepts a valid typed Action event", () => {
    const action = {
      v: 1,
      type: "navigate",
      task_id: "task-1",
      action_id: "action-1",
      sequence_number: 1,
      narration: "Applying filters.",
      url: "/c/shoes?type=running&max_price=2000",
    };

    expect(parseAgentEvent("action", { action })).toEqual({
      type: "action",
      data: { action },
    });
  });

  it("rejects unknown events and malformed payloads", () => {
    expect(() => parseAgentEvent("unexpected", {})).toThrow(/supported/);
    expect(() => parseAgentEvent("narration", {})).toThrow(/text/);
    expect(() =>
      parseAgentEvent("done", { summary: "Done", language: "fr" }),
    ).toThrow(/language/);
  });

  it("publishes the event names used by the EventSource subscription", () => {
    expect(AGENT_EVENT_TYPES).toEqual([
      "task_started",
      "narration",
      "action",
      "done",
      "cancelled",
      "error",
    ]);
  });
});
