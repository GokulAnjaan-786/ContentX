import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import VerifyPortalPage from "@/app/verify/page";
import VerifyRecordPage from "@/app/verify/[recordId]/page";
import { verificationApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  verificationApi: {
    verifyRecord: jest.fn(),
    verifyByText: jest.fn(),
    verifyByFile: jest.fn(),
    adminVerifyChain: jest.fn(),
  },
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ recordId: "rec-uuid-12345" }),
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/verify",
}));

describe("Public Verification Portal Components", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("portal page verifies content text and displays authentic result", async () => {
    (verificationApi.verifyByText as jest.Mock).mockResolvedValueOnce({
      status: "verified",
      record_id: "rec-uuid-12345",
      record_type: "generated_output",
      organisation_name: "Acme Cyber Defense Corp",
      output_type: "advisory",
      approved_by: "Chief Information Security Officer",
      approved_at: "2026-09-26T12:00:00Z",
      source_document_verified: true,
      chain_integrity: "intact",
      chain_index: 2,
      content_hash: "a".repeat(64),
      record_hash: "b".repeat(64),
    });

    render(<VerifyPortalPage />);

    const textarea = screen.getByPlaceholderText(/Paste the full text of the advisory/i);
    const submitBtn = screen.getByRole("button", { name: /Verify Content Authenticity/i });

    fireEvent.change(textarea, { target: { value: "Authentic cybersecurity bulletin content..." } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Content Perfectly Verified/i)).toBeInTheDocument();
    expect(screen.getByText("Acme Cyber Defense Corp")).toBeInTheDocument();
    expect(screen.getByText("Chief Information Security Officer")).toBeInTheDocument();
  });

  test("portal page shows unverified message for altered content", async () => {
    (verificationApi.verifyByText as jest.Mock).mockResolvedValueOnce({
      status: "not_found",
      message: "No matching verified record found.",
    });

    render(<VerifyPortalPage />);

    const textarea = screen.getByPlaceholderText(/Paste the full text of the advisory/i);
    const submitBtn = screen.getByRole("button", { name: /Verify Content Authenticity/i });

    fireEvent.change(textarea, { target: { value: "Altered fake advisory..." } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/No Official Matching Record Found/i)).toBeInTheDocument();
  });

  test("record page loads and displays verified details for authentic record", async () => {
    (verificationApi.verifyRecord as jest.Mock).mockResolvedValueOnce({
      status: "verified",
      record_id: "rec-uuid-12345",
      record_type: "generated_output",
      organisation_name: "Acme Cyber Defense Corp",
      output_type: "advisory",
      approved_by: "Chief Information Security Officer",
      approved_at: "2026-09-26T12:00:00Z",
      source_document_verified: true,
      chain_integrity: "intact",
      chain_index: 1,
      content_hash: "e".repeat(64),
      record_hash: "f".repeat(64),
    });

    render(<VerifyRecordPage />);

    expect(await screen.findByText(/Authentic Official Output/i)).toBeInTheDocument();
    expect(screen.getByText("Block #1")).toBeInTheDocument();
    expect(screen.getByText("Acme Cyber Defense Corp")).toBeInTheDocument();
    expect(screen.getByText(/Chief Information Security Officer/i)).toBeInTheDocument();
    expect(screen.getByText(/Tamper-Evident Hash Chain/i)).toBeInTheDocument();
  });
});
