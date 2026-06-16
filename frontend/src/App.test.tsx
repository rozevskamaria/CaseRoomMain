import { render, screen } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { gql } from "@apollo/client";
import { describe, it, expect } from "vitest";
import App from "./App";

const PING = gql`
  query Ping {
    ping
    version
    health
  }
`;

const mocks = [
  {
    request: { query: PING },
    result: {
      data: { __typename: "Query", ping: "pong", version: "0.1.0", health: "ok" },
    },
  },
];

describe("App", () => {
  it("renders the heading immediately", () => {
    render(
      <MockedProvider mocks={mocks}>
        <App />
      </MockedProvider>,
    );
    expect(screen.getByRole("heading", { name: "CaseRoom" })).toBeInTheDocument();
  });

  it("shows the loading state before the mock resolves", () => {
    render(
      <MockedProvider mocks={mocks}>
        <App />
      </MockedProvider>,
    );
    expect(screen.getByText(/Connecting to backend/i)).toBeInTheDocument();
  });

  it("renders the backend value once the mock resolves", async () => {
    render(
      <MockedProvider mocks={mocks}>
        <App />
      </MockedProvider>,
    );
    expect(await screen.findByText(/Backend says: pong · v0\.1\.0/i)).toBeInTheDocument();
  });
});
