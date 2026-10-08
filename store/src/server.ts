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
createApp({ ...identityConfig(), repository }).listen(port, "127.0.0.1", () => {
  console.log(`Shopping Copilot Store listening on http://localhost:${port}`);
});
