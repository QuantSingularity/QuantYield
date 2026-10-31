import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import api, { ApiError } from "@/lib/apiClient";
import { AuthProvider, useAuth } from "./AuthContext";

// Keep the real ApiError (the provider checks instanceof) but fake the HTTP calls.
vi.mock("@/lib/apiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { get: vi.fn(), post: vi.fn() } };
});

const TOKENS = { access: "access-token", refresh: "refresh-token" };

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

async function renderAuth() {
  const hook = renderHook(() => useAuth(), { wrapper });
  await waitFor(() => expect(hook.result.current.loading).toBe(false));
  return hook;
}

// Runs an auth action inside act() and returns what it resolved with.
async function run(action) {
  let value;
  await act(async () => {
    value = await action();
  });
  return value;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    api.get.mockReset();
    api.post.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("session", () => {
    it("starts logged out when nothing is stored", async () => {
      const { result } = await renderAuth();

      expect(result.current.user).toBeNull();
    });

    it("restores a stored user", async () => {
      localStorage.setItem(
        "qy_user",
        JSON.stringify({ id: 1, name: "Ada Lovelace" }),
      );

      const { result } = await renderAuth();

      expect(result.current.user).toEqual({ id: 1, name: "Ada Lovelace" });
    });

    it("ignores a corrupted stored user", async () => {
      localStorage.setItem("qy_user", "{not json");

      const { result } = await renderAuth();

      expect(result.current.user).toBeNull();
    });

    it("clears the stored tokens and user on logout", async () => {
      localStorage.setItem("qy_tokens", JSON.stringify(TOKENS));
      localStorage.setItem("qy_user", JSON.stringify({ id: 1 }));
      const { result } = await renderAuth();

      act(() => result.current.logout());

      expect(result.current.user).toBeNull();
      expect(localStorage.getItem("qy_tokens")).toBeNull();
      expect(localStorage.getItem("qy_user")).toBeNull();
    });
  });

  describe("login", () => {
    it("requires an email and a password", async () => {
      const { result } = await renderAuth();

      await expect(
        run(() => result.current.login("", "secret")),
      ).resolves.toEqual({
        ok: false,
        error: "Email and password required",
      });
      expect(api.post).not.toHaveBeenCalled();
    });

    it("stores the tokens and a normalised user profile", async () => {
      api.post.mockResolvedValueOnce(TOKENS);
      api.get.mockResolvedValueOnce({
        id: 7,
        first_name: "Ada",
        last_name: "Lovelace",
        email: "ada@firm.com",
        profile: { role: "Quant Analyst", plan: "Starter" },
      });
      const { result } = await renderAuth();

      const outcome = await run(() =>
        result.current.login("ada@firm.com", "secret"),
      );

      expect(outcome).toEqual({ ok: true });
      expect(api.post).toHaveBeenCalledWith("/auth/token/", {
        email: "ada@firm.com",
        password: "secret",
      });
      expect(api.get).toHaveBeenCalledWith("/auth/me/");
      expect(JSON.parse(localStorage.getItem("qy_tokens"))).toEqual(TOKENS);
      expect(result.current.user).toEqual({
        id: 7,
        name: "Ada Lovelace",
        email: "ada@firm.com",
        role: "Quant Analyst",
        initials: "A",
        plan: "Starter",
      });
      expect(JSON.parse(localStorage.getItem("qy_user"))).toEqual(
        result.current.user,
      );
    });

    it("falls back to the username, default role and plan", async () => {
      api.post.mockResolvedValueOnce(TOKENS);
      api.get.mockResolvedValueOnce({
        pk: 3,
        username: "bob",
        email: "bob@firm.com",
      });
      const { result } = await renderAuth();

      await run(() => result.current.login("bob@firm.com", "secret"));

      expect(result.current.user).toEqual({
        id: 3,
        name: "bob",
        email: "bob@firm.com",
        role: "Analyst",
        initials: "B",
        plan: "Pro",
      });
    });

    it.each([
      [
        "the detail message",
        { detail: "No active account" },
        "No active account",
      ],
      [
        "the first non-field error",
        { non_field_errors: ["Wrong password"] },
        "Wrong password",
      ],
      ["a generic message", {}, "Login failed"],
    ])("reports %s from the server", async (_label, body, expected) => {
      api.post.mockRejectedValueOnce(new ApiError(401, body));
      const { result } = await renderAuth();

      const outcome = await run(() => result.current.login("a@b.com", "wrong"));

      expect(outcome).toEqual({ ok: false, error: expected });
      expect(result.current.user).toBeNull();
    });

    it("reports a network error for non-API failures", async () => {
      api.post.mockRejectedValueOnce(new TypeError("Failed to fetch"));
      const { result } = await renderAuth();

      const outcome = await run(() =>
        result.current.login("a@b.com", "secret"),
      );

      expect(outcome).toEqual({
        ok: false,
        error: "Network error - check your connection",
      });
    });

    it("discards the tokens when the profile request fails", async () => {
      api.post.mockResolvedValueOnce(TOKENS);
      api.get.mockRejectedValueOnce(new ApiError(500, {}));
      const { result } = await renderAuth();

      const outcome = await run(() =>
        result.current.login("a@b.com", "secret"),
      );

      expect(outcome.ok).toBe(false);
      expect(localStorage.getItem("qy_tokens")).toBeNull();
    });
  });

  describe("register", () => {
    const details = {
      name: "Jane Q Smith",
      email: "jane@firm.com",
      password: "Passw0rd!",
    };

    it("requires name, email and password", async () => {
      const { result } = await renderAuth();

      const outcome = await run(() =>
        result.current.register({ ...details, name: "" }),
      );

      expect(outcome).toEqual({ ok: false, error: "All fields required" });
      expect(api.post).not.toHaveBeenCalled();
    });

    it("rejects passwords shorter than 8 characters", async () => {
      const { result } = await renderAuth();

      const outcome = await run(() =>
        result.current.register({ ...details, password: "short" }),
      );

      expect(outcome).toEqual({
        ok: false,
        error: "Password must be at least 8 characters",
      });
    });

    it("creates the account, then logs the user in", async () => {
      api.post.mockResolvedValueOnce({}).mockResolvedValueOnce(TOKENS);
      api.get.mockResolvedValueOnce({
        id: 9,
        first_name: "Jane",
        last_name: "Q Smith",
        email: "jane@firm.com",
      });
      const { result } = await renderAuth();

      const outcome = await run(() => result.current.register(details));

      expect(outcome).toEqual({ ok: true });
      expect(api.post).toHaveBeenNthCalledWith(1, "/auth/register/", {
        username: "jane@firm.com",
        email: "jane@firm.com",
        password: "Passw0rd!",
        first_name: "Jane",
        last_name: "Q Smith",
      });
      expect(api.post).toHaveBeenNthCalledWith(2, "/auth/token/", {
        email: "jane@firm.com",
        password: "Passw0rd!",
      });
      expect(result.current.user.name).toBe("Jane Q Smith");
    });

    it.each([
      [
        "the email error",
        { email: ["Already registered"] },
        "Already registered",
      ],
      ["the password error", { password: ["Too common"] }, "Too common"],
      ["a generic message", {}, "Registration failed"],
    ])("reports %s from the server", async (_label, body, expected) => {
      api.post.mockRejectedValueOnce(new ApiError(400, body));
      const { result } = await renderAuth();

      const outcome = await run(() => result.current.register(details));

      expect(outcome).toEqual({ ok: false, error: expected });
    });

    it("reports a network error for non-API failures", async () => {
      api.post.mockRejectedValueOnce(new TypeError("Failed to fetch"));
      const { result } = await renderAuth();

      const outcome = await run(() => result.current.register(details));

      expect(outcome.error).toBe("Network error - check your connection");
    });
  });

  describe("useAuth", () => {
    it("throws outside an AuthProvider", () => {
      // React logs the thrown error; keep the test output clean.
      vi.spyOn(console, "error").mockImplementation(() => {});

      expect(() => renderHook(() => useAuth())).toThrow(
        "useAuth must be used within AuthProvider",
      );
    });
  });
});
