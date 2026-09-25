import { randomUUID } from "node:crypto";

import { products } from "./catalogue.js";

export type MutationKind = "clear_cart" | "submit_checkout";
export interface CartLine {
  product_id: string;
  quantity: number;
  size?: string;
  color?: string;
}

export function lineKey(
  line: Pick<CartLine, "product_id" | "size" | "color">,
): string {
  return [line.product_id, line.size ?? "", line.color ?? ""].join("~");
}

interface UndoRecord {
  id: string;
  before: CartLine[];
  expiresAt: number;
  kind: string;
  line: string;
  revision: number;
}

interface Confirmation {
  kind: MutationKind;
  cartRevision: number;
  issuedAt: number;
}

export class GuardedCart {
  #lines: CartLine[] = [];
  #revision = 0;
  #confirmations = new Map<string, Confirmation>();
  #orders: Array<{ id: string; lines: CartLine[] }> = [];
  #undo: UndoRecord | null = null;
  #operations = new Set<string>();
  readonly #clock: () => number;

  constructor(clock: () => number = Date.now) {
    this.#clock = clock;
  }

  get revision(): number {
    return this.#revision;
  }

  get lines(): CartLine[] {
    return this.#lines.map((line) => ({ ...line }));
  }

  get state() {
    return {
      revision: this.#revision,
      lines: this.lines,
      orders: this.#orders.map((order) => ({
        id: order.id,
        lines: order.lines.map((line) => ({ ...line })),
      })),
    };
  }

  get undo() {
    const record = this.#undo;
    const before = record?.before.find((line) => lineKey(line) === record.line);
    const after = this.#lines.find((line) => lineKey(line) === record?.line);
    const item = after ?? before;
    const product = products.find((product) => product.id === item?.product_id);
    return record !== null &&
      record.expiresAt > this.#clock() &&
      record.revision === this.#revision
      ? {
          id: record.id,
          remaining_ms: record.expiresAt - this.#clock(),
          kind: record.kind,
          description: `${product?.nameAr ?? item?.product_id} · ${item?.size ?? "—"} / ${item?.color ?? "—"}: ${before?.quantity ?? 0} → ${after?.quantity ?? 0}`,
          description_en: `${product?.nameEn ?? item?.product_id} · ${item?.size ?? "—"} / ${item?.color ?? "—"}: ${before?.quantity ?? 0} → ${after?.quantity ?? 0}`,
        }
      : null;
  }

  edit(
    kind: "add" | "quantity" | "remove" | "undo",
    input: Record<string, unknown>,
  ): boolean {
    const operation = input.operation_id;
    if (
      typeof operation !== "string" ||
      operation.length < 1 ||
      operation.length > 100 ||
      this.#operations.has(operation) ||
      input.revision !== this.#revision
    )
      return false;
    if (kind === "undo") {
      const undo = this.#undo;
      if (undo === null || this.undo === null || input.undo_id !== undo.id)
        return false;
      this.#lines = undo.before.map((line) => ({ ...line }));
      this.#undo = null;
    } else {
      const product = products.find((item) => item.id === input.product_id);
      if (!product || !product.available) return false;
      const size = typeof input.size === "string" ? input.size : undefined;
      const color = typeof input.color === "string" ? input.color : undefined;
      if (
        kind === "add" &&
        (!product.sizes.includes(size ?? "") ||
          !product.colors.includes(color ?? ""))
      )
        return false;
      const key = lineKey({ product_id: product.id, size, color });
      const index = this.#lines.findIndex((line) => lineKey(line) === key);
      if (kind !== "add" && index === -1) return false;
      const quantity = input.quantity;
      if (
        kind !== "remove" &&
        (typeof quantity !== "number" ||
          !Number.isSafeInteger(quantity) ||
          quantity < 1 ||
          quantity > 99)
      )
        return false;
      const nextQuantity =
        kind === "add"
          ? (this.#lines[index]?.quantity ?? 0) + Number(quantity)
          : Number(quantity);
      if (kind !== "remove" && nextQuantity > 99) return false;
      const previous = this.#undo;
      const coalesce =
        kind === "quantity" &&
        this.undo !== null &&
        previous?.kind === kind &&
        previous.line === key;
      this.#undo = coalesce
        ? { ...previous!, revision: this.#revision + 1 }
        : {
            id: randomUUID(),
            before: this.lines,
            expiresAt: this.#clock() + 10000,
            kind,
            line: key,
            revision: this.#revision + 1,
          };
      if (kind === "remove") this.#lines.splice(index, 1);
      else if (index !== -1) this.#lines[index].quantity = nextQuantity;
      else
        this.#lines.push({
          product_id: product.id,
          size,
          color,
          quantity: nextQuantity,
        });
    }
    this.#revision++;
    this.#operations.add(operation);
    this.#confirmations.clear();
    return true;
  }

  seed(lines: CartLine[]): boolean {
    if (
      !Array.isArray(lines) ||
      lines.some(
        (line) =>
          typeof line.product_id !== "string" ||
          !Number.isSafeInteger(line.quantity) ||
          line.quantity < 1 ||
          line.quantity > 99 ||
          !products.some(
            (product) => product.id === line.product_id && product.available,
          ),
      )
    )
      return false;
    this.#lines = lines.map((line) => ({ ...line }));
    this.#revision++;
    this.#undo = null;
    return true;
  }

  register(input: {
    token: string;
    task_id: string;
    kind: MutationKind;
    cart_revision: number;
  }): boolean {
    if (
      !/^confirmation-[0-9a-f]{32}$/.test(input.token) ||
      !/^task-[a-zA-Z0-9-]+$/.test(input.task_id) ||
      !["clear_cart", "submit_checkout"].includes(input.kind) ||
      input.cart_revision !== this.#revision ||
      this.#lines.length === 0 ||
      this.#confirmations.has(input.token)
    )
      return false;
    this.#confirmations.set(input.token, {
      kind: input.kind,
      cartRevision: input.cart_revision,
      issuedAt: this.#clock(),
    });
    return true;
  }

  consume(token: unknown, kind: MutationKind, revision: unknown): boolean {
    if (typeof token !== "string") return false;
    const confirmation = this.#confirmations.get(token);
    if (confirmation === undefined) return false;
    this.#confirmations.delete(token);
    return (
      confirmation.kind === kind &&
      confirmation.cartRevision === this.#revision &&
      String(confirmation.cartRevision) === revision &&
      this.#clock() - confirmation.issuedAt < 60_000 &&
      this.#lines.length > 0
    );
  }

  clear(): void {
    this.#lines = [];
    this.#revision++;
    this.#undo = null;
  }

  submitOrder(): string {
    const id = randomUUID();
    this.#orders.push({ id, lines: this.lines });
    this.clear();
    return id;
  }

  reset(): void {
    this.#lines = [];
    this.#revision = 0;
    this.#confirmations.clear();
    this.#orders = [];
    this.#undo = null;
    this.#operations.clear();
  }
}
