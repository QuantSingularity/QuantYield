import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import api, { ApiError } from "./apiClient";

function mockFetch(status, body) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json:
      body === undefined
        ? () => Promise.reject(new Error("no body"))
        : () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ApiError", () => {
  it("prefers the detail field for its message", () => {
    const err = new ApiError(400, { detail: "Bad input", message: "ignored" });

    expect(err.message).toBe("Bad input");
    expect(err.status).toBe(400);
    expect(err.data).toEqual({ detail: "Bad input", message: "ignored" });
  });

  it("falls back to the message field, then to the HTTP status", () => {
    expect(new ApiError(400, { message: "Oops" }).message).toBe("Oops");
    expect(new ApiError(502, null).message).toBe("HTTP 502");
  });

  it("is an Error instance", () => {
    expect(new ApiError(500, null)).toBeInstanceOf(Error);
  });
});

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("sends JSON requests to the versioned API", async () => {
    const fetchMock = mockFetch(200, { ok: true });

    await api.get("/bonds/");

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/bonds/", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      body: undefined,
    });
  });

  it("returns the parsed JSON body", async () => {
    mockFetch(200, { id: 1, name: "UST 10Y" });

    await expect(api.get("/bonds/1/")).resolves.toEqual({
      id: 1,
      name: "UST 10Y",
    });
  });

  it("serialises the body for write requests", async () => {
    const fetchMock = mockFetch(201, { id: 2 });

    await api.post("/bonds/", { coupon_rate: 0.05 });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify({ coupon_rate: 0.05 }));
  });

  it.each([
    ["put", "PUT"],
    ["patch", "PATCH"],
  ])("maps api.%s to the %s method", async (verb, method) => {
    const fetchMock = mockFetch(200, {});

    await api[verb]("/bonds/1/", { name: "x" });

    expect(fetchMock.mock.calls[0][1].method).toBe(method);
  });

  it("maps api.delete to the DELETE method without a body", async () => {
    const fetchMock = mockFetch(200, {});

    await api.delete("/bonds/1/");

    const [, options] = fetchMock.mock.calls[0];
    expect(options.method).toBe("DELETE");
    expect(options.body).toBeUndefined();
  });

  it("attaches the stored access token", async () => {
    localStorage.setItem(
      "qy_tokens",
      JSON.stringify({ access: "abc123", refresh: "r" }),
    );
    const fetchMock = mockFetch(200, {});

    await api.get("/auth/me/");

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe(
      "Bearer abc123",
    );
  });

  it("sends no Authorization header when there is no token", async () => {
    const fetchMock = mockFetch(200, {});

    await api.get("/health/");

    expect(fetchMock.mock.calls[0][1].headers).not.toHaveProperty(
      "Authorization",
    );
  });

  it("ignores a corrupted token entry", async () => {
    localStorage.setItem("qy_tokens", "{not json");
    const fetchMock = mockFetch(200, {});

    await api.get("/health/");

    expect(fetchMock.mock.calls[0][1].headers).not.toHaveProperty(
      "Authorization",
    );
  });

  it("throws an ApiError carrying the status and body on failure", async () => {
    mockFetch(401, { detail: "Invalid token" });

    const error = await api.get("/auth/me/").catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(401);
    expect(error.message).toBe("Invalid token");
    expect(error.data).toEqual({ detail: "Invalid token" });
  });

  it("copes with a response that has no JSON body", async () => {
    mockFetch(500, undefined);

    const error = await api.get("/boom/").catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(500);
    expect(error.data).toBeNull();
    expect(error.message).toBe("HTTP 500");
  });
});
