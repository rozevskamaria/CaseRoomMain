import { useEffect, useReducer, useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";
import { Button } from "../../../components/Button";
import { Callout } from "../../../components/Callout";
import { Card } from "../../../components/Card";
import { InfoBanner } from "../../../components/InfoBanner";
import { LabeledTextarea } from "../../../components/LabeledTextarea";
import { Pill } from "../../../components/Pill";
import { TabBar } from "../../../components/TabBar";
import { TextInput } from "../../../components/TextInput";
import {
  AuthorCasesQuery,
  CaseDraftQuery,
  DiscardCaseDraftMutation,
  PublishCaseVersionMutation,
  SetCaseDraftLabDataMutation,
  SetCaseDraftLocalizationMutation,
  SetCaseDraftScalarsMutation,
} from "../../../graphql/authoringOperations";
import { DashboardSpinner } from "../DashboardShell";
import { CaseLabDataEditor } from "./CaseLabDataEditor";
import { CasePreview } from "./CasePreview";
import {
  editorReducer,
  emptyEditorState,
  type EditorLang,
  type ListField,
} from "./caseEditorState";
import {
  hydrateEditorState,
  labTestsInput,
  localizationContent,
  type PlainCaseVersion,
} from "./caseEditorMapping";
import styles from "./CaseEditor.module.css";

export interface CaseEditorProps {
  versionId: string;
  canPublish: boolean;
  onDiscarded: () => void;
}

const DIFFICULTIES = ["beg", "int", "adv"];

export function CaseEditor({ versionId, canPublish, onDiscarded }: CaseEditorProps) {
  const { t } = useTranslation();
  const { data, loading } = useQuery(CaseDraftQuery, {
    variables: { versionId },
    fetchPolicy: "cache-and-network",
  });
  const [state, dispatch] = useReducer(editorReducer, undefined, emptyEditorState);
  const [langTab, setLangTab] = useState<EditorLang>("en");
  const [viewTab, setViewTab] = useState<"edit" | "preview">("edit");
  const [error, setError] = useState<string | null>(null);
  const [hydratedId, setHydratedId] = useState<string | null>(null);

  const draft = data?.caseDraft as PlainCaseVersion | null | undefined;

  useEffect(() => {
    if (draft && draft.versionId !== hydratedId) {
      dispatch({ type: "HYDRATE", state: hydrateEditorState(draft) });
      setHydratedId(draft.versionId);
    }
  }, [draft, hydratedId]);

  const [setScalars, scalarsState] = useMutation(SetCaseDraftScalarsMutation);
  const [setLocalization, localizationState] = useMutation(
    SetCaseDraftLocalizationMutation,
  );
  const [setLabData, labDataState] = useMutation(SetCaseDraftLabDataMutation);
  const [publish, publishState] = useMutation(PublishCaseVersionMutation, {
    refetchQueries: [{ query: AuthorCasesQuery }],
  });
  const [discard, discardState] = useMutation(DiscardCaseDraftMutation, {
    refetchQueries: [{ query: AuthorCasesQuery }],
  });

  const saving =
    scalarsState.loading || localizationState.loading || labDataState.loading;
  const isPublished = state.status === "published";

  if (loading && data === undefined) {
    return <DashboardSpinner />;
  }
  if (!draft) {
    return <Callout tone="amber">{t("dashboard.cases.editor.notFound")}</Callout>;
  }

  const onSave = async () => {
    setError(null);
    try {
      await setScalars({
        variables: {
          versionId,
          input: {
            difficulty: state.scalars.difficulty,
            targetDiagnosis: state.scalars.targetDiagnosis,
            iuis: state.scalars.iuis,
            topic: state.byLang.en.topic,
          },
        },
      });
      for (const lang of ["en", "lv"] as EditorLang[]) {
        await setLocalization({
          variables: {
            versionId,
            language: lang,
            content: localizationContent(state.byLang[lang], state.labRows, lang),
          },
        });
        await setLabData({
          variables: {
            input: {
              versionId,
              language: lang,
              tests: labTestsInput(state.labRows, lang),
            },
          },
        });
      }
      dispatch({ type: "MARK_SAVED" });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const onPublish = () => {
    setError(null);
    if (!window.confirm(t("dashboard.cases.editor.publishConfirm"))) return;
    void publish({ variables: { versionId } })
      .then((res) => {
        const next = res.data?.publishCaseVersion?.version;
        if (next) {
          dispatch({ type: "HYDRATE", state: hydrateEditorState(next as PlainCaseVersion) });
          setHydratedId(next.versionId);
        }
      })
      .catch((err: Error) => setError(err.message));
  };

  const onDiscard = () => {
    setError(null);
    if (!window.confirm(t("dashboard.cases.editor.discardConfirm"))) return;
    void discard({ variables: { versionId } })
      .then(() => onDiscarded())
      .catch((err: Error) => setError(err.message));
  };

  const lang = state.byLang[langTab];

  return (
    <div className={styles.editor}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>
            {state.byLang.en.title || state.slug || t("dashboard.cases.untitled")}
          </h2>
          <div className={styles.headMeta}>
            <Pill tone="count">
              {isPublished
                ? t("dashboard.cases.statusPublished")
                : t("dashboard.cases.statusDraft")}
            </Pill>
            <Pill tone="count">
              {t("dashboard.cases.versionLabel", { no: state.versionNo })}
            </Pill>
            {state.dirty && <Pill tone="count">{t("dashboard.cases.editor.unsaved")}</Pill>}
          </div>
        </div>
        <div className={styles.actions}>
          <Button variant="secondary" disabled={!state.dirty || saving || isPublished} onClick={() => void onSave()}>
            {saving ? t("dashboard.cases.editor.saving") : t("dashboard.cases.editor.save")}
          </Button>
          {canPublish && (
            <Button
              variant="primary"
              disabled={isPublished || publishState.loading || state.dirty}
              onClick={onPublish}
            >
              {t("dashboard.cases.editor.publish")}
            </Button>
          )}
          <Button variant="ghost" disabled={discardState.loading} onClick={onDiscard}>
            {t("dashboard.cases.editor.discard")}
          </Button>
        </div>
      </div>

      {isPublished && (
        <Callout tone="teal">{t("dashboard.cases.editor.publishedReadOnly")}</Callout>
      )}
      {error && <Callout tone="amber">{error}</Callout>}

      <TabBar
        tabs={[
          { key: "edit", label: t("dashboard.cases.editor.tabEdit") },
          { key: "preview", label: t("dashboard.cases.editor.tabPreview") },
        ]}
        active={viewTab}
        onChange={(key) => setViewTab(key as "edit" | "preview")}
      />

      {viewTab === "preview" ? (
        <CasePreview versionId={versionId} language={langTab} />
      ) : (
        <div className={styles.body}>
          <Card className={styles.scalarCard}>
            <div className={styles.sectionHeading}>
              {t("dashboard.cases.editor.scalarsHeading")}
            </div>
            <div className={styles.scalarRow}>
              <div className={styles.selectField}>
                <label className={styles.fieldLabel} htmlFor="case-difficulty">
                  {t("dashboard.cases.editor.difficulty")}
                </label>
                <select
                  id="case-difficulty"
                  className={styles.select}
                  value={state.scalars.difficulty}
                  onChange={(event) =>
                    dispatch({ type: "SET_SCALAR", field: "difficulty", value: event.target.value })
                  }
                >
                  <option value="">{t("dashboard.cases.editor.choose")}</option>
                  {DIFFICULTIES.map((d) => (
                    <option key={d} value={d}>
                      {t(`dashboard.cases.editor.difficulty_${d}`)}
                    </option>
                  ))}
                </select>
              </div>
              <TextInput
                label={t("dashboard.cases.editor.targetDiagnosis")}
                value={state.scalars.targetDiagnosis}
                onChange={(value) =>
                  dispatch({ type: "SET_SCALAR", field: "targetDiagnosis", value })
                }
                className={styles.flexField}
              />
              <TextInput
                label={t("dashboard.cases.editor.iuis")}
                value={state.scalars.iuis}
                onChange={(value) => dispatch({ type: "SET_SCALAR", field: "iuis", value })}
                className={styles.flexField}
              />
            </div>
          </Card>

          <TabBar
            tabs={[
              { key: "en", label: t("dashboard.cases.editor.langEn") },
              { key: "lv", label: t("dashboard.cases.editor.langLv") },
            ]}
            active={langTab}
            onChange={(key) => setLangTab(key as EditorLang)}
          />

          {langTab === "lv" && (
            <InfoBanner
              tone="navy"
              message={t("dashboard.cases.editor.lvUntranslated")}
              action={
                <Button variant="ghost" onClick={() => dispatch({ type: "COPY_FROM_EN" })}>
                  {t("dashboard.cases.editor.copyFromEn")}
                </Button>
              }
            />
          )}

          <Card className={styles.proseCard}>
            <TextInput
              label={t("dashboard.cases.editor.fieldTitle")}
              value={lang.title}
              onChange={(value) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "title", value })
              }
            />
            <TextInput
              label={t("dashboard.cases.editor.fieldTopic")}
              value={lang.topic}
              onChange={(value) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "topic", value })
              }
            />
            <TextInput
              label={t("dashboard.cases.editor.fieldPatient")}
              value={lang.patient}
              onChange={(value) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "patient", value })
              }
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldOpeningClinical")}
              value={lang.openingClinical}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "openingClinical", value: event.target.value })
              }
              rows={3}
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldOpening")}
              value={lang.opening}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "opening", value: event.target.value })
              }
              rows={3}
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldParentPrompt")}
              value={lang.parentPrompt}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "parentPrompt", value: event.target.value })
              }
              rows={12}
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldExamFindings")}
              value={lang.examFindings}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "examFindings", value: event.target.value })
              }
              rows={4}
            />
            <TextInput
              label={t("dashboard.cases.editor.fieldModelDiagnosis")}
              value={lang.modelDiagnosis}
              onChange={(value) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "modelDiagnosis", value })
              }
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldModelManagement")}
              value={lang.modelManagement}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "modelManagement", value: event.target.value })
              }
              rows={4}
            />
            <LabeledTextarea
              label={t("dashboard.cases.editor.fieldModelGenetic")}
              value={lang.modelGeneticCounselling}
              onChange={(event) =>
                dispatch({ type: "SET_PROSE", lang: langTab, field: "modelGeneticCounselling", value: event.target.value })
              }
              rows={4}
            />
          </Card>

          <Card className={styles.proseCard}>
            {(["redFlags", "keyClues"] as ListField[]).map((field) => (
              <div key={field} className={styles.listBlock}>
                <div className={styles.listHead}>
                  <div className={styles.fieldLabel}>
                    {t(`dashboard.cases.editor.field_${field}`)}
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => dispatch({ type: "ADD_LIST_ITEM", lang: langTab, field })}
                  >
                    {t("dashboard.cases.editor.addItem")}
                  </Button>
                </div>
                {lang[field].map((item, index) => (
                  <div key={index} className={styles.listRow}>
                    <TextInput
                      value={item}
                      onChange={(value) =>
                        dispatch({ type: "SET_LIST_ITEM", lang: langTab, field, index, value })
                      }
                      className={styles.flexField}
                    />
                    <Button
                      variant="ghost"
                      onClick={() =>
                        dispatch({ type: "REMOVE_LIST_ITEM", lang: langTab, field, index })
                      }
                    >
                      {t("dashboard.cases.editor.removeItem")}
                    </Button>
                  </div>
                ))}
              </div>
            ))}

            <div className={styles.listBlock}>
              <div className={styles.listHead}>
                <div className={styles.fieldLabel}>
                  {t("dashboard.cases.editor.fieldWrongPaths")}
                </div>
                <Button
                  variant="ghost"
                  onClick={() => dispatch({ type: "ADD_WRONG_PATH", lang: langTab })}
                >
                  {t("dashboard.cases.editor.addItem")}
                </Button>
              </div>
              {lang.wrongPaths.map((wp, index) => (
                <div key={index} className={styles.wrongPathRow}>
                  <TextInput
                    value={wp.key}
                    onChange={(value) =>
                      dispatch({ type: "SET_WRONG_PATH_KEY", lang: langTab, index, value })
                    }
                    placeholder={t("dashboard.cases.editor.wrongPathKey")}
                    className={styles.wrongPathKey}
                  />
                  <LabeledTextarea
                    label=""
                    value={wp.value}
                    onChange={(event) =>
                      dispatch({ type: "SET_WRONG_PATH_VALUE", lang: langTab, index, value: event.target.value })
                    }
                    rows={2}
                    className={styles.flexField}
                  />
                  <Button
                    variant="ghost"
                    onClick={() => dispatch({ type: "REMOVE_WRONG_PATH", lang: langTab, index })}
                  >
                    {t("dashboard.cases.editor.removeItem")}
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card className={styles.proseCard}>
            <CaseLabDataEditor rows={state.labRows} lang={langTab} dispatch={dispatch} />
          </Card>
        </div>
      )}
    </div>
  );
}
