import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MockedProvider } from "@apollo/client/testing";
import { describe, expect, it } from "vitest";
import { EnrollStudentForm } from "./EnrollStudentForm";
import { LookupStudentQuery } from "../../graphql/cohortOperations";

const COHORT = "c-1";

function lookupMock(loginName: string, status: string, fullName: string | null) {
  return {
    request: {
      query: LookupStudentQuery,
      variables: { cohortId: COHORT, loginName },
    },
    result: {
      data: {
        __typename: "Query",
        lookupStudent: { __typename: "StudentLookupResult", status, fullName },
      },
    },
    maxUsageCount: 5,
  };
}

function renderForm(mocks: ReturnType<typeof lookupMock>[]) {
  return render(
    <MockedProvider mocks={mocks}>
      <EnrollStudentForm cohortId={COHORT} />
    </MockedProvider>,
  );
}

function idInput() {
  return screen.getByLabelText("Student ID") as HTMLInputElement;
}

describe("EnrollStudentForm", () => {
  it("clamps the ID input to six digits and strips non-digits", () => {
    renderForm([]);
    fireEvent.change(idInput(), { target: { value: "12ab34cd5678" } });
    expect(idInput().value).toBe("123456");
  });

  it("does not lookup or enable submit before six digits", () => {
    renderForm([]);
    fireEvent.change(idInput(), { target: { value: "1234" } });
    expect(screen.getByRole("button", { name: "Add to cohort" })).toBeDisabled();
  });

  it("shows an enrollable banner with the name and enables submit", async () => {
    renderForm([lookupMock("482913", "enrollable", "Jane Doe")]);
    fireEvent.change(idInput(), { target: { value: "482913" } });

    expect(
      await screen.findByText("Ready to enrol: Jane Doe"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add to cohort" }),
    ).not.toBeDisabled();
  });

  it("shows an amber already-enrolled banner and keeps submit disabled", async () => {
    renderForm([lookupMock("482913", "already_enrolled", "Jane Doe")]);
    fireEvent.change(idInput(), { target: { value: "482913" } });

    expect(
      await screen.findByText("This student is already enrolled in this cohort."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add to cohort" })).toBeDisabled();
  });

  it("shows a not-found banner and keeps submit disabled", async () => {
    renderForm([lookupMock("000000", "not_found", null)]);
    fireEvent.change(idInput(), { target: { value: "000000" } });

    expect(
      await screen.findByText("No student found with that ID."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add to cohort" })).toBeDisabled();
  });

  it("shows a not-a-student banner and keeps submit disabled", async () => {
    renderForm([lookupMock("555555", "not_a_student", null)]);
    fireEvent.change(idInput(), { target: { value: "555555" } });

    expect(
      await screen.findByText(
        "That ID belongs to an account that is not a student.",
      ),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Add to cohort" })).toBeDisabled(),
    );
  });
});
