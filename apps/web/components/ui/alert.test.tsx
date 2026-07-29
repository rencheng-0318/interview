import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Alert } from "./alert";

describe("Alert", () => {
  it("renders the title and body", () => {
    render(
      <Alert tone="info" title="Nothing indexed yet">
        Run the indexer first.
      </Alert>,
    );

    expect(screen.getByText("Nothing indexed yet")).toBeInTheDocument();
    expect(screen.getByText("Run the indexer first.")).toBeInTheDocument();
  });

  it("announces failures assertively so they are not missed", () => {
    render(<Alert tone="danger" title="Search failed" />);

    expect(screen.getByRole("alert")).toHaveTextContent("Search failed");
  });

  it("uses a polite role for non-failure states", () => {
    render(<Alert tone="success" title="Indexing complete" />);

    expect(screen.getByRole("status")).toHaveTextContent("Indexing complete");
  });

  it("conveys state with a text label rather than colour alone", () => {
    render(<Alert tone="warning" title="Partial results" />);

    expect(screen.getByText("Warning:")).toBeInTheDocument();
  });
});
