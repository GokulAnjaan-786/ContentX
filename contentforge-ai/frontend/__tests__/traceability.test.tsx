import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { TraceabilityPanel } from "@/components/traceability/TraceabilityPanel";
import { FactRegistryItem } from "@/lib/api";

describe("Traceability Panel Component", () => {
  const mockFacts: FactRegistryItem[] = [
    {
      id: "fact-1",
      document_id: "doc-1",
      fact_id_string: "f1",
      fact_statement: "API attacks increased by 340% in Q2 2026 across enterprise tenants.",
      source_chunk_id: "chunk-101",
      source_snippet: "According to our global sensor network, API attacks surged by 340% between April and June 2026.",
      confidence: 0.98,
      created_at: "2026-09-26T00:00:00Z",
    },
    {
      id: "fact-2",
      document_id: "doc-1",
      fact_id_string: "f2",
      fact_statement: "Multi-factor authentication halted 98% of lateral threat movements.",
      source_chunk_id: "chunk-102",
      source_snippet: "Enforcement of FIDO2-compliant MFA successfully blocked 98 percent of lateral movement attempts.",
      confidence: 0.95,
      created_at: "2026-09-26T00:00:00Z",
    },
  ];

  test("clicking a verified claim shows the correct source snippet from mock data", () => {
    const handleClose = jest.fn();

    render(
      <TraceabilityPanel
        selectedClaim={{
          claimText: "Our threat intelligence team detected 340% increase in API attacks.",
          factIds: ["f1"],
          isUnverified: false,
        }}
        factsRegistry={mockFacts}
        onClose={handleClose}
      />
    );

    expect(screen.getByTestId("traceability-panel")).toBeInTheDocument();
    expect(screen.getByText(/Verified Source Grounding/i)).toBeInTheDocument();
    expect(screen.getByText(/\[F1\]/i)).toBeInTheDocument();
    expect(screen.getByText(/API attacks increased by 340% in Q2 2026/i)).toBeInTheDocument();

    // Check exact source snippet from Fact Registry
    const snippetElem = screen.getByTestId("traceability-source-snippet");
    expect(snippetElem).toHaveTextContent(
      "According to our global sensor network, API attacks surged by 340% between April and June 2026."
    );
  });

  test("shows 'No matching source text found' when claim has no matching fact or is unverified", () => {
    const handleClose = jest.fn();

    render(
      <TraceabilityPanel
        selectedClaim={{
          claimText: "Unsubstantiated speculative prediction about 2030.",
          factIds: [],
          isUnverified: true,
          unverifiedReason: "No corresponding chunk found in uploaded report.",
        }}
        factsRegistry={mockFacts}
        onClose={handleClose}
      />
    );

    expect(screen.getByTestId("traceability-panel")).toBeInTheDocument();
    expect(screen.getByTestId("traceability-unverified-alert")).toBeInTheDocument();
    expect(screen.getByText(/No matching source text found/i)).toBeInTheDocument();
    expect(
      screen.getByText(/This claim could not be matched to the source document/i)
    ).toBeInTheDocument();
  });
});
