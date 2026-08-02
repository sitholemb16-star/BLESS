import request from "supertest";
import { createApp } from "../app";
import { promises as fs } from "fs";
import { join } from "path";

const TEST_KEY = "test-key-provenance";
const SUMS_PATH = join(process.cwd(), "apks", "SHA256SUMS.txt");
const PROV_PATH = join(process.cwd(), "apks", "provenance.json");

describe("GET /api/provenance", () => {
  let app: ReturnType<typeof createApp>;

  beforeEach(() => {
    process.env["API_KEY"] = TEST_KEY;
    app = createApp();
  });

  afterEach(() => {
    delete process.env["API_KEY"];
  });

  it("returns 404 when provenance.json does not exist", async () => {
    // provenance.json is git-ignored and won't be present in CI
    const exists = await fs.access(PROV_PATH).then(() => true).catch(() => false);
    if (exists) {
      // File exists in local dev — skip this variant
      return;
    }
    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it("returns 200 with parsed JSON when provenance.json exists", async () => {
    // Only run when the file exists (local dev with pulled APKs)
    const exists = await fs.access(PROV_PATH).then(() => true).catch(() => false);
    if (!exists) return;

    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).toBe(200);
    expect(typeof res.body).toBe("object");
  });

  it("SHA256SUMS.txt is present in the repo", async () => {
    // Verify the hashes manifest (tracked in git) is accessible
    const exists = await fs.access(SUMS_PATH).then(() => true).catch(() => false);
    expect(exists).toBe(true);
  });
});
