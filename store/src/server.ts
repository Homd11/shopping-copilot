import { createApp } from "./app.js";

const port = 4000;

createApp().listen(port, "127.0.0.1", () => {
  console.log(`Shopping Copilot Store listening on http://localhost:${port}`);
});
