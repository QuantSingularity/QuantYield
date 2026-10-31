import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ToastProvider, useToast } from "./ToastContext";

function Trigger({ message = "Saved", type, duration }) {
  const toast = useToast();
  return (
    <button onClick={() => toast(message, type, duration)}>
      show {message}
    </button>
  );
}

function renderToast(props) {
  return render(
    <ToastProvider>
      <Trigger {...props} />
    </ToastProvider>,
  );
}

function show(label = "show Saved") {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("ToastProvider", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a toast with the requested type", () => {
    renderToast({ type: "success" });

    show();

    expect(screen.getByText("Saved").closest(".toast")).toHaveClass(
      "toast",
      "success",
    );
  });

  it("defaults to an info toast", () => {
    renderToast({});

    show();

    expect(screen.getByText("Saved").closest(".toast")).toHaveClass("info");
  });

  it("removes the toast after the default 3.5 seconds", () => {
    renderToast({});
    show();

    act(() => vi.advanceTimersByTime(3499));
    expect(screen.getByText("Saved")).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(1));
    expect(screen.queryByText("Saved")).not.toBeInTheDocument();
  });

  it("honours a custom duration", () => {
    renderToast({ duration: 1000 });
    show();

    act(() => vi.advanceTimersByTime(1000));

    expect(screen.queryByText("Saved")).not.toBeInTheDocument();
  });

  it("dismisses a toast from its close button", () => {
    renderToast({});
    show();
    const toast = screen.getByText("Saved").closest(".toast");

    fireEvent.click(within(toast).getByRole("button"));

    expect(screen.queryByText("Saved")).not.toBeInTheDocument();
  });

  it("stacks several toasts", () => {
    renderToast({});

    show();
    show();

    expect(screen.getAllByText("Saved")).toHaveLength(2);
  });
});

describe("useToast", () => {
  it("throws outside a ToastProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<Trigger />)).toThrow(
      "useToast must be used within ToastProvider",
    );
    vi.restoreAllMocks();
  });
});
