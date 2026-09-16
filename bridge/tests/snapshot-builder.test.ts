import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import { SnapshotBuilder } from "../src/snapshot.js";

describe("SnapshotBuilder", () => {
  it("describes Arabic category controls using their accessible names", () => {
    const dom = new JSDOM(
      `<!doctype html><html lang="ar"><head><title>الأحذية</title></head><body>
      <header><a href="/cart">السلة (0)</a></header>
      <main>
        <form aria-label="فلترة الأحذية">
          <fieldset><legend>نوع الحذاء</legend>
            <label><input type="radio" name="type" value="running"> جري</label>
          </fieldset>
          <label for="max-price">أقصى سعر</label>
          <input id="max-price" name="max_price" value="">
          <button>تطبيق الفلاتر</button>
        </form>
      </main>
    </body></html>`,
      { url: "http://localhost:4000/c/shoes" },
    );

    const snapshot = new SnapshotBuilder(dom.window.document, {
      isVisible: () => true,
      viewport: { w: 390, h: 844, scrollY: 0 },
    }).build();

    expect(snapshot).toMatchObject({
      v: 1,
      url: "http://localhost:4000/c/shoes",
      title: "الأحذية",
      lang: "ar",
      truncated: false,
    });
    expect(snapshot.elements).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          role: "link",
          name: "السلة (0)",
          region: "header",
        }),
        expect.objectContaining({
          role: "radio",
          name: "جري",
          group: "نوع الحذاء",
        }),
        expect.objectContaining({
          role: "textbox",
          name: "أقصى سعر",
          value: "",
        }),
        expect.objectContaining({ role: "button", name: "تطبيق الفلاتر" }),
      ]),
    );
  });

  it("represents a Sensitive Field without collecting its value or state", () => {
    const dom = new JSDOM(
      `<!doctype html><html><body>
      <label for="card">Card number</label>
      <input id="card" name="card_number" autocomplete="cc-number" value="4111111111111111">
    </body></html>`,
      { url: "http://localhost:4000/checkout" },
    );

    const snapshot = new SnapshotBuilder(dom.window.document, {
      isVisible: () => true,
      viewport: { w: 1280, h: 720, scrollY: 0 },
    }).build();

    expect(snapshot.elements).toEqual([
      expect.objectContaining({
        role: "textbox",
        name: "Card number",
        sensitive: true,
      }),
    ]);
    expect(snapshot.elements[0]).not.toHaveProperty("value");
  });
});
