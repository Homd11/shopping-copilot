import { createApp } from "./app.js";

const port = 4000;

createApp().listen(port, () => {
  console.log(`Shopping Copilot Store listening on http://localhost:${port}`);
});
