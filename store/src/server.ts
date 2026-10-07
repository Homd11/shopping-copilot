import { createApp } from "./app.js";
import { identityConfig } from "./identity-config.js";

const port = 4000;

createApp(identityConfig()).listen(port, "127.0.0.1", () => {
  console.log(`Shopping Copilot Store listening on http://localhost:${port}`);
});
