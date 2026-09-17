import express, { type Express } from "express";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  categories,
  filterProducts,
  type Category,
  type ProductConstraints,
  type ProductSort,
} from "./catalogue.js";
import { renderCategory, renderHome } from "./views.js";

function firstQueryValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function nonEmptyQueryValue(value: unknown): string | undefined {
  const text = firstQueryValue(value)?.trim();
  return text === undefined || text === "" ? undefined : text;
}

function priceFromQuery(value: unknown): number | undefined {
  const text = nonEmptyQueryValue(value);
  if (text === undefined) return undefined;
  const amount = Number(text);
  return Number.isFinite(amount) && amount >= 0 ? amount : undefined;
}

function categoryFromValue(value: unknown): Category | undefined {
  return categories.find((category) => category === value);
}

function availabilityFromQuery(value: unknown): boolean | undefined {
  if (value === "available") return true;
  if (value === "unavailable") return false;
  return undefined;
}

function sortFromQuery(value: unknown): ProductSort | undefined {
  return value === "cheapest" || value === "newest" ? value : undefined;
}

function constraintsFromQuery(
  category: Category,
  query: Record<string, unknown>,
): ProductConstraints {
  return {
    category,
    query: nonEmptyQueryValue(query.q),
    type: nonEmptyQueryValue(query.type),
    minPrice: priceFromQuery(query.min_price),
    maxPrice: priceFromQuery(query.max_price),
    size: nonEmptyQueryValue(query.size),
    color: nonEmptyQueryValue(query.color),
    availability: availabilityFromQuery(query.availability),
    sort: sortFromQuery(query.sort),
  };
}

function stateFilters(constraints: ProductConstraints) {
  return {
    q: constraints.query ?? null,
    type: constraints.type ?? null,
    min_price: constraints.minPrice ?? null,
    max_price: constraints.maxPrice ?? null,
    size: constraints.size ?? null,
    color: constraints.color ?? null,
    availability:
      constraints.availability === undefined
        ? null
        : constraints.availability
          ? "available"
          : "unavailable",
    sort: constraints.sort ?? null,
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

  app.get("/c/:category", (request, response) => {
    const category = categoryFromValue(request.params.category);
    if (category === undefined) {
      response.status(404).type("text").send("Unknown category");
      return;
    }
    const constraints = constraintsFromQuery(category, request.query);
    response
      .type("html")
      .send(renderCategory(filterProducts(constraints), constraints));
  });

  app.post("/__test/reset", (_request, response) => {
    response.status(204).send();
  });

  app.get("/__test/state", (request, response) => {
    const requestedCategory =
      firstQueryValue(request.query.category) ?? "shoes";
    const category = categoryFromValue(requestedCategory);
    if (category === undefined) {
      response.status(400).json({ error: "unknown category" });
      return;
    }
    const constraints = constraintsFromQuery(category, request.query);
    const matchingProducts = filterProducts(constraints);
    const legacyShoeState = request.query.category === undefined;
    response.json({
      ...(legacyShoeState ? {} : { category }),
      filters: legacyShoeState
        ? {
            type: constraints.type ?? null,
            min_price: constraints.minPrice ?? null,
            max_price: constraints.maxPrice ?? null,
          }
        : stateFilters(constraints),
      product_ids: matchingProducts.map((product) => product.id),
      product_count: matchingProducts.length,
    });
  });

  return app;
}
