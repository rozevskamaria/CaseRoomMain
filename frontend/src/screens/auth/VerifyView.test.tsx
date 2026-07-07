import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { VerifyView } from "./VerifyView";
import { ConsumeMagicLinkMutation } from "../../graphql/authOperations";

function noop() {}

function consumeMock(onCall: () => void, ok = true, reason: string | null = null) {
  return {
    request: { query: ConsumeMagicLinkMutation, variables: { token: "tok-123" } },
    result: () => {
      onCall();
      return {
        data: {
          __typename: "Mutation",
          consumeMagicLink: { __typename: "ConsumeResultType", ok, reason },
        },
      };
    },
  };
}

describe("VerifyView", () => {
  it("does NOT consume the magic link on mount", async () => {
    let consumed = false;
    render(
      <MockedProvider mocks={[consumeMock(() => (consumed = true))]}>
        <VerifyView token="tok-123" onConfirmed={noop} onBackToLogin={noop} />
      </MockedProvider>,
    );

    expect(
      screen.getByRole("button", { name: "Confirm sign in" }),
    ).toBeInTheDocument();
    await Promise.resolve();
    await Promise.resolve();
    expect(consumed).toBe(false);
  });

  it("consumes the magic link only on explicit confirm click", async () => {
    let consumed = false;
    let confirmedCalled = false;
    render(
      <MockedProvider mocks={[consumeMock(() => (consumed = true))]}>
        <VerifyView
          token="tok-123"
          onConfirmed={() => (confirmedCalled = true)}
          onBackToLogin={noop}
        />
      </MockedProvider>,
    );

    expect(consumed).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Confirm sign in" }));

    await waitFor(() => expect(consumed).toBe(true));
    await waitFor(() => expect(confirmedCalled).toBe(true));
  });

  it("shows an expired message and offers a new link when token is missing", () => {
    let backCalled = false;
    render(
      <MockedProvider mocks={[]}>
        <VerifyView token={null} onConfirmed={noop} onBackToLogin={() => (backCalled = true)} />
      </MockedProvider>,
    );

    expect(
      screen.getByText("This link has expired or is invalid. Request a new one to sign in."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Request a new link" }));
    expect(backCalled).toBe(true);
  });

  it("shows the expired state when consume returns ok:false", async () => {
    render(
      <MockedProvider mocks={[consumeMock(() => {}, false, "expired")]}>
        <VerifyView token="tok-123" onConfirmed={noop} onBackToLogin={noop} />
      </MockedProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Confirm sign in" }));

    expect(
      await screen.findByText(
        "This link has expired or is invalid. Request a new one to sign in.",
      ),
    ).toBeInTheDocument();
  });
});
