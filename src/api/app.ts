/**
 * Express application factory.
 *
 * Separated from server.ts so the app can be imported directly by tests
 * without binding to a port.
 */

import express from "express";
import { requireApiKey } from "./auth/index";
import healthRouter from "./routes/health";
import provenanceRouter from "./routes/provenance";

export function createApp(): express.Application {
  const app = express();

  // Do not advertise the framework in responses.
  app.disable("x-powered-by");

  // Unauthenticated routes — no body parsing needed.
  app.use(healthRouter);

  // All /api/* routes require a valid API key (see auth/middleware.ts).
  // express.json() is scoped here so unauthenticated requests never reach the
  // body parser and malformed bodies cannot produce stack traces on public paths.
  app.use("/api", requireApiKey, express.json(), provenanceRouter);

  // JSON body-parse error handler — must declare all four parameters so Express
  // recognises it as an error-handling middleware (not a regular route).
  app.use(
    (
      err: unknown,
      _req: express.Request,
      res: express.Response,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      _next: express.NextFunction,
    ): void => {
      if (typeof err === "object" && err !== null && "type" in err) {
        const bodyError = err as { type: string; status?: number; statusCode?: number };
        if (bodyError.type === "entity.parse.failed") {
          res.status(400).json({ error: "Invalid JSON in request body." });
          return;
        }
        if (bodyError.type === "entity.too.large") {
          res.status(bodyError.status ?? bodyError.statusCode ?? 413).json({
            error: "Request body too large.",
          });
          return;
        }
      }
      if (
        typeof err === "object" &&
        err !== null &&
        "status" in err &&
        typeof (err as { status?: unknown }).status === "number"
      ) {
        const status = (err as { status: number }).status;
        if (status >= 400 && status < 500) {
          res.status(status).json({ error: "Request rejected." });
          return;
        }
      }
      if (
        typeof err === "object" &&
        err !== null &&
        "statusCode" in err &&
        typeof (err as { statusCode?: unknown }).statusCode === "number"
      ) {
        const status = (err as { statusCode: number }).statusCode;
        if (status >= 400 && status < 500) {
          res.status(status).json({ error: "Request rejected." });
          return;
        }
      }
      res.status(500).json({ error: "Internal server error." });
    },
  );

  // 404 fallback
  app.use((_req, res) => {
    res.status(404).json({ error: "Not found." });
  });

  return app;
}
