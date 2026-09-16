import express, { type Express } from "express";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  filterShoes,
  type Product,
  type ShoeConstraints,
} from "./catalogue.js";
import { renderHome, renderShoes } from "./views.js";

function firstQueryValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function priceFromQuery(value: unknown): number | undefined {
  const text = firstQueryValue(value);
  if (text === undefined || text.trim() === "") return undefined;
  const amount = Number(text);
  return Number.isFinite(amount) && amount >= 0 ? amount : undefined;
}

function typeFromQuery(value: unknown): Product["type"] | undefined {
  return value === "running" || value === "casual" || value === "football"
    ? value
    : undefined;
}

function constraintsFromQuery(query: Record<string, unknown>): ShoeConstraints {
  return {
    type: typeFromQuery(query.type),
    minPrice: priceFromQuery(query.min_price),
    maxPrice: priceFromQuery(query.max_price),
  };
}

export function createApp(): Express {
  const app = express();
  const sourceDirectory = dirname(fileURLToPath(import.meta.url));
  app.use(
    "/bridge",
    express.static(resolve(sourceDirectory, "../../bridge/dist")),
  );

  app.get("/", (_request, response) => {
    response.type("html").send(renderHome());
  });

  app.get("/c/shoes", (request, response) => {
    const constraints = constraintsFromQuery(request.query);
    response
      .type("html")
      .send(renderShoes(filterShoes(constraints), constraints));
  });

  app.post("/__test/reset", (_request, response) => {
    response.status(204).send();
  });

  app.get("/__test/state", (request, response) => {
    const constraints = constraintsFromQuery(request.query);
    const products = filterShoes(constraints);
    response.json({
      filters: {
        type: constraints.type ?? null,
        min_price: constraints.minPrice ?? null,
        max_price: constraints.maxPrice ?? null,
      },
      product_ids: products.map((product) => product.id),
      product_count: products.length,
    });
  });

  return app;
}
