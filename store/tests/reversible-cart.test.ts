import request from "supertest";
import { describe, expect, it } from "vitest";
import { createApp } from "../src/app.js";

const item = { product_id: "shoe-09", size: "43", color: "blue", quantity: 1 };
describe("Reversible cart HTTP journey", () => {
  it("adds a chosen variant and restores the exact empty cart once", async () => {
    const app = createApp();
    const add = await request(app)
      .post("/cart/items")
      .send({ ...item, revision: 0, operation_id: "add-1" });
    expect(add.status).toBe(200);
    expect(add.body.lines).toEqual([item]);
    const undo = await request(app)
      .post("/cart/undo")
      .send({ revision: 1, operation_id: "undo-1", undo_id: add.body.undo.id });
    expect(undo.status).toBe(200);
    expect(undo.body.lines).toEqual([]);
    expect(
      (
        await request(app)
          .post("/cart/items")
          .send({ ...item, revision: 2, operation_id: "add-1" })
      ).status,
    ).toBe(409);
  });
  it("coalesces same-line quantity changes and keeps the original ten-second deadline", async () => {
    let now = 0;
    const app = createApp({ clock: () => now });
    await request(app)
      .post("/cart/items")
      .send({ ...item, revision: 0, operation_id: "add" });
    const first = await request(app)
      .post("/cart/quantity")
      .send({ ...item, quantity: 2, revision: 1, operation_id: "q1" });
    now = 4000;
    const second = await request(app)
      .post("/cart/quantity")
      .send({ ...item, quantity: 3, revision: 2, operation_id: "q2" });
    expect(second.body.undo.id).toBe(first.body.undo.id);
    expect(second.body.undo.remaining_ms).toBe(6000);
    expect(second.body.undo.description).toContain("43 / blue: 1 → 3");
    const restored = await request(app)
      .post("/cart/undo")
      .send({ revision: 3, operation_id: "undo", undo_id: first.body.undo.id });
    expect(restored.body.lines).toEqual([item]);
  });
  it("removes the final line without Confirmation and can undo it exactly", async () => {
    const app = createApp();
    await request(app)
      .post("/cart/items")
      .send({ ...item, revision: 0, operation_id: "add" });
    const removed = await request(app)
      .post("/cart/remove")
      .send({ ...item, revision: 1, operation_id: "remove" });
    expect(removed.status).toBe(200);
    expect(removed.body.lines).toEqual([]);
    const undone = await request(app).post("/cart/undo").send({
      revision: 2,
      operation_id: "undo",
      undo_id: removed.body.undo.id,
    });
    expect(undone.body.lines).toEqual([item]);
  });
  it("rejects expired Undo, stale edits, invalid variants and unavailable stock", async () => {
    let now = 0;
    const app = createApp({ clock: () => now });
    const add = await request(app)
      .post("/cart/items")
      .send({ ...item, revision: 0, operation_id: "add" });
    now = 10000;
    expect(
      (
        await request(app).post("/cart/undo").send({
          revision: 1,
          operation_id: "undo",
          undo_id: add.body.undo.id,
        })
      ).status,
    ).toBe(409);
    for (const change of [
      { revision: 0 },
      { size: "99", revision: 1 },
      { quantity: -1, revision: 1 },
      { product_id: "shoe-05", revision: 1 },
    ]) {
      expect(
        (
          await request(app)
            .post("/cart/items")
            .send({ ...item, operation_id: "invalid", ...change })
        ).status,
      ).toBeGreaterThanOrEqual(400);
    }
    expect((await request(app).get("/cart/state")).body.lines).toEqual([item]);
  });
  it("invalidates guarded authority after a reversible edit", async () => {
    const app = createApp();
    await request(app)
      .post("/cart/items")
      .send({ ...item, revision: 0, operation_id: "add" })
      .expect(200);
    const token = "confirmation-abcdef1234567890abcdef1234567890";
    await request(app)
      .post("/__copilot/confirmations")
      .send({ token, task_id: "task-1", kind: "clear_cart", cart_revision: 1 })
      .expect(201);
    await request(app)
      .post("/cart/quantity")
      .send({ ...item, quantity: 2, revision: 1, operation_id: "q" })
      .expect(200);
    expect(
      (
        await request(app)
          .post("/cart/clear")
          .type("form")
          .send({ copilot_confirmation: token, cart_revision: "1" })
      ).status,
    ).toBe(403);
  });
});
