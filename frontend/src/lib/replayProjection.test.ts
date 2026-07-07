import { describe, expect, it } from "vitest";
import { projectReplay } from "./replayProjection";

function msg(id: string, type: string, text = "x") {
  return { __typename: "MessageType" as const, id, type, text };
}

describe("projectReplay", () => {
  it("splits chat messages from investigation messages", () => {
    const session = {
      messages: [
        msg("1", "student"),
        msg("2", "parent"),
        msg("3", "lab"),
        msg("4", "tutor"),
        msg("5", "lab_note"),
        msg("6", "lab_tutor"),
        msg("7", "safety"),
        msg("8", "system"),
      ],
    };

    const { consultation, investigations, labCount } = projectReplay(session);

    expect(consultation.map((m) => m.id)).toEqual(["1", "2", "4", "7", "8"]);
    expect(investigations.map((m) => m.id)).toEqual(["3", "5", "6"]);
    expect(labCount).toBe(1);
  });

  it("counts only lab rows toward labCount", () => {
    const session = {
      messages: [msg("1", "lab"), msg("2", "lab"), msg("3", "lab_note")],
    };
    expect(projectReplay(session).labCount).toBe(2);
  });

  it("preserves message order within each bucket", () => {
    const session = {
      messages: [msg("a", "parent"), msg("b", "student"), msg("c", "parent")],
    };
    expect(projectReplay(session).consultation.map((m) => m.id)).toEqual([
      "a",
      "b",
      "c",
    ]);
  });

  it("handles an empty transcript", () => {
    const result = projectReplay({ messages: [] });
    expect(result.consultation).toEqual([]);
    expect(result.investigations).toEqual([]);
    expect(result.labCount).toBe(0);
  });
});
