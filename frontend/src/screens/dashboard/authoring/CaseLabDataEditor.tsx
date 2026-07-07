import type { Dispatch } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../../components/Button";
import { Card } from "../../../components/Card";
import { Callout } from "../../../components/Callout";
import { InfoBanner } from "../../../components/InfoBanner";
import { LabeledTextarea } from "../../../components/LabeledTextarea";
import { TextInput } from "../../../components/TextInput";
import {
  LAB_KINDS,
  type EditorAction,
  type EditorLang,
  type LabRow,
} from "./caseEditorState";
import styles from "./CaseLabDataEditor.module.css";

export interface CaseLabDataEditorProps {
  rows: LabRow[];
  lang: EditorLang;
  dispatch: Dispatch<EditorAction>;
}

function findDuplicates(rows: LabRow[]): Set<number> {
  const seen = new Map<string, number>();
  const dups = new Set<number>();
  rows.forEach((row, index) => {
    const key = row.key.trim();
    if (!key) return;
    const prev = seen.get(key);
    if (prev !== undefined) {
      dups.add(prev);
      dups.add(index);
    } else {
      seen.set(key, index);
    }
  });
  return dups;
}

export function CaseLabDataEditor({ rows, lang, dispatch }: CaseLabDataEditorProps) {
  const { t } = useTranslation();
  const dups = findDuplicates(rows);

  return (
    <div className={styles.editor}>
      <div className={styles.headRow}>
        <h3 className={styles.heading}>{t("dashboard.cases.lab.heading")}</h3>
        <Button variant="secondary" onClick={() => dispatch({ type: "ADD_LAB_ROW" })}>
          {t("dashboard.cases.lab.addRow")}
        </Button>
      </div>

      <Callout tone="teal">{t("dashboard.cases.lab.formatHint")}</Callout>

      {rows.length === 0 ? (
        <p className={styles.empty}>{t("dashboard.cases.lab.empty")}</p>
      ) : (
        <div className={styles.list}>
          {rows.map((row, index) => {
            const isDup = dups.has(index);
            const isEmpty = !row.key.trim();
            return (
              <Card key={index} className={styles.rowCard}>
                <div className={styles.rowHead}>
                  <TextInput
                    label={t("dashboard.cases.lab.nameLabel")}
                    value={row.key}
                    onChange={(value) =>
                      dispatch({ type: "SET_LAB_KEY", index, value })
                    }
                    placeholder={t("dashboard.cases.lab.namePlaceholder")}
                    className={styles.nameField}
                  />
                  <div className={styles.kindField}>
                    <label className={styles.kindLabel} htmlFor={`lab-kind-${index}`}>
                      {t("dashboard.cases.lab.kindLabel")}
                    </label>
                    <select
                      id={`lab-kind-${index}`}
                      className={styles.select}
                      value={row.kind}
                      onChange={(event) =>
                        dispatch({
                          type: "SET_LAB_KIND",
                          index,
                          value: event.target.value,
                        })
                      }
                    >
                      {LAB_KINDS.map((kind) => (
                        <option key={kind} value={kind}>
                          {t(`dashboard.cases.lab.kind.${kind}`)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      if (window.confirm(t("dashboard.cases.lab.removeConfirm"))) {
                        dispatch({ type: "REMOVE_LAB_ROW", index });
                      }
                    }}
                  >
                    {t("dashboard.cases.lab.remove")}
                  </Button>
                </div>
                {isEmpty && (
                  <InfoBanner
                    tone="navy"
                    message={t("dashboard.cases.lab.emptyNameWarning")}
                  />
                )}
                {isDup && (
                  <InfoBanner
                    tone="navy"
                    message={t("dashboard.cases.lab.duplicateNameWarning")}
                  />
                )}
                <LabeledTextarea
                  label={t("dashboard.cases.lab.resultLabel", {
                    lang: lang.toUpperCase(),
                  })}
                  value={row.resultByLang[lang]}
                  onChange={(event) =>
                    dispatch({
                      type: "SET_LAB_RESULT",
                      index,
                      lang,
                      value: event.target.value,
                    })
                  }
                  rows={5}
                  placeholder={t("dashboard.cases.lab.resultPlaceholder")}
                />
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
