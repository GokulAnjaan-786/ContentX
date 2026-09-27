import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "@/app/login/page";
import { authApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
  },
}));

describe("Login Form Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test("shows validation error on empty fields", async () => {
    render(<LoginPage />);

    const submitBtn = screen.getByTestId("auth-submit-btn");
    fireEvent.click(submitBtn);

    // Error alert should be displayed
    expect(
      await screen.findByText(/Email and password are required/i)
    ).toBeInTheDocument();
    expect(authApi.login).not.toHaveBeenCalled();
  });

  test("calls the auth API correctly on submit", async () => {
    (authApi.login as jest.Mock).mockResolvedValueOnce({
      access_token: "mock-jwt-token-12345",
      token_type: "bearer",
      expires_in: 3600,
      user: {
        id: "usr-1",
        org_id: "org-1",
        email: "operator@test.com",
        role: "operator",
        created_at: "2026-09-26T00:00:00Z",
      },
    });

    render(<LoginPage />);

    const emailInput = screen.getByTestId("email-input");
    const passwordInput = screen.getByTestId("password-input");
    const submitBtn = screen.getByTestId("auth-submit-btn");

    fireEvent.change(emailInput, { target: { value: "operator@test.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledTimes(1);
      expect(authApi.login).toHaveBeenCalledWith({
        email: "operator@test.com",
        password: "password123",
      });
    });

    // Verify token stored in localStorage
    expect(localStorage.getItem("contentforge_access_token")).toBe("mock-jwt-token-12345");
  });
});
