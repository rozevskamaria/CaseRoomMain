import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect } from "vitest";
import { parseLabText, flagRow, type LabLine } from "./labText";

const FIXTURE_DIR = resolve(process.cwd(), "../backend/tests/fixtures/parity");

interface ParseFixture {
  input: string;
  output: LabLine[];
}

interface FlagFixture {
  input: string;
  output: string;
}

function loadFixture<T>(name: string): T[] {
  return JSON.parse(readFileSync(`${FIXTURE_DIR}/${name}`, "utf-8")) as T[];
}

const parseFixtures = loadFixture<ParseFixture>("parseLabText.json");
const flagFixtures = loadFixture<FlagFixture>("flagRow.json");

describe("parseLabText parity", () => {
  it("loads the canonical oracle fixtures", () => {
    expect(parseFixtures.length).toBe(31);
  });

  it.each(parseFixtures.map((f, i) => [i, f] as const))(
    "reproduces the oracle output for entry %i",
    (_i, fixture) => {
      expect(parseLabText(fixture.input)).toEqual(fixture.output);
    },
  );
});

describe("flagRow parity", () => {
  it("loads the canonical oracle fixtures", () => {
    expect(flagFixtures.length).toBe(73);
  });

  it.each(flagFixtures.map((f, i) => [i, f] as const))(
    "reproduces the oracle output for entry %i",
    (_i, fixture) => {
      expect(flagRow(fixture.input)).toBe(fixture.output);
    },
  );
});
