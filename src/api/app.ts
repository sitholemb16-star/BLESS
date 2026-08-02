/**
 * Express application factory.
 *
 * Separated from server.ts so the app can be imported directly by tests
 * without binding to a port.
 */

import express from "express";
import { requireApiKey } from "./auth/index.js";
import healthRouter from "./routes/health.js";
import provenanceRouter from "./routes/provenance.js";

export function createApp(): express.Application {
  const app = express();

  // Do not advertise the framework in responses.
  app.disable("x-powered-by");

  // Unauthenticated routes — no body parsing needed.
  app.use(healthRouter);

  // All /api/* routes require a valid Bearer token.
  // express.json() is scoped here so unauthenticated requests never reach the
  // body parser and malformed bodies cannot produce stack traces on public paths.
  app.use("/api", requireApiKey, express.json(), provenanceRouter);

  // 404 fallback
  app.use((_req, res) => {
    res.status(404).json({ error: "Not found." });
  });

  return app;
}
