import express, { type Express } from "express";
import { randomUUID } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { GuardedCart, type CartLine } from "./guarded-cart.js";

import {
  categories,
  filterProducts,
  money,
  products,
  type Category,
  type Money,
  type ProductConstraints,
  type ProductSort,
} from "./catalogue.js";
import {
  renderAccount,
  renderCart,
  renderCartContents,
  renderCategory,
  renderCheckout,
  renderHome,
  renderLogin,
  renderOrders,
  renderOrderComplete,
  renderProduct,
} from "./views.js";

const orderHistoryPath = "/account/orders";
const loginPath = `/login?next=${encodeURIComponent(orderHistoryPath)}`;

function sessionIdFromCookie(
  cookieHeader: string | undefined,
): string | undefined {
  return cookieHeader
    ?.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("fictional_session="))
    ?.slice("fictional_session=".length);
}

function requestedNextPath(value: unknown): string {
  const requestedPath = firstQueryValue(value);
  return requestedPath === orderHistoryPath ? requestedPath : orderHistoryPath;
}

function firstQueryValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function nonEmptyQueryValue(value: unknown): string | undefined {
  const text = firstQueryValue(value)?.trim();
  return text === undefined || text === "" ? undefined : text;
}

function priceFromQuery(value: unknown): Money | undefined {
  const text = nonEmptyQueryValue(value);
  if (text === undefined) return undefined;
  try {
    return money(text);
  } catch {
    return undefined;
  }
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

export function createApp(options: { clock?: () => number } = {}): Express {
  const app = express();
  const fictionalSessions = new Set<string>();
  const cart = new GuardedCart(options.clock);
  const sourceDirectory = dirname(fileURLToPath(import.meta.url));
  app.use(express.urlencoded({ extended: false }));
  app.use(express.json());
  app.use("/assets", express.static(resolve(sourceDirectory, "../public")));
  app.use(
    "/bridge",
    express.static(resolve(sourceDirectory, "../../bridge/dist")),
  );

  app.get("/", (_request, response) => {
    response.type("html").send(renderHome());
  });

  app.get("/cart", (_request, response) => {
    response.type("html").send(renderCart(cart.lines, cart.revision));
  });

  app.post("/cart/clear", (request, response) => {
    if (
      !cart.consume(
        request.body?.copilot_confirmation,
        "clear_cart",
        request.body?.cart_revision,
      )
    ) {
      response
        .status(403)
        .type("html")
        .send(
          renderCart(
            cart.lines,
            cart.revision,
            "انتهى التأكيد أو تغيرت السلة. لم يتم الإفراغ.",
          ),
        );
      return;
    }
    cart.clear();
    response.redirect(303, "/cart");
  });

  app.post("/cart/items", (request, response) => {
    const productId = request.body?.product_id;
    const product =
      typeof productId === "string"
        ? products.find((item) => item.id === productId)
        : undefined;
    if (product === undefined) {
      response.status(404).json({ error: "unknown_product" });
      return;
    }
    if (!product.available) {
      response.status(409).json({ error: "product_unavailable" });
      return;
    }
    if (!cart.edit("add", request.body ?? {})) {
      response.status(409).json({ error: "invalid_or_stale_cart_edit" });
      return;
    }
    response.json(cartView());
  });

  function cartView() {
    return {
      ...cart.state,
      undo: cart.undo,
      count: cart.lines.reduce((sum, line) => sum + line.quantity, 0),
      html: renderCartContents(cart.lines, cart.revision),
    };
  }
  app.get("/cart/state", (_request, response) => {
    response.set("Cache-Control", "no-store").json(cartView());
  });
  for (const kind of ["quantity", "remove", "undo"] as const) {
    app.post(`/cart/${kind}`, (request, response) => {
      if (!cart.edit(kind, request.body ?? {})) {
        response.status(409).json({ error: "invalid_or_stale_cart_edit" });
        return;
      }
      response.json(cartView());
    });
  }

  app.get("/checkout", (_request, response) => {
    response.type("html").send(renderCheckout(cart.lines, cart.revision));
  });

  app.post("/checkout/submit", (request, response) => {
    if (
      !cart.consume(
        request.body?.copilot_confirmation,
        "submit_checkout",
        request.body?.cart_revision,
      )
    ) {
      response
        .status(403)
        .type("html")
        .send(
          renderCheckout(
            cart.lines,
            cart.revision,
            "انتهى التأكيد أو تغيرت السلة. لم يتم تسجيل طلب.",
          ),
        );
      return;
    }
    if (
      request.body?.card_number !== "0000 0000 0000 0000" ||
      request.body?.card_expiry !== "01/30" ||
      request.body?.card_security_code !== "000"
    ) {
      response
        .status(400)
        .type("html")
        .send(
          renderCheckout(
            cart.lines,
            cart.revision,
            "استخدم بيانات الدفع الخيالية المعروضة فقط. لم يتم تسجيل طلب.",
          ),
        );
      return;
    }
    response.redirect(303, `/order/complete/${cart.submitOrder()}`);
  });

  app.get("/order/complete/:orderId", (request, response) => {
    if (
      !cart.state.orders.some((order) => order.id === request.params.orderId)
    ) {
      response.status(404).type("text").send("Unknown fictional order");
      return;
    }
    response.type("html").send(renderOrderComplete(request.params.orderId));
  });

  app.post("/__copilot/confirmations", (request, response) => {
    if (!cart.register(request.body)) {
      response.status(409).json({ error: "invalid_or_stale_confirmation" });
      return;
    }
    response.status(201).json({ status: "registered" });
  });

  app.get("/account", (_request, response) => {
    response.type("html").send(renderAccount());
  });

  app.get("/login", (request, response) => {
    response
      .type("html")
      .send(renderLogin(requestedNextPath(request.query.next)));
  });

  app.post("/login", (request, response) => {
    const body = request.body ?? {};
    const username = body.username;
    const password = body.password;
    if (
      typeof username !== "string" ||
      username.trim() === "" ||
      typeof password !== "string" ||
      password === ""
    ) {
      response.status(400).type("html").send(renderLogin(orderHistoryPath));
      return;
    }

    const sessionId = randomUUID();
    fictionalSessions.add(sessionId);
    response.cookie("fictional_session", sessionId, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
    });
    response.redirect(303, requestedNextPath(body.next));
  });

  app.get(orderHistoryPath, (request, response) => {
    const sessionId = sessionIdFromCookie(request.headers.cookie);
    if (sessionId === undefined || !fictionalSessions.has(sessionId)) {
      response.redirect(302, loginPath);
      return;
    }
    response.type("html").send(renderOrders());
  });

  app.get("/__catalogue/v1/products", (_request, response) => {
    response.set("Cache-Control", "no-store").json({
      v: 1,
      currency: "EGP",
      products: products.map((product) => ({
        id: product.id,
        category: product.category,
        name_ar: product.nameAr,
        name_en: product.nameEn,
        product_type: product.type,
        price: product.price,
        sizes: product.sizes,
        colors: product.colors,
        available: product.available,
        added_at: product.addedAt,
        features: product.features,
        suitable_for: product.suitableFor,
        wear_position: product.wearPosition,
      })),
    });
  });

  app.get("/p/:productId", (request, response) => {
    const product = products.find(
      (item) => item.id === request.params.productId,
    );
    if (product === undefined) {
      response.status(404).type("text").send("Unknown product");
      return;
    }
    response.type("html").send(renderProduct(product));
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
    cart.reset();
    response.status(204).send();
  });

  app.post("/__test/cart", (request, response) => {
    if (!cart.seed(request.body?.lines as CartLine[])) {
      response.status(400).json({ error: "invalid_cart_seed" });
      return;
    }
    response.status(204).send();
  });

  app.get("/__test/cart-state", (_request, response) => {
    response.set("Cache-Control", "no-store").json(cart.state);
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
