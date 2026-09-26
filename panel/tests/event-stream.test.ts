import { expect, it } from "vitest";
import { subscribeAgentStream } from "../src/event-stream.js";

it("resumes after the cursor and does not repeat messages on reconnect", () => {
  const listeners = new Map<string, (event: MessageEvent<string>) => void>();
  const delivered: unknown[] = [];
  const cursors: number[] = [];
  let closed = false;
  const close = subscribeAgentStream(
    "/events?after=3",
    (e) => delivered.push(e),
    3,
    (c) => cursors.push(c),
    () => ({
      addEventListener: (name, listener) => {
        listeners.set(name, listener);
      },
      close: () => {
        closed = true;
      },
    }),
  );
  for (const id of ["3", "4", "4", "2", "5"])
    listeners.get("narration")!(
      new MessageEvent("narration", {
        lastEventId: id,
        data: JSON.stringify({ text: "Working" }),
      }),
    );
  expect(delivered).toHaveLength(2);
  expect(cursors).toEqual([4, 5]);
  close();
  expect(closed).toBe(true);
});
