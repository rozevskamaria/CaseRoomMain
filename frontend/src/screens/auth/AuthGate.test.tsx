import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { afterEach, describe, expect, it } from "vitest";
import { AuthGate } from "./AuthGate";
import { LogoutMutation, MeQuery } from "../../graphql/authOperations";
import { MyCohortsQuery } from "../../graphql/cohortOperations";
import { resetSeenCases } from "../../state/seenCases";

const studentMe = {
  __typename: "MeType" as const,
  id: "u-1",
  role: "student",
  status: "active",
  loginName: "482913",
  email: "482913@rsu.edu.lv",
  fullName: null,
};

const staffMe = { ...studentMe, id: "s-1", role: "staff", loginName: "100001" };
const adminMe = { ...studentMe, id: "a-1", role: "admin", loginName: "100002" };

function meMock(me: typeof studentMe | null) {
  return {
    request: { query: MeQuery },
    result: { data: { __typename: "Query", me } },
  };
}

function myCohortsMock() {
  return {
    request: { query: MyCohortsQuery },
    result: { data: { __typename: "Query", myCohorts: [] } },
    maxUsageCount: 5,
  };
}

const logoutMock = {
  request: { query: LogoutMutation },
  result: {
    data: { __typename: "Mutation", logout: { __typename: "AuthResult", ok: true } },
  },
};

afterEach(() => {
  resetSeenCases();
  window.history.replaceState({}, "", "/");
});

describe("AuthGate", () => {
  it("shows the login screen when me is null", async () => {
    render(
      <MockedProvider mocks={[meMock(null)]}>
        <AuthGate />
      </MockedProvider>,
    );

    expect(
      await screen.findByRole("button", { name: "Send login link" }),
    ).toBeInTheDocument();
  });

  it("renders the app when me is an authenticated student", async () => {
    render(
      <MockedProvider mocks={[meMock(studentMe)]}>
        <AuthGate />
      </MockedProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Clinical Immunology" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
  });

  it("renders the educator dashboard for a staff me", async () => {
    render(
      <MockedProvider mocks={[meMock(staffMe), myCohortsMock()]}>
        <AuthGate />
      </MockedProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Educator Dashboard" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("No cohorts yet"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Clinical Immunology" }),
    ).toBeNull();
  });

  it("renders the educator dashboard for an admin me", async () => {
    render(
      <MockedProvider mocks={[meMock(adminMe), myCohortsMock()]}>
        <AuthGate />
      </MockedProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Educator Dashboard" }),
    ).toBeInTheDocument();
  });

  it("routes to the verify screen when the URL is /auth/verify", async () => {
    window.history.replaceState({}, "", "/auth/verify?token=abc");
    render(
      <MockedProvider mocks={[meMock(null)]}>
        <AuthGate />
      </MockedProvider>,
    );

    expect(
      await screen.findByRole("button", { name: "Confirm sign in" }),
    ).toBeInTheDocument();
  });

  it("logs out and returns to the login screen", async () => {
    render(
      <MockedProvider mocks={[meMock(studentMe), logoutMock, meMock(null)]}>
        <AuthGate />
      </MockedProvider>,
    );

    const signOut = await screen.findByRole("button", { name: "Sign out" });
    fireEvent.click(signOut);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Send login link" }),
      ).toBeInTheDocument(),
    );
  });
});
