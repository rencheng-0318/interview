import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock next/link to a simple anchor
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

// Mock suggestions API to prevent fetch calls
vi.mock("../suggestions-api", () => ({
  fetchSearchSuggestions: vi.fn().mockResolvedValue([]),
}));

// Mock useActionState to control the state directly
let mockState: import("../types").SearchState = { status: "idle" };
const mockFormAction = vi.fn();

vi.mock("react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react")>();
  return {
    ...actual,
    useActionState: () => [mockState, mockFormAction],
  };
});

// Mock useFormStatus
vi.mock("react-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-dom")>();
  return {
    ...actual,
    useFormStatus: () => ({ pending: false }),
  };
});

import { SearchPanel } from "./search-panel";

import type { SearchState } from "../types";

const successState: SearchState = {
  status: "success",
  query: "chest pain",
  data: {
    query: "chest pain",
    results: [
      {
        patient: { id: "patient-001", displayName: "Jane Smith" },
        bestMatch: {
          documentId: "doc-1",
          documentType: "diagnostic_note",
          documentTitle: "Cardiology Assessment",
          documentDate: "2024-03-15",
          snippet: "Patient presents with acute chest pain radiating to left arm.",
          relevanceScore: 0.92,
        },
        additionalMatchingDocuments: 2,
      },
      {
        patient: { id: "patient-002", displayName: "Bob Wilson" },
        bestMatch: {
          documentId: "doc-2",
          documentType: "lab_report",
          documentTitle: "Troponin Panel",
          documentDate: "2024-02-20",
          snippet: "Elevated troponin levels consistent with myocardial injury.",
          relevanceScore: 0.85,
        },
        additionalMatchingDocuments: 0,
      },
    ],
    meta: { resultCount: 2, tookMs: 23 },
  },
};

describe("SearchPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockState = { status: "idle" };
  });

  it("renders the idle state with instructions", () => {
    render(<SearchPanel />);

    expect(screen.getByText("Search clinical records")).toBeInTheDocument();
    expect(
      screen.getByText(/Describe a clinical presentation in plain language/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("renders document type filter options", () => {
    render(<SearchPanel />);

    expect(screen.getByLabelText("Document type")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "All types" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Diagnostic note" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Specialist note" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Radiology report" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Laboratory report" })).toBeInTheDocument();
  });

  it("shows validation error state", () => {
    mockState = {
      status: "validation_error",
      error: "Please enter a search query.",
      query: "",
    };

    render(<SearchPanel />);

    expect(screen.getByText("Invalid query")).toBeInTheDocument();
    expect(screen.getByText("Please enter a search query.")).toBeInTheDocument();
  });

  it("shows service error state", () => {
    mockState = {
      status: "service_error",
      error: "The search service is temporarily unavailable. Please try again shortly.",
      query: "headache",
    };

    render(<SearchPanel />);

    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("The search service is temporarily unavailable. Please try again shortly."),
    ).toBeInTheDocument();
  });

  it("shows no results state", () => {
    mockState = {
      status: "no_results",
      query: "zebra disease",
      data: { query: "zebra disease", results: [], meta: { resultCount: 0, tookMs: 8 } },
    };

    render(<SearchPanel />);

    expect(screen.getByText("No matching patients")).toBeInTheDocument();
    expect(screen.getByText(/No records matched "zebra disease"/)).toBeInTheDocument();
  });

  it("renders search results with patient cards", () => {
    mockState = successState;

    render(<SearchPanel />);

    // Meta info
    expect(screen.getByText(/2 results in 23 ms/)).toBeInTheDocument();

    // Patient cards
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText("Bob Wilson")).toBeInTheDocument();

    // Document type badges (also appears in select options, so use getAllByText)
    const diagnosticNotes = screen.getAllByText("Diagnostic note");
    expect(diagnosticNotes.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Laboratory report").length).toBeGreaterThanOrEqual(1);

    // Document titles and dates
    expect(screen.getByText(/Cardiology Assessment/)).toBeInTheDocument();
    expect(screen.getByText(/Troponin Panel/)).toBeInTheDocument();

    // Snippets
    expect(screen.getByText(/Patient presents with acute chest pain/)).toBeInTheDocument();
    expect(screen.getByText(/Elevated troponin levels/)).toBeInTheDocument();

    // Additional documents indicator
    expect(screen.getByText("+2 more matching documents")).toBeInTheDocument();
  });

  it("renders patient detail links", () => {
    mockState = successState;

    render(<SearchPanel />);

    const link = screen.getByText("Jane Smith");
    expect(link).toHaveAttribute("href", "/patients/patient-001");

    const link2 = screen.getByText("Bob Wilson");
    expect(link2).toHaveAttribute("href", "/patients/patient-002");
  });

  it("does not show additional documents text when count is 0", () => {
    mockState = successState;

    render(<SearchPanel />);

    // Bob has 0 additional documents — only Jane's "+2" should appear
    expect(screen.getByText("+2 more matching documents")).toBeInTheDocument();
    expect(screen.queryByText("+0 more matching documents")).not.toBeInTheDocument();
  });

  it("shows singular result text for one result", () => {
    mockState = {
      status: "success",
      query: "headache",
      data: {
        query: "headache",
        results: [
          {
            patient: { id: "p1", displayName: "Alice" },
            bestMatch: {
              documentId: "d1",
              documentType: "specialist_note",
              documentTitle: "Neuro Note",
              documentDate: "2024-01-01",
              snippet: "Migraine with aura",
              relevanceScore: 0.9,
            },
            additionalMatchingDocuments: 1,
          },
        ],
        meta: { resultCount: 1, tookMs: 10 },
      },
    };

    render(<SearchPanel />);

    expect(screen.getByText(/1 result in 10 ms/)).toBeInTheDocument();
    expect(screen.getByText("+1 more matching document")).toBeInTheDocument();
  });
});
