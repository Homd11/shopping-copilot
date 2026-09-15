import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

describe("store health", () => {
  it("serves the hello page", async () => {
    const response = await request(createApp()).get("/");

    expect(response.status).toBe(200);
    expect(response.type).toMatch(/html/);
    expect(response.text).toContain("Shopping Copilot Store");
  });
});
