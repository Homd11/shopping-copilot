import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

describe("Controlled Storefront", () => {
  it("serves an Arabic home page with a shoes category link", async () => {
    const response = await request(createApp()).get("/");

    expect(response.status).toBe(200);
    expect(response.type).toMatch(/html/);
    expect(response.text).toContain('<html lang="ar" dir="rtl">');
    expect(response.text).toContain('href="/c/shoes"');
    expect(response.text).toContain("الأحذية");
  });

  it("serves a semantic shoes page with deterministic Arabic filters", async () => {
    const response = await request(createApp()).get("/c/shoes");

    expect(response.status).toBe(200);
    expect(response.text).toContain('<form aria-label="فلترة الأحذية"');
    expect(response.text).toContain("<legend>نوع الحذاء</legend>");
    expect(response.text).toContain('name="type" value="running"');
    expect(response.text).toContain('for="max-price">أقصى سعر</label>');
    expect(response.text).toContain("تطبيق الفلاتر");
    expect(response.text).toContain(
      '<script type="module" src="/bridge/runtime.js"></script>',
    );
    expect(response.text.match(/<article /g)).toHaveLength(15);
  });

  it("filters running shoes by an inclusive maximum price in the URL", async () => {
    const response = await request(createApp()).get(
      "/c/shoes?type=running&max_price=2000",
    );

    expect(response.status).toBe(200);
    expect(response.text).toContain("3 منتجات");
    expect(response.text).toContain("عدّاء النيل");
    expect(response.text).not.toContain("ماراثون القاهرة");
    expect(response.text).toContain('value="2000"');
  });

  it("provides a deterministic reset endpoint for isolated Evaluation Cases", async () => {
    const response = await request(createApp()).post("/__test/reset");

    expect(response.status).toBe(204);
    expect(response.text).toBe("");
  });

  it("reports authoritative filtered Storefront state for Evaluation Cases", async () => {
    const response = await request(createApp()).get(
      "/__test/state?type=running&max_price=2000",
    );

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      filters: { type: "running", min_price: null, max_price: 2000 },
      product_ids: ["shoe-01", "shoe-02", "shoe-03"],
      product_count: 3,
    });
  });
});
