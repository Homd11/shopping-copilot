import { createApp } from "./app.js";
import { identityConfig } from "./identity-config.js";
import { openCatalogue } from "./catalogue-db.js";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const port = 4000;

const repository = openCatalogue(
  process.env.COPILOT_CATALOGUE_DB ??
    resolve(
      dirname(fileURLToPath(import.meta.url)),
      "../../work/catalogue.sqlite",
    ),
);
const catalogueRanking = process.env.CATALOGUE_RANKING ?? "lexical";
if (catalogueRanking !== "lexical" && catalogueRanking !== "hybrid")
  throw new Error("Invalid catalogue ranking");
createApp({ ...identityConfig(), repository, catalogueRanking }).listen(
  port,
  "127.0.0.1",
  () => {
    console.log(`Shopping Copilot Store listening on http://localhost:${port}`);
  },
);
