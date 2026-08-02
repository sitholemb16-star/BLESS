import request from "supertest";
import { createApp } from "../app";

describe("Health endpoint", () => {
  const app = createApp();

  it("GET /health returns 200 without authentication", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: "ok" });
  });

  it("GET /unknown-path returns 404", async () => {
    const res = await request(app).get("/does-not-exist");
    expect(res.status).toBe(404);
  });
});
