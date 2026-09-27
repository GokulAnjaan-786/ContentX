import React from "react";
import { render, screen } from "@testing-library/react";
import { ExecutiveSummaryCard } from "@/components/output-cards/ExecutiveSummaryCard";
import { GeneratedOutput } from "@/lib/api";

describe("Unverified Claims Visual Distinction", () => {
  test("unverified claims are visually distinguished from verified ones in a rendered output card", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-diff-1",
      job_id: "job-100",
      output_type: "executive_summary",
      validation_score: 0.72,
      status: "completed_with_warnings",
      fact_ids_used: ["f1"],
      unverified_claims: [
        {
          claim: "Quantum computing will crack standard RSA by next Tuesday.",
          reason: "Not supported by source document facts.",
          cited_fact_ids: [],
        },
      ],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        title: "Cyber Resilience Assessment",
        summary_text:
          "Enterprise systems experienced a 40% reduction in downtime. Quantum computing will crack standard RSA by next Tuesday.",
        key_takeaways: [
          "Enterprise systems experienced a 40% reduction in downtime.",
          "Quantum computing will crack standard RSA by next Tuesday.",
        ],
        fact_ids_used: ["f1"],
      },
    };

    render(<ExecutiveSummaryCard output={mockOutput} />);

    // Query unverified claims in the rendered output
    const unverifiedElements = screen.getAllByTestId("unverified-claim");
    expect(unverifiedElements.length).toBeGreaterThan(0);

    // Check first unverified element properties
    const unverifiedClaim = unverifiedElements[0];
    expect(unverifiedClaim).toHaveClass("claim-unverified");
    expect(unverifiedClaim).toHaveAttribute(
      "title",
      "This claim could not be matched to the source document"
    );
    expect(unverifiedClaim).toHaveTextContent(
      "Quantum computing will crack standard RSA by next Tuesday."
    );

    // Query verified claims
    const verifiedElements = screen.getAllByTestId("verified-claim");
    expect(verifiedElements.length).toBeGreaterThan(0);

    const verifiedClaim = verifiedElements[0];
    expect(verifiedClaim).not.toHaveClass("claim-unverified");
    expect(verifiedClaim).toHaveClass("claim-verified");
    expect(verifiedClaim).toHaveTextContent(
      "Enterprise systems experienced a 40% reduction in downtime."
    );
  });
});
