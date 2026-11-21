import { browser } from "./browser.js";
import { describe, expect, it } from "vitest";
import { createApp } from "./app.js";
import { GuardedCart } from "../src/guarded-cart.js";
import type { ProductRepository } from "../src/product-repository.js";
import { StoreEventLog, memorySink } from "../src/event-log.js";

const blue = { product_id: "shoe-09", size: "43", color: "blue", quantity: 2 };
const beige = { ...blue, color: "beige" };
const black = {
  product_id: "shoe-01",
  size: "41",
  color: "black",
  quantity: 3,
};
const swapFor = (revision: number, id: string, extra = {}) => ({
  product_id: "shoe-09",
  size: "43",
  color: "blue",
  new_color: "beige",
  revision,
  operation_id: id,
  ...extra,
});

async function cartWith(
  client: Awaited<ReturnType<typeof browser>>,
  lines: (typeof blue)[],
) {
  let revision = 0;
  for (const line of lines) {
    await client
      .post("/cart/items")
      .send({ ...line, revision, operation_id: `add-${revision}` })
      .expect(200);
    revision++;
  }
  return revision;
}

describe("Colour swap of a cart line", () => {
  it("keeps size and quantity, changes colour, and makes one replace Undo", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue]);
    const swap = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"));
    expect(swap.status).toBe(200);
    expect(swap.body.lines).toEqual([beige]);
    expect(swap.body.undo.kind).toBe("replace");
    expect(swap.body.undo.description).toBe(
      "تبديل اللون: ممشى النيل · 43: blue → beige",
    );
    expect(swap.body.undo.description_en).toBe(
      "Colour swap: Nile Walk · 43: blue → beige",
    );
  });

  it("one Undo restores the old line exactly, position included", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue, black]);
    const swap = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"));
    expect(swap.body.lines).toEqual([beige, black]);
    const undone = await client.post("/cart/undo").send({
      revision: revision + 1,
      operation_id: "u1",
      undo_id: swap.body.undo.id,
    });
    expect(undone.status).toBe(200);
    expect(undone.body.lines).toEqual([blue, black]);
    expect(undone.body.undo).toBeNull();
  });

  it("merges into an existing line and one Undo restores both lines", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const existing = { ...beige, quantity: 5 };
    const revision = await cartWith(client, [blue, existing]);
    const swap = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"));
    expect(swap.body.lines).toEqual([{ ...beige, quantity: 7 }]);
    const undone = await client.post("/cart/undo").send({
      revision: revision + 1,
      operation_id: "u1",
      undo_id: swap.body.undo.id,
    });
    expect(undone.body.lines).toEqual([blue, existing]);
  });

  it("refuses a merge whose quantity would exceed 99", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [
      { ...blue, quantity: 60 },
      { ...beige, quantity: 50 },
    ]);
    const swap = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"));
    expect(swap.status).toBe(409);
    expect(swap.body.error).toBe("invalid_or_stale_cart_edit");
    expect((await client.get("/cart/state")).body.revision).toBe(revision);
  });

  it("is never coalesced with an earlier quantity Undo", async () => {
    const client = await browser(createApp({ evaluation: true }));
    let revision = await cartWith(client, [{ ...blue, quantity: 1 }]);
    const quantity = await client
      .post("/cart/quantity")
      .send({ ...blue, quantity: 2, revision, operation_id: "q1" });
    revision++;
    const swap = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"));
    expect(swap.body.undo.id).not.toBe(quantity.body.undo.id);
    expect(swap.body.undo.kind).toBe("replace");
    const undone = await client.post("/cart/undo").send({
      revision: revision + 1,
      operation_id: "u1",
      undo_id: swap.body.undo.id,
    });
    expect(undone.body.lines).toEqual([blue]);
  });

  it("refuses a colour the product does not offer with variant_unavailable", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue]);
    const refused = await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1", { new_color: "purple" }));
    expect(refused.status).toBe(409);
    expect(refused.body.error).toBe("variant_unavailable");
    const state = (await client.get("/cart/state")).body;
    expect(state.lines).toEqual([blue]);
    expect(state.revision).toBe(revision);
  });

  it("refuses same colour and a missing line as invalid_or_stale_cart_edit", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue]);
    const changes = [
      { new_color: "blue" },
      { color: "beige", new_color: "blue" },
      { size: "41" },
      { product_id: "shoe-01", color: "black", new_color: "blue" },
    ];
    for (const [index, change] of changes.entries()) {
      const refused = await client
        .post("/cart/replace")
        .send(swapFor(revision, `bad-${index}`, change));
      expect(refused.status).toBe(409);
      expect(refused.body.error).toBe("invalid_or_stale_cart_edit");
    }
    const state = (await client.get("/cart/state")).body;
    expect(state.lines).toEqual([blue]);
    expect(state.revision).toBe(revision);
  });

  it("refuses an unavailable product with variant_unavailable", () => {
    const product = {
      available: true,
      sizes: ["43"],
      colors: ["blue", "beige"],
    };
    const repository = {
      get: () => product,
      productRevision: () => 1,
      revision: () => 1,
    } as unknown as ProductRepository;
    const cart = new GuardedCart(() => 0, repository);
    expect(cart.seed([{ ...blue }])).toBe(true);
    product.available = false;
    const input = swapFor(cart.revision, "s1");
    expect(cart.replaceRefusal(input)).toBe("variant_unavailable");
    expect(cart.edit("replace", input)).toBe(false);
    expect(cart.lines).toEqual([blue]);
  });

  it("rejects a stale revision and a repeated operation id", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue]);
    const stale = await client
      .post("/cart/replace")
      .send(swapFor(revision - 1, "s0"));
    expect(stale.status).toBe(409);
    expect(stale.body.error).toBe("invalid_or_stale_cart_edit");
    const staleBad = await client
      .post("/cart/replace")
      .send(swapFor(revision - 1, "s0b", { new_color: "purple" }));
    expect(staleBad.body.error).toBe("invalid_or_stale_cart_edit");
    await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"))
      .expect(200);
    const repeat = await client
      .post("/cart/replace")
      .send(swapFor(revision + 1, "s1", { color: "beige", new_color: "blue" }));
    expect(repeat.status).toBe(409);
    expect((await client.get("/cart/state")).body.lines).toEqual([beige]);
  });

  it("logs replace with the outcome only", async () => {
    const sink = memorySink();
    const events = new StoreEventLog(sink, "test-release");
    const client = await browser(createApp({ evaluation: true, events }));
    const revision = await cartWith(client, [blue]);
    await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"))
      .expect(200);
    await client
      .post("/cart/replace")
      .send(
        swapFor(revision + 1, "s2", { color: "beige", new_color: "purple" }),
      )
      .expect(409);
    const records = sink.records.filter((r) => r.change === "replace");
    expect(records.map((r) => [r.outcome, r.status])).toEqual([
      ["ok", 200],
      ["rejected", 409],
    ]);
    for (const record of records)
      expect(Object.keys(record).sort()).toEqual([
        "change",
        "event",
        "outcome",
        "release",
        "status",
        "time",
      ]);
    const text = records.map((r) => JSON.stringify(r)).join("\n");
    for (const leak of ["shoe-09", "beige", "purple", "43", "quantity"])
      expect(text).not.toContain(leak);
  });

  it("invalidates a pending clear confirmation like any other cart edit", async () => {
    const client = await browser(createApp({ evaluation: true }));
    const revision = await cartWith(client, [blue]);
    const token = (
      await client
        .post("/__copilot/manual-confirmation")
        .send({ kind: "clear_cart", cart_revision: revision })
        .expect(201)
    ).body.token;
    await client
      .post("/cart/replace")
      .send(swapFor(revision, "s1"))
      .expect(200);
    expect(
      (
        await client
          .post("/cart/clear")
          .type("form")
          .send({
            copilot_confirmation: token,
            cart_revision: String(revision),
          })
      ).status,
    ).toBe(403);
  });
});

describe("Swap control on the rendered cart line", () => {
  async function render(lines: (typeof blue)[]) {
    const client = await browser(createApp({ evaluation: true }));
    await client.post("/__test/cart").send({ lines }).expect(204);
    return (await client.get("/cart/state")).body.html as string;
  }

  it("has a swap form with distinct accessible names and only the other colours", async () => {
    const html = await render([blue]);
    expect(html).toContain('action="/cart/replace"');
    expect(html).toContain('data-cart-edit="replace"');
    expect(html).toContain("اللون الجديد — ممشى النيل</label>");
    expect(html).toContain("غيّر اللون — ممشى النيل</button>");
    expect(html.match(/<select[^>]*>(.*?)<\/select>/s)![1]).toBe(
      '<option value="beige">beige</option>',
    );
    expect(html).toContain("تحديث الكمية — ممشى النيل");
    expect(html).toContain("حذف المنتج — ممشى النيل");
  });

  it("shows no swap control for a single-colour product", async () => {
    const html = await render([
      { product_id: "clothing-01", size: "M", color: "black", quantity: 1 },
    ]);
    expect(html).not.toContain("/cart/replace");
    expect(html).not.toContain("<select");
  });
});
