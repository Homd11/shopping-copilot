import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

describe("fictional guarded Storefront mutations", () => {
  it("rejects an unconfirmed bulk clear and consumes one matching confirmation", async () => {
    const app = createApp();
    const seed = await request(app)
      .post("/__test/cart")
      .send({ lines: [{ product_id: "shoe-09", quantity: 2 }] });
    expect(seed.status).toBe(204);
    const before = await request(app).get("/__test/cart-state");
    expect(before.body).toMatchObject({
      revision: 1,
      lines: [{ product_id: "shoe-09", quantity: 2 }],
    });
    const noConfirmation = await request(app)
      .post("/cart/clear")
      .type("form")
      .send({ cart_revision: "1" });
    expect(noConfirmation.status).toBe(403);

    const token = "confirmation-1234567890abcdef1234567890abcdef";
    expect(
      (
        await request(app).post("/__copilot/confirmations").send({
          token,
          task_id: "task-1",
          kind: "clear_cart",
          cart_revision: 1,
        })
      ).status,
    ).toBe(201);
    const clear = await request(app)
      .post("/cart/clear")
      .type("form")
      .send({ cart_revision: "1", copilot_confirmation: token });
    expect(clear.status).toBe(303);
    expect((await request(app).get("/__test/cart-state")).body.lines).toEqual(
      [],
    );
    expect(
      (
        await request(app).post("/cart/clear").type("form").send({
          cart_revision: "1",
          copilot_confirmation: token,
        })
      ).status,
    ).toBe(403);
  });

  it("submits only a fictional order with Shopper-entered dummy fields and fresh matching confirmation", async () => {
    const app = createApp();
    await request(app)
      .post("/__test/cart")
      .send({ lines: [{ product_id: "shoe-09", quantity: 1 }] });
    const token = "confirmation-abcdef1234567890abcdef1234567890";
    await request(app).post("/__copilot/confirmations").send({
      token,
      task_id: "task-2",
      kind: "submit_checkout",
      cart_revision: 1,
    });
    const noCard = await request(app)
      .post("/checkout/submit")
      .type("form")
      .send({
        cart_revision: "1",
        copilot_confirmation: token,
      });
    expect(noCard.status).toBe(400);
    expect(noCard.text).toContain("/bridge/runtime.js");
    const reused = await request(app)
      .post("/checkout/submit")
      .type("form")
      .send({
        cart_revision: "1",
        copilot_confirmation: token,
        card_number: "0000 0000 0000 0000",
        card_expiry: "01/30",
        card_security_code: "000",
      });
    expect(reused.status).toBe(403);
    const fresh = "confirmation-11111111111111111111111111111111";
    await request(app).post("/__copilot/confirmations").send({
      token: fresh,
      task_id: "task-2",
      kind: "submit_checkout",
      cart_revision: 1,
    });
    const submitted = await request(app)
      .post("/checkout/submit")
      .type("form")
      .send({
        cart_revision: "1",
        copilot_confirmation: fresh,
        card_number: "0000 0000 0000 0000",
        card_expiry: "01/30",
        card_security_code: "000",
      });
    expect(submitted.status).toBe(303);
    expect(submitted.headers.location).toMatch(/^\/order\/complete\//);
    const state = (await request(app).get("/__test/cart-state")).body;
    expect(state.lines).toEqual([]);
    expect(state.orders).toHaveLength(1);
    expect(JSON.stringify(state)).not.toContain("0000 0000 0000 0000");
  });

  it("rejects an expired or cart-stale confirmation at the mutation endpoint", async () => {
    let now = 1_000;
    const app = createApp({ clock: () => now });
    await request(app)
      .post("/__test/cart")
      .send({ lines: [{ product_id: "shoe-09", quantity: 1 }] });
    const staleToken = "confirmation-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    expect(
      (
        await request(app).post("/__copilot/confirmations").send({
          token: staleToken,
          task_id: "task-1",
          kind: "clear_cart",
          cart_revision: 1,
        })
      ).status,
    ).toBe(201);
    await request(app)
      .post("/__test/cart")
      .send({ lines: [{ product_id: "shoe-09", quantity: 2 }] });
    expect(
      (
        await request(app).post("/cart/clear").type("form").send({
          cart_revision: "1",
          copilot_confirmation: staleToken,
        })
      ).status,
    ).toBe(403);

    const expiringToken = "confirmation-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    await request(app).post("/__copilot/confirmations").send({
      token: expiringToken,
      task_id: "task-1",
      kind: "clear_cart",
      cart_revision: 2,
    });
    now += 60_000;
    expect(
      (
        await request(app).post("/cart/clear").type("form").send({
          cart_revision: "2",
          copilot_confirmation: expiringToken,
        })
      ).status,
    ).toBe(403);
    expect((await request(app).get("/__test/cart-state")).body.lines).toEqual([
      { product_id: "shoe-09", quantity: 2 },
    ]);
  });
});
