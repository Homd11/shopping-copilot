import { afterEach, expect, it } from "vitest";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { products } from "../src/catalogue.js";
import { importCatalogue, openCatalogue } from "../src/catalogue-db.js";

const folders: string[] = [];
afterEach(() => {
  for (const folder of folders.splice(0))
    rmSync(folder, { recursive: true, force: true });
});
function path() {
  const folder = mkdtempSync(join(tmpdir(), "copilot-catalogue-"));
  folders.push(folder);
  return join(folder, "catalogue.sqlite");
}
it("imports and reopens exact seed facts without reseeding an existing database", () => {
  const file = path();
  importCatalogue(file, products);
  let repo = openCatalogue(file);
  expect(repo.all()).toEqual(products);
  const revision = repo.revision();
  repo.close();
  importCatalogue(file, products);
  repo = openCatalogue(file);
  expect(repo.revision()).toBe(revision);
  repo.close();
  importCatalogue(
    file,
    products.map((p, i) =>
      i ? p : { ...p, price: { amount: "123.45", currency: "EGP" } },
    ),
  );
  repo = openCatalogue(file);
  expect(repo.get(products[0].id)?.price.amount).toBe("123.45");
  expect(repo.revision()).toBe(revision + 1);
  repo.close();
});
it("rejects missing databases and invalid imports without losing existing facts", () => {
  const file = path();
  expect(() => openCatalogue(file)).toThrow();
  importCatalogue(file, products);
  expect(() => importCatalogue(file, [...products, products[0]])).toThrow();
  expect(() =>
    importCatalogue(
      file,
      products.map((p, i) =>
        i ? p : { ...p, price: { amount: "-1", currency: "EGP" } },
      ),
    ),
  ).toThrow();
  const repo = openCatalogue(file);
  expect(repo.all()).toEqual(products);
  expect(repo.revision()).toBe(1);
  repo.close();
});
it("retains unknown absence and rejects contradictory explicit negative facts", () => {
  const file = path();
  importCatalogue(file, products);
  let repo = openCatalogue(file);
  expect(repo.evidence(products[0].id)?.absent_features).toEqual([]);
  repo.close();
  expect(() =>
    importCatalogue(
      file,
      products.map((p, i) =>
        i
          ? p
          : {
              ...p,
              features: ["leather"],
              absent_features: ["leather"],
            },
      ),
    ),
  ).toThrow();
  repo = openCatalogue(file);
  expect(repo.revision()).toBe(1);
  repo.close();
});
