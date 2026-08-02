/**
 * Entry point — binds the Express app to a port.
 *
 * Do not import this file in tests; import app.ts instead.
 */

import { isApiKeyConfigured } from "./auth/index.js";
import { createApp } from "./app.js";

const PORT = process.env["PORT"] ? parseInt(process.env["PORT"], 10) : 3000;

if (!isApiKeyConfigured()) {
  process.stderr.write(
    "FATAL: API_KEY environment variable is not set. Set it before starting the server.\n",
  );
  process.exit(1);
}

const app = createApp();

app.listen(PORT, () => {
  process.stdout.write(`BLESS API listening on port ${PORT}\n`);
});
