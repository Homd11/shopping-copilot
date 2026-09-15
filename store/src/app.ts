import express, { type Express } from "express";

export function createApp(): Express {
  const app = express();

  app.get("/", (_request, response) => {
    response.type("html").send(`<!doctype html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Shopping Copilot Store</title>
  </head>
  <body>
    <main>
      <h1>Shopping Copilot Store</h1>
      <p>مرحبًا بك في متجر الاختبار.</p>
    </main>
  </body>
</html>`);
  });

  return app;
}
