import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { RegisterView } from "./RegisterView";
import { RegisterStudentMutation } from "../../graphql/authOperations";

function noop() {}

describe("RegisterView", () => {
  it("submits registerStudent and shows the check-email state", async () => {
    let called = false;
    const mock = {
      request: {
        query: RegisterStudentMutation,
        variables: { loginName: "601274", fullName: "Jane Doe" },
      },
      result: () => {
        called = true;
        return {
          data: {
            __typename: "Mutation",
            registerStudent: { __typename: "AuthResult", ok: true },
          },
        };
      },
    };

    render(
      <MockedProvider mocks={[mock]}>
        <RegisterView onGoToLogin={noop} />
      </MockedProvider>,
    );

    fireEvent.change(screen.getByLabelText("Student ID"), {
      target: { value: "601274" },
    });
    fireEvent.change(screen.getByLabelText("Full name (optional)"), {
      target: { value: "Jane Doe" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Check your email")).toBeInTheDocument();
    await waitFor(() => expect(called).toBe(true));
  });

  it("sends a null full name when left blank", async () => {
    let sentVariables: Record<string, unknown> | null = null;
    const mock = {
      request: {
        query: RegisterStudentMutation,
        variables: { loginName: "601274", fullName: null },
      },
      result: () => {
        sentVariables = { loginName: "601274", fullName: null };
        return {
          data: {
            __typename: "Mutation",
            registerStudent: { __typename: "AuthResult", ok: true },
          },
        };
      },
    };

    render(
      <MockedProvider mocks={[mock]}>
        <RegisterView onGoToLogin={noop} />
      </MockedProvider>,
    );

    fireEvent.change(screen.getByLabelText("Student ID"), {
      target: { value: "601274" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await screen.findByText("Check your email");
    await waitFor(() => expect(sentVariables).toEqual({ loginName: "601274", fullName: null }));
  });
});
