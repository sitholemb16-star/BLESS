import request from "supertest";
import { createApp } from "../app";
import { promises as fs } from "fs";
import { join } from "path";
import os from "os";

const TEST_KEY = "test-key-provenance";
const SUMS_PATH = join(process.cwd(), "apks", "SHA256SUMS.txt");

describe("GET /api/provenance", () => {
  let app: ReturnType<typeof createApp>;
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(join(os.tmpdir(), "bless-prov-test-"));
    process.env["API_KEY"] = TEST_KEY;
    app = createApp();
  });

  afterEach(async () => {
    delete process.env["API_KEY"];
    delete process.env["PROVENANCE_PATH"];
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it("returns 404 when provenance.json does not exist", async () => {
    // Point to a path we know doesn't exist.
    process.env["PROVENANCE_PATH"] = join(tmpDir, "no-such-file.json");
    app = createApp();

    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it("returns 200 with parsed JSON when provenance.json exists", async () => {
    const provData = { generated_at: "2024-01-01T00:00:00Z", packages: [{ package_name: "com.example.app" }], apks: [] };
    const provFile = join(tmpDir, "provenance.json");
    await fs.writeFile(provFile, JSON.stringify(provData));
    process.env["PROVENANCE_PATH"] = provFile;
    app = createApp();

    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ generated_at: "2024-01-01T00:00:00Z" });
  });

  it("SHA256SUMS.txt is present in the repo", async () => {
    const exists = await fs.access(SUMS_PATH).then(() => true).catch(() => false);
    expect(exists).toBe(true);
  });
});
