import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";

import { fetchSearchSuggestions } from "../suggestions-api";

import { SearchSuggestions } from "./search-suggestions";

vi.mock("../suggestions-api", () => ({
  fetchSearchSuggestions: vi.fn(),
}));

const mockFetch = vi.mocked(fetchSearchSuggestions);

/** Stateful wrapper to simulate controlled component behavior */
function TestHarness({ onSelect = vi.fn() }: { onSelect?: (v: string) => void }) {
  const [query, setQuery] = useState("");
  return (
    <SearchSuggestions
      query={query}
      onQueryChange={setQuery}
      onSelect={onSelect}
      inputId="test-query"
    />
  );
}

describe("SearchSuggestions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockFetch.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders input with placeholder and helper text", () => {
    render(<TestHarness />);

    expect(
      screen.getByPlaceholderText("e.g. recurring headaches with nausea"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Describe a presentation in plain language/),
    ).toBeInTheDocument();
  });

  it("has correct accessibility attributes", () => {
    render(<TestHarness />);

    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-autocomplete", "list");
    expect(input).toHaveAttribute("aria-expanded", "false");
    expect(input).toHaveAttribute("aria-controls", "test-query-suggestions");
  });

  it("does not fetch suggestions for queries shorter than 2 characters", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<TestHarness />);

    const input = screen.getByRole("textbox");
    await user.type(input, "a");

    await vi.advanceTimersByTimeAsync(300);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("fetches and displays suggestions after debounce", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    mockFetch.mockResolvedValue(["chest pain", "chest tightness"]);

    render(<TestHarness />);

    const input = screen.getByRole("textbox");
    await user.type(input, "ch");

    // Advance past debounce
    await vi.advanceTimersByTimeAsync(300);

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
      expect(screen.getByText("chest pain")).toBeInTheDocument();
      expect(screen.getByText("chest tightness")).toBeInTheDocument();
    });
  });

  it("calls onSelect when a suggestion is clicked", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    mockFetch.mockResolvedValue(["headache with aura"]);

    const onSelect = vi.fn();
    render(<TestHarness onSelect={onSelect} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "he");

    await vi.advanceTimersByTimeAsync(300);

    await waitFor(() => {
      expect(screen.getByText("headache with aura")).toBeInTheDocument();
    });

    await user.click(screen.getByText("headache with aura"));
    expect(onSelect).toHaveBeenCalledWith("headache with aura");
  });

  it("closes suggestions on Escape key", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    mockFetch.mockResolvedValue(["suggestion one"]);

    render(<TestHarness />);

    const input = screen.getByRole("textbox");
    await user.type(input, "su");

    await vi.advanceTimersByTimeAsync(300);

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    await user.keyboard("{Escape}");

    await waitFor(() => {
      expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    });
  });

  it("supports keyboard navigation with ArrowDown and Enter", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    mockFetch.mockResolvedValue(["first option", "second option"]);

    const onSelect = vi.fn();
    render(<TestHarness onSelect={onSelect} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "fi");

    await vi.advanceTimersByTimeAsync(300);

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    // Navigate down and select
    await user.keyboard("{ArrowDown}{Enter}");
    expect(onSelect).toHaveBeenCalledWith("first option");
  });
});
