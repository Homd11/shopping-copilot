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
      filters: {
        type: "running",
        min_price: null,
        max_price: { amount: "2000", currency: "EGP" },
      },
      product_ids: ["shoe-01", "shoe-02", "shoe-03"],
      product_count: 3,
    });
  });

  it("reports exact decimal Money in authoritative Storefront state", async () => {
    const response = await request(createApp()).get(
      "/__test/state?category=bags&max_price=1500.50",
    );

    expect(response.status).toBe(200);
    expect(response.body.filters.max_price).toEqual({
      amount: "1500.50",
      currency: "EGP",
    });
  });

  it("serves all four bilingual category links from the home page", async () => {
    const response = await request(createApp()).get("/");

    for (const href of [
      "/c/shoes",
      "/c/clothing",
      "/c/bags",
      "/c/electronics",
    ]) {
      expect(response.text).toContain(`href="${href}"`);
    }
    expect(response.text).toContain("Shoes");
    expect(response.text).toContain("الشنط");
  });

  it("applies generic URL filters and sorting on every category", async () => {
    const response = await request(createApp()).get(
      "/c/clothing?q=jacket&type=outerwear&min_price=1000&max_price=1800&size=L&color=black&availability=available&sort=cheapest",
    );

    expect(response.status).toBe(200);
    expect(response.text).toContain("جاكيت القاهرة");
    expect(response.text).toContain('name="q"');
    expect(response.text).toContain('name="availability"');
    expect(response.text).toContain('name="sort"');
    expect(response.text.match(/<article /g)).toHaveLength(1);
  });

  it("reports canonical generic filter state for Evaluation Cases", async () => {
    const response = await request(createApp()).get(
      "/__test/state?category=bags&q=Nile&size=M&availability=available&sort=newest",
    );

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      category: "bags",
      filters: {
        q: "Nile",
        type: null,
        min_price: null,
        max_price: null,
        size: "M",
        color: null,
        availability: "available",
        sort: "newest",
      },
      product_ids: ["bag-01"],
      product_count: 1,
    });
  });

  it("renders an explicit empty state without broadening constraints", async () => {
    const response = await request(createApp()).get(
      "/c/shoes?size=99&color=purple&availability=available",
    );

    expect(response.status).toBe(200);
    expect(response.text).toContain("0 منتجات");
    expect(response.text).toContain("لا توجد منتجات مطابقة");
    expect(response.text.match(/<article /g)).toBeNull();
  });

  it("returns not found for an unknown category instead of guessing", async () => {
    const response = await request(createApp()).get("/c/toys");

    expect(response.status).toBe(404);
  });
});
