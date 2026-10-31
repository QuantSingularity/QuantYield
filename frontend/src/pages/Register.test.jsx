import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "../context/AuthContext";
import Register from "./Register";

vi.mock("../context/AuthContext", () => ({ useAuth: vi.fn() }));

const mockedUseAuth = vi.mocked(useAuth);
// The real register is async and resolves to { ok, error }.
const register = vi.fn();

function Destination() {
  const location = useLocation();
  return <p>arrived at {location.pathname}</p>;
}

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={["/register"]}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Destination />} />
      </Routes>
    </MemoryRouter>,
  );
}

const submitButton = () =>
  screen.getByRole("button", { name: /Create Account/ });

async function fillForm(
  user,
  { password = "Passw0rd!", confirm = password } = {},
) {
  await user.type(screen.getByPlaceholderText("Jane Smith"), "Jane Smith");
  await user.type(
    screen.getByPlaceholderText("jane@firm.com"),
    "jane@firm.com",
  );
  await user.type(screen.getByPlaceholderText("Min. 8 characters"), password);
  await user.type(screen.getByPlaceholderText("Re-enter password"), confirm);
}

// The page waits ~700ms before registering; fake timers keep tests fast.
async function submit(user) {
  await user.click(submitButton());
  await act(async () => {
    await vi.advanceTimersByTimeAsync(800);
  });
}

describe("Register page", () => {
  let user;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    register.mockReset();
    mockedUseAuth.mockReset();
    mockedUseAuth.mockReturnValue({ register });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the sign up form with the free trial selected", () => {
    renderRegister();

    expect(
      screen.getByRole("heading", { name: "Create your account" }),
    ).toBeInTheDocument();
    expect(submitButton()).toHaveTextContent("Create Account · Free Trial");
  });

  it("rejects mismatched passwords without calling the API", async () => {
    renderRegister();
    await fillForm(user, { password: "Passw0rd!", confirm: "Different1!" });

    await submit(user);

    expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it("rejects a weak password without calling the API", async () => {
    renderRegister();
    await fillForm(user, { password: "abc" });

    await submit(user);

    expect(
      screen.getByText("Please use a stronger password"),
    ).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it.each([
    ["abc", ""],
    ["abcdefgh", "Weak"],
    ["Abcdefgh", "Fair"],
    ["Abcdefg1", "Good"],
    ["Abcdef1!", "Strong"],
  ])("rates the password %s as %s", async (password, label) => {
    renderRegister();

    await user.type(screen.getByPlaceholderText("Min. 8 characters"), password);

    if (label) expect(screen.getByText(label)).toBeInTheDocument();
    else {
      for (const text of ["Weak", "Fair", "Good", "Strong"]) {
        expect(screen.queryByText(text)).not.toBeInTheDocument();
      }
    }
  });

  it("registers and goes to the dashboard", async () => {
    register.mockResolvedValue({ ok: true });
    renderRegister();
    await fillForm(user);

    await submit(user);

    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Jane Smith",
        email: "jane@firm.com",
        password: "Passw0rd!",
        plan: "trial",
      }),
    );
    expect(screen.getByText("arrived at /app/dashboard")).toBeInTheDocument();
  });

  it("shows the error returned for a failed registration and stays on the page", async () => {
    register.mockResolvedValue({ ok: false, error: "Already registered" });
    renderRegister();
    await fillForm(user);

    await submit(user);

    expect(screen.getByText("Already registered")).toBeInTheDocument();
    expect(screen.queryByText(/arrived at/)).not.toBeInTheDocument();
  });
});
