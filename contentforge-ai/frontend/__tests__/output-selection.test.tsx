import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import OutputSelectionPage from "@/app/new-transformation/output-selection/page";
import { generationApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  generationApi: {
    generate: jest.fn(),
  },
}));

describe("Output Selection Screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("Generate button is disabled until at least one output type is selected", async () => {
    render(<OutputSelectionPage />);

    // Click "Clear All" to remove all selected formats
    const clearAllBtn = screen.getByText(/Clear All/i);
    fireEvent.click(clearAllBtn);

    // Generate button should now be disabled
    const generateBtn = screen.getByTestId("generate-outputs-btn");
    expect(generateBtn).toBeDisabled();
    expect(screen.getByText(/Select at Least 1 Output/i)).toBeInTheDocument();

    // Now select one output: LinkedIn
    const linkedinCard = screen.getByTestId("output-card-linkedin");
    fireEvent.click(linkedinCard);

    // Button should now be enabled
    expect(generateBtn).not.toBeDisabled();
    expect(screen.getByText(/Generate 1 Format/i)).toBeInTheDocument();
  });
});
