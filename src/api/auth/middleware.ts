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
import { createHmac, timingSafeEqual as cryptoTimingSafeEqual } from "node:crypto";

// Anchored regex: exactly "Bearer <single-token>", no extra spaces/tokens.
const BEARER_RE = /^Bearer ([!-~]+)$/;

// Stable key used only for constant-time HMAC comparison; not a secret.
const CMP_KEY = "bless-auth-hmac-compare";

/**
 * Returns true when the process has a non-empty, non-whitespace API_KEY.
 * Call once at startup to fail-closed before accepting connections.
 */
export function isApiKeyConfigured(): boolean {
  const key = process.env["API_KEY"];
  return typeof key === "string" && key.trim().length > 0 && key === key.trim();
}

/**
 * Express middleware that enforces Bearer authentication.
 *
 * Reads the expected key from `process.env.API_KEY`. Responds with 401 when
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
  const match = BEARER_RE.exec(authHeader);

  if (!match || !match[1]) {
    res
      .status(401)
      .set("WWW-Authenticate", 'Bearer realm="BLESS API"')
      .json({ error: "Missing or malformed Authorization header. Expected: Bearer <token>" });
    return;
  }

  const token = match[1];

  // HMAC both strings to equal-length digests before comparing — prevents
  // length-leaking early exits in crypto.timingSafeEqual.
  if (!hmacTimingSafeEqual(token, configured)) {
    res
      .status(401)
      .set("WWW-Authenticate", 'Bearer realm="BLESS API"')
      .json({ error: "Invalid API key." });
    return;
  }

  next();
}

/**
 * Constant-time string equality via HMAC-SHA256.
 *
 * Both inputs are reduced to fixed-length digests with the same key before
 * calling Node's crypto.timingSafeEqual, so comparison time is independent
 * of the length or content of either string.
 */
function hmacTimingSafeEqual(a: string, b: string): boolean {
  const keyBuf = Buffer.from(CMP_KEY);
  const aDigest = createHmac("sha256", keyBuf).update(a).digest();
  const bDigest = createHmac("sha256", keyBuf).update(b).digest();
  return cryptoTimingSafeEqual(aDigest, bDigest);
}
