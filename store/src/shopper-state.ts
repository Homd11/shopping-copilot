import { createHash, randomBytes } from "node:crypto";
import { GuardedCart } from "./guarded-cart.js";

export const opaqueToken = (): string => randomBytes(32).toString("hex");
export const credentialDigest = (value: string): string =>
  createHash("sha256").update(value).digest("hex");
export interface ShopperBinding {
  shopper_id: string;
  generation: string;
}
export interface ShopperState {
  binding: ShopperBinding;
  cart: GuardedCart;
  csrf: string;
  loggedIn: boolean;
  lastActivity: number;
}

/** Commerce lifetime is independent of the Agent's thirty-minute task lifetime. */
export class ShopperRegistry {
  readonly generation = opaqueToken();
  readonly #states = new Map<string, ShopperState>();
  readonly #credentials = new Map<string, string>();
  readonly #clock: () => number;
  readonly #capacity: number;
  readonly #ttlMs: number;
  constructor(
    options: { clock?: () => number; capacity?: number; ttlMs?: number } = {},
  ) {
    this.#clock = options.clock ?? Date.now;
    this.#capacity = options.capacity ?? 100;
    this.#ttlMs = options.ttlMs ?? 24 * 60 * 60 * 1000;
  }
  #expire(): void {
    for (const [id, state] of this.#states)
      if (this.#clock() - state.lastActivity >= this.#ttlMs)
        this.#states.delete(id);
    for (const [digest, id] of this.#credentials)
      if (!this.#states.has(id)) this.#credentials.delete(digest);
  }
  create(): { credential: string; state: ShopperState } | undefined {
    this.#expire();
    if (this.#states.size >= this.#capacity) return undefined;
    const credential = opaqueToken();
    const state: ShopperState = {
      binding: { shopper_id: opaqueToken(), generation: this.generation },
      cart: new GuardedCart(this.#clock),
      csrf: opaqueToken(),
      loggedIn: false,
      lastActivity: this.#clock(),
    };
    this.#states.set(state.binding.shopper_id, state);
    this.#credentials.set(
      credentialDigest(credential),
      state.binding.shopper_id,
    );
    return { credential, state };
  }
  resolve(credential: string, touch = true): ShopperState | undefined {
    this.#expire();
    const id = this.#credentials.get(credentialDigest(credential));
    const state = id === undefined ? undefined : this.#states.get(id);
    if (state && touch) state.lastActivity = this.#clock();
    return state;
  }
  lookup(binding: ShopperBinding): ShopperState | undefined {
    this.#expire();
    return binding.generation === this.generation
      ? this.#states.get(binding.shopper_id)
      : undefined;
  }
}
