import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { LoginView } from "./LoginView";
import { RequestLoginLinkMutation } from "../../graphql/authOperations";

function noop() {}

describe("LoginView", () => {
  it("disables the submit button until a 6-digit ID is entered", () => {
    render(
      <MockedProvider mocks={[]}>
        <LoginView onGoToRegister={noop} onAuthed={noop} />
      </MockedProvider>,
    );

    const submit = screen.getByRole("button", { name: "Send login link" });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Student ID"), {
      target: { value: "482913" },
    });
    expect(submit).toBeEnabled();
  });

  it("submits requestLoginLink and shows the check-email state", async () => {
    let called = false;
    const mock = {
      request: {
        query: RequestLoginLinkMutation,
        variables: { loginName: "482913" },
      },
      result: () => {
        called = true;
        return {
          data: {
            __typename: "Mutation",
            requestLoginLink: { __typename: "AuthResult", ok: true },
          },
        };
      },
    };

    render(
      <MockedProvider mocks={[mock]}>
        <LoginView onGoToRegister={noop} onAuthed={noop} />
      </MockedProvider>,
    );

    fireEvent.change(screen.getByLabelText("Student ID"), {
      target: { value: "482913" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send login link" }));

    expect(await screen.findByText("Check your email")).toBeInTheDocument();
    expect(screen.getByText("482913")).toBeInTheDocument();
    await waitFor(() => expect(called).toBe(true));
  });

  it("navigates to register", () => {
    let toRegister = false;
    render(
      <MockedProvider mocks={[]}>
        <LoginView onGoToRegister={() => (toRegister = true)} onAuthed={noop} />
      </MockedProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(toRegister).toBe(true);
  });
});
