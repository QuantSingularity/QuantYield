import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

// The real pages pull in charts and animations; routing is what is under test,
// so every page except the auth forms is replaced by a one-line stand-in.
vi.mock("./pages/Landing", () => ({ default: () => <p>landing page</p> }));
vi.mock("./pages/app/Dashboard", () => ({
  default: () => <p>dashboard page</p>,
}));
vi.mock("./pages/app/Bonds", () => ({ default: () => <p>bonds page</p> }));
vi.mock("./pages/app/Portfolios", () => ({
  default: () => <p>portfolios page</p>,
}));
vi.mock("./pages/app/Curves", () => ({ default: () => <p>curves page</p> }));
vi.mock("./pages/app/Analytics", () => ({
  default: () => <p>analytics page</p>,
}));
vi.mock("./pages/app/ML", () => ({ default: () => <p>ml page</p> }));

const SIGN_IN = { name: "Sign in to your account" };

// App owns its BrowserRouter, so navigation is driven through the real history.
function renderAt(path) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

function signIn() {
  localStorage.setItem(
    "qy_user",
    JSON.stringify({
      id: 1,
      name: "Ada Lovelace",
      email: "ada@firm.com",
      role: "Analyst",
      initials: "A",
      plan: "Pro",
    }),
  );
}

describe("App routing", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
  });

  describe("anonymous visitors", () => {
    it("see the landing page on /", async () => {
      renderAt("/");

      expect(await screen.findByText("landing page")).toBeInTheDocument();
    });

    it("can open the sign in page", async () => {
      renderAt("/login");

      expect(await screen.findByRole("heading", SIGN_IN)).toBeInTheDocument();
    });

    it("can open the registration page", async () => {
      renderAt("/register");

      expect(
        await screen.findByRole("heading", { name: "Create your account" }),
      ).toBeInTheDocument();
    });

    it.each(["/app/dashboard", "/app/bonds", "/app/ml"])(
      "are redirected from %s to the sign in page",
      async (path) => {
        renderAt(path);

        expect(await screen.findByRole("heading", SIGN_IN)).toBeInTheDocument();
        expect(window.location.pathname).toBe("/login");
      },
    );

    it("are sent to the landing page for unknown paths", async () => {
      renderAt("/does-not-exist");

      expect(await screen.findByText("landing page")).toBeInTheDocument();
      expect(window.location.pathname).toBe("/");
    });
  });

  describe("signed in users", () => {
    beforeEach(signIn);

    it.each([
      ["/app/dashboard", "dashboard page"],
      ["/app/bonds", "bonds page"],
      ["/app/portfolios", "portfolios page"],
      ["/app/curves", "curves page"],
      ["/app/analytics", "analytics page"],
      ["/app/ml", "ml page"],
    ])("can open %s", async (path, text) => {
      renderAt(path);

      expect(await screen.findByText(text)).toBeInTheDocument();
    });

    it("land on the dashboard from /app", async () => {
      renderAt("/app");

      expect(await screen.findByText("dashboard page")).toBeInTheDocument();
      expect(window.location.pathname).toBe("/app/dashboard");
    });

    it.each(["/login", "/register"])(
      "are sent from %s straight to the dashboard",
      async (path) => {
        renderAt(path);

        expect(await screen.findByText("dashboard page")).toBeInTheDocument();
        expect(screen.queryByRole("heading", SIGN_IN)).not.toBeInTheDocument();
      },
    );
  });
});
