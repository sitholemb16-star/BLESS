import request from "supertest";
import { createApp } from "../app";

const TEST_KEY = "test-secret-key-for-unit-tests";

describe("Authentication middleware", () => {
  let app: ReturnType<typeof createApp>;

  beforeEach(() => {
    process.env["API_KEY"] = TEST_KEY;
    app = createApp();
  });

  afterEach(() => {
    delete process.env["API_KEY"];
  });

  it("returns 401 when Authorization header is absent", async () => {
    const res = await request(app).get("/api/provenance");
    expect(res.status).toBe(401);
    expect(res.body).toHaveProperty("error");
  });

  it("returns 401 when scheme is not Bearer", async () => {
    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Basic ${TEST_KEY}`);
    expect(res.status).toBe(401);
  });

  it("returns 401 when token is wrong", async () => {
    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", "Bearer wrong-key");
    expect(res.status).toBe(401);
  });

  it("returns 503 when API_KEY is not configured", async () => {
    delete process.env["API_KEY"];
    app = createApp();
    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).toBe(503);
    expect(res.body.error).toMatch(/not configured/i);
  });

  it("passes authentication with valid Bearer token", async () => {
    // Should get past auth (404 or 200 from the route itself, not 401)
    const res = await request(app)
      .get("/api/provenance")
      .set("Authorization", `Bearer ${TEST_KEY}`);
    expect(res.status).not.toBe(401);
    expect(res.status).not.toBe(503);
  });
});
