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

  app.use(express.json());

  // Unauthenticated routes
  app.use(healthRouter);

  // All /api/* routes require a valid Bearer key
  app.use("/api", requireApiKey, provenanceRouter);

  // 404 fallback
  app.use((_req, res) => {
    res.status(404).json({ error: "Not found." });
  });

  return app;
}
