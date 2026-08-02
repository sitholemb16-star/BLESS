/**
 * Bearer-token authentication middleware.
 *
 * Authorization policy: only requests bearing the configured API_KEY are
 * permitted to access protected endpoints. The key is read exclusively from
 * the environment so it is never committed or logged.
 *
 * Applied to: src/api/**  (see auth.instructions.md)
 */

import type { Request, Response, NextFunction } from "express";

/**
 * Returns true when the process has a non-empty API_KEY configured.
 * Call once at startup to fail-closed before accepting connections.
 */
export function isApiKeyConfigured(): boolean {
  return typeof process.env["API_KEY"] === "string" &&
    process.env["API_KEY"].length > 0;
}

/**
 * Express middleware that enforces Bearer token authentication.
 *
 * Reads the expected key from `process.env.API_KEY`.  Responds with 401 when
 * the header is absent or the token does not match, and 503 when no API key
 * has been configured in the environment (fail-closed posture).
 */
export function requireApiKey(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const configured = process.env["API_KEY"];
  if (!configured) {
    res.status(503).json({ error: "API key not configured on this server." });
    return;
  }

  const authHeader = req.headers["authorization"] ?? "";
  const [scheme, token] = authHeader.split(" ");

  if (scheme !== "Bearer" || !token) {
    res.status(401).json({ error: "Missing or malformed Authorization header. Expected: Bearer <token>" });
    return;
  }

  // Constant-time comparison to prevent timing attacks
  if (!timingSafeEqual(token, configured)) {
    res.status(401).json({ error: "Invalid API key." });
    return;
  }

  next();
}

/** Constant-time string comparison (no early exit on first mismatch). */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
