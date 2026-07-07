import type { SessionFieldsFragment } from "../gql/graphql";

export type ReplayMessage = SessionFieldsFragment["messages"][number];

export interface ReplayProjection {
  consultation: ReplayMessage[];
  investigations: ReplayMessage[];
  labCount: number;
}

const LAB_TYPES = ["lab", "lab_note", "lab_tutor"];

export function projectReplay(
  session: Pick<SessionFieldsFragment, "messages">,
): ReplayProjection {
  const messages = session.messages ?? [];
  const consultation = messages.filter((m) => !LAB_TYPES.includes(m.type));
  const investigations = messages.filter((m) => LAB_TYPES.includes(m.type));
  const labCount = messages.filter((m) => m.type === "lab").length;
  return { consultation, investigations, labCount };
}
