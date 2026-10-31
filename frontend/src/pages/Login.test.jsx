import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "../context/AuthContext";
import Login from "./Login";

vi.mock("../context/AuthContext", () => ({ useAuth: vi.fn() }));

const mockedUseAuth = vi.mocked(useAuth);
// The real login is async and resolves to { ok, error }.
const login = vi.fn();

// Stands in for whatever page the login redirects to.
function Destination() {
  const location = useLocation();
  return <p>arrived at {location.pathname}</p>;
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Destination />} />
      </Routes>
    </MemoryRouter>,
  );
}

// The page waits ~600ms before calling login; fake timers keep tests fast.
async function signIn(user, email = "ada@firm.com", password = "secret") {
  await user.type(screen.getByPlaceholderText("you@firm.com"), email);
  await user.type(screen.getByPlaceholderText("Enter your password"), password);
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(700);
  });
}

describe("Login page", () => {
  let user;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    login.mockReset();
    mockedUseAuth.mockReset();
    mockedUseAuth.mockReturnValue({ login });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the sign in form", () => {
    renderLogin();

    expect(
      screen.getByRole("heading", { name: "Sign in to your account" }),
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("you@firm.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter your password")).toHaveAttribute(
      "type",
      "password",
    );
    expect(
      screen.getByRole("link", { name: "Create one free" }),
    ).toBeInTheDocument();
  });

  it("logs in and goes to the dashboard", async () => {
    login.mockResolvedValue({ ok: true });
    renderLogin();

    await signIn(user);

    expect(login).toHaveBeenCalledWith("ada@firm.com", "secret");
    expect(screen.getByText("arrived at /app/dashboard")).toBeInTheDocument();
  });

  it("shows the error returned for a failed login and stays on the page", async () => {
    login.mockResolvedValue({ ok: false, error: "No active account" });
    renderLogin();

    await signIn(user);

    expect(screen.getByText("No active account")).toBeInTheDocument();
    expect(screen.queryByText(/arrived at/)).not.toBeInTheDocument();
  });

  it("disables the submit button while the request is in flight", async () => {
    login.mockResolvedValue({ ok: true });
    const { container } = renderLogin();

    await user.type(
      screen.getByPlaceholderText("you@firm.com"),
      "ada@firm.com",
    );
    await user.type(
      screen.getByPlaceholderText("Enter your password"),
      "secret",
    );
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(container.querySelector(".auth-submit")).toBeDisabled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
  });

  it("toggles password visibility", async () => {
    renderLogin();
    const field = screen.getByPlaceholderText("Enter your password");
    const toggle = within(field.parentElement).getByRole("button");

    await user.click(toggle);
    expect(field).toHaveAttribute("type", "text");

    await user.click(toggle);
    expect(field).toHaveAttribute("type", "password");
  });
});
