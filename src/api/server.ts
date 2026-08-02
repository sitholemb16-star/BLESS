/**
 * Entry point — binds the Express app to a port.
 *
 * Do not import this file in tests; import app.ts instead.
 */

import { isApiKeyConfigured } from "./auth/index.js";
import { createApp } from "./app.js";

// Strict integer port validation: must be a bare integer in [1, 65535].
const rawPort = process.env["PORT"];
let PORT = 3000;
if (rawPort !== undefined) {
  if (!/^\d+$/.test(rawPort)) {
    process.stderr.write(`FATAL: PORT "${rawPort}" is not a valid integer.\n`);
    process.exit(1);
  }
  PORT = parseInt(rawPort, 10);
  if (PORT < 1 || PORT > 65535) {
    process.stderr.write(
      `FATAL: PORT ${PORT} is outside the valid range 1–65535.\n`,
    );
    process.exit(1);
  }
}

if (!isApiKeyConfigured()) {
  process.stderr.write(
    "FATAL: API_KEY environment variable is not set or contains whitespace. " +
      "Set it to a non-empty trimmed value before starting the server.\n",
  );
  process.exit(1);
}

const app = createApp();

const server = app.listen(PORT, () => {
  // Read the actual bound address — handles PORT=0 (OS-assigned) correctly.
  const addr = server.address();
  const boundPort = typeof addr === "object" && addr !== null ? addr.port : PORT;
  process.stdout.write(`BLESS API listening on port ${boundPort}\n`);
});
