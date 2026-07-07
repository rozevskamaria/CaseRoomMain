import { describe, expect, it } from "vitest";
import {
  editorReducer,
  emptyEditorState,
  type EditorState,
} from "./caseEditorState";

function seeded(): EditorState {
  const state = emptyEditorState();
  state.versionId = "v-1";
  state.slug = "xla";
  state.byLang.en.title = "A Boy Who Is Always Getting Pneumonia";
  state.byLang.en.patient = "Tom, 4 years";
  state.byLang.en.redFlags = ["recurrent pneumonia", "absent tonsils"];
  state.byLang.en.wrongPaths = [{ key: "cf", value: "Consider cystic fibrosis" }];
  return state;
}

describe("editorReducer", () => {
  it("sets scalars and marks dirty", () => {
    const next = editorReducer(emptyEditorState(), {
      type: "SET_SCALAR",
      field: "difficulty",
      value: "adv",
    });
    expect(next.scalars.difficulty).toBe("adv");
    expect(next.dirty).toBe(true);
  });

  it("sets a per-language prose field without touching the other language", () => {
    const next = editorReducer(seeded(), {
      type: "SET_PROSE",
      lang: "lv",
      field: "title",
      value: "Zēns, kuram vienmēr ir pneimonija",
    });
    expect(next.byLang.lv.title).toBe("Zēns, kuram vienmēr ir pneimonija");
    expect(next.byLang.en.title).toBe("A Boy Who Is Always Getting Pneumonia");
  });

  it("adds, edits and removes list items", () => {
    let state = editorReducer(seeded(), {
      type: "ADD_LIST_ITEM",
      lang: "en",
      field: "keyClues",
    });
    expect(state.byLang.en.keyClues).toHaveLength(1);
    state = editorReducer(state, {
      type: "SET_LIST_ITEM",
      lang: "en",
      field: "keyClues",
      index: 0,
      value: "low IgG",
    });
    expect(state.byLang.en.keyClues[0]).toBe("low IgG");
    state = editorReducer(state, {
      type: "REMOVE_LIST_ITEM",
      lang: "en",
      field: "keyClues",
      index: 0,
    });
    expect(state.byLang.en.keyClues).toHaveLength(0);
  });

  it("manages lab rows: add, set key/kind/result, remove", () => {
    let state = editorReducer(emptyEditorState(), { type: "ADD_LAB_ROW" });
    expect(state.labRows).toHaveLength(1);
    state = editorReducer(state, { type: "SET_LAB_KEY", index: 0, value: "CBC" });
    state = editorReducer(state, { type: "SET_LAB_KIND", index: 0, value: "imaging" });
    state = editorReducer(state, {
      type: "SET_LAB_RESULT",
      index: 0,
      lang: "en",
      value: "Lymphocytes: 0.4 ↓",
    });
    expect(state.labRows[0]).toMatchObject({
      key: "CBC",
      kind: "imaging",
      resultByLang: { en: "Lymphocytes: 0.4 ↓", lv: "" },
    });
    state = editorReducer(state, { type: "REMOVE_LAB_ROW", index: 0 });
    expect(state.labRows).toHaveLength(0);
  });

  it("Copy from EN copies EN content verbatim into LV (deep, independent)", () => {
    const next = editorReducer(seeded(), { type: "COPY_FROM_EN" });
    expect(next.byLang.lv.title).toBe(next.byLang.en.title);
    expect(next.byLang.lv.redFlags).toEqual(next.byLang.en.redFlags);
    expect(next.byLang.lv.wrongPaths).toEqual(next.byLang.en.wrongPaths);
    expect(next.byLang.lv.redFlags).not.toBe(next.byLang.en.redFlags);

    const mutated = editorReducer(next, {
      type: "SET_PROSE",
      lang: "lv",
      field: "title",
      value: "changed",
    });
    expect(mutated.byLang.en.title).toBe("A Boy Who Is Always Getting Pneumonia");
  });

  it("HYDRATE replaces state and clears dirty; MARK_SAVED clears dirty", () => {
    const dirtyState = editorReducer(seeded(), {
      type: "SET_SCALAR",
      field: "iuis",
      value: "I",
    });
    expect(dirtyState.dirty).toBe(true);
    const saved = editorReducer(dirtyState, { type: "MARK_SAVED" });
    expect(saved.dirty).toBe(false);
  });
});
