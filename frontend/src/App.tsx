import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useMutation, useQuery } from "@apollo/client";
import { SendBranch } from "./gql/graphql";
import {
  CaseQuery,
  GoToSummaryMutation,
  InterpretResultsMutation,
  OrderInvestigationsMutation,
  ReflectMutation,
  ProposeDifferentialsMutation,
  RequestExamMutation,
  RequestHintMutation,
  SendMessageMutation,
  SendTestOrderMutation,
  SessionQuery,
  SetDifferentialsMutation,
  SetFinalAnswerFieldMutation,
  SetInterpretationMutation,
  SetSummaryMutation,
  StartCaseMutation,
  SubmitDifferentialsMutation,
  SubmitFinalMutation,
  SubmitInterpretationMutation,
  SubmitReflectionMutation,
  SubmitSummaryMutation,
} from "./graphql/operations";
import { useParentStream } from "./lib/useParentStream";
import { ChatScreen } from "./screens/ChatScreen";
import { ReflectionDone } from "./screens/ReflectionDone";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import type {
  CaseMeta,
  ChatCallbacks,
  ChatUi,
  FinalAnswerField,
  Session,
  SessionMessage,
} from "./screens/types";
import { CASE_LIST } from "./content/caseList";
import { createInitialUiState, uiReducer } from "./state/uiState";

const SUMMARY_PROMPT =
  "Please write a clinical summary in 2–4 sentences: main problem, key history features, and your initial thinking about which immune compartment is affected.";
const DIFFERENTIALS_PROMPT =
  "Please state your top 2–3 differential diagnoses or immune defect categories. Consider which immune compartment is most likely affected.";
const INTERPRET_PROMPT =
  "You have gathered investigation results. Please interpret the key findings — which results are most important, and what do they tell you about the likely diagnosis?";
const FINAL_PROMPT = "Please now submit your final diagnosis and management plan.";

function pickRandomUnseen(seenCases: string[]): string | null {
  const unseen = CASE_LIST.filter((c) => !seenCases.includes(c.id));
  if (unseen.length === 0) return null;
  return unseen[Math.floor(Math.random() * unseen.length)].id;
}

function streamingMessage(text: string): SessionMessage {
  return { __typename: "MessageType", id: "__streaming__", type: "parent", text };
}

export default function App() {
  const [ui, dispatch] = useReducer(uiReducer, undefined, createInitialUiState);
  const [input, setInput] = useState("");
  const [streamText, setStreamText] = useState<string | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = ui.sessionId;

  const sessionQuery = useQuery(SessionQuery, {
    variables: { id: ui.sessionId ?? "" },
    skip: ui.sessionId === null,
    fetchPolicy: "cache-and-network",
  });
  const session = (sessionQuery.data?.session ?? null) as Session | null;

  const caseQuery = useQuery(CaseQuery, {
    variables: { id: ui.selectedCaseId ?? "" },
    skip: ui.selectedCaseId === null,
  });

  const refetchSession = useCallback(async () => {
    if (sessionIdRef.current === null) return;
    await sessionQuery.refetch({ id: sessionIdRef.current });
  }, [sessionQuery]);

  const [startCase] = useMutation(StartCaseMutation);
  const [sendMessage] = useMutation(SendMessageMutation);
  const [sendTestOrder] = useMutation(SendTestOrderMutation);
  const [requestExam] = useMutation(RequestExamMutation);
  const [setSummary] = useMutation(SetSummaryMutation);
  const [submitSummary] = useMutation(SubmitSummaryMutation);
  const [setDifferentials] = useMutation(SetDifferentialsMutation);
  const [submitDifferentials] = useMutation(SubmitDifferentialsMutation);
  const [setInterpretation] = useMutation(SetInterpretationMutation);
  const [submitInterpretation] = useMutation(SubmitInterpretationMutation);
  const [setFinalAnswerField] = useMutation(SetFinalAnswerFieldMutation);
  const [submitFinal] = useMutation(SubmitFinalMutation);
  const [requestHint] = useMutation(RequestHintMutation);
  const [submitReflection] = useMutation(SubmitReflectionMutation);
  const [goToSummary] = useMutation(GoToSummaryMutation);
  const [proposeDifferentials] = useMutation(ProposeDifferentialsMutation);
  const [interpretResults] = useMutation(InterpretResultsMutation);
  const [orderInvestigations] = useMutation(OrderInvestigationsMutation);
  const [reflect] = useMutation(ReflectMutation);

  const parentStream = useParentStream({
    onChunk: (accumulated) => setStreamText(accumulated),
    onDone: () => {
      setStreamText(null);
      dispatch({ type: "SET_BUSY", value: false });
      void refetchSession();
    },
    onError: () => {
      setStreamText(null);
      dispatch({ type: "SET_BUSY", value: false });
      void refetchSession();
    },
  });

  const runAsync = useCallback(
    async (work: () => Promise<void>) => {
      dispatch({ type: "SET_BUSY", value: true });
      try {
        await work();
      } finally {
        dispatch({ type: "SET_BUSY", value: false });
      }
    },
    [],
  );

  const onStartCase = useCallback(
    (caseId: string, markSeen: boolean) => {
      void runAsync(async () => {
        if (markSeen) dispatch({ type: "MARK_CASE_SEEN", caseId });
        const result = await startCase({ variables: { caseId, mode: ui.mode } });
        const started = result.data?.startCase;
        dispatch({
          type: "START_CASE",
          caseId,
          sessionId: started?.id ?? null,
        });
        setInput("");
      });
    },
    [runAsync, startCase, ui.mode],
  );

  const onStartRandom = useCallback(() => {
    const caseId = pickRandomUnseen(ui.seenCases);
    if (caseId === null) return;
    onStartCase(caseId, true);
  }, [onStartCase, ui.seenCases]);

  const onSend = useCallback(() => {
    if (!input.trim() || ui.busy || ui.sessionId === null) return;
    const text = input;
    setInput("");
    void runAsync(async () => {
      const result = await sendMessage({
        variables: { sessionId: ui.sessionId as string, text },
      });
      const branch = result.data?.sendMessage.branch;
      if (branch === SendBranch.Parent) {
        dispatch({ type: "SET_BUSY", value: true });
        setStreamText("");
        parentStream.open(ui.sessionId as string);
        return;
      }
      await refetchSession();
    });
  }, [input, parentStream, refetchSession, runAsync, sendMessage, ui.busy, ui.sessionId]);

  const onOrderTests = useCallback(() => {
    if (!input.trim() || ui.sessionId === null) return;
    const text = input;
    setInput("");
    void runAsync(async () => {
      await sendTestOrder({ variables: { sessionId: ui.sessionId as string, text } });
      await refetchSession();
    });
  }, [input, refetchSession, runAsync, sendTestOrder, ui.sessionId]);

  const onRequestExam = useCallback(() => {
    if (ui.sessionId === null) return;
    void runAsync(async () => {
      await requestExam({ variables: { sessionId: ui.sessionId as string } });
      await refetchSession();
    });
  }, [refetchSession, requestExam, runAsync, ui.sessionId]);

  const onSetSummary = useCallback(
    (value: string) => {
      if (ui.sessionId === null) return;
      void setSummary({ variables: { sessionId: ui.sessionId, value } });
    },
    [setSummary, ui.sessionId],
  );

  const onSubmitSummary = useCallback(() => {
    if (ui.sessionId === null) return;
    void runAsync(async () => {
      await submitSummary({ variables: { sessionId: ui.sessionId as string } });
      dispatch({ type: "SET_INPUT_MODE", inputMode: "history" });
      await refetchSession();
    });
  }, [refetchSession, runAsync, submitSummary, ui.sessionId]);

  const onSetDifferentials = useCallback(
    (value: string) => {
      if (ui.sessionId === null) return;
      void setDifferentials({ variables: { sessionId: ui.sessionId, value } });
    },
    [setDifferentials, ui.sessionId],
  );

  const onSubmitDifferentials = useCallback(() => {
    if (ui.sessionId === null) return;
    void runAsync(async () => {
      await submitDifferentials({ variables: { sessionId: ui.sessionId as string } });
      dispatch({ type: "SET_INPUT_MODE", inputMode: "history" });
      await refetchSession();
    });
  }, [refetchSession, runAsync, submitDifferentials, ui.sessionId]);

  const onSetInterpText = useCallback(
    (value: string) => {
      if (ui.sessionId === null) return;
      void setInterpretation({ variables: { sessionId: ui.sessionId, value } });
    },
    [setInterpretation, ui.sessionId],
  );

  const onSubmitInterpretation = useCallback(() => {
    if (ui.sessionId === null) return;
    void runAsync(async () => {
      await submitInterpretation({ variables: { sessionId: ui.sessionId as string } });
      dispatch({ type: "SET_INPUT_MODE", inputMode: "history" });
      await refetchSession();
    });
  }, [refetchSession, runAsync, submitInterpretation, ui.sessionId]);

  const onSetFinalAnswerField = useCallback(
    (field: FinalAnswerField, value: string) => {
      if (ui.sessionId === null) return;
      void setFinalAnswerField({
        variables: { sessionId: ui.sessionId, fieldName: field, value },
      });
    },
    [setFinalAnswerField, ui.sessionId],
  );

  const onSubmitFinalAnswer = useCallback(() => {
    if (ui.sessionId === null) return;
    void runAsync(async () => {
      dispatch({ type: "SET_ACTIVE_TAB", tab: "consultation" });
      await submitFinal({
        variables: { sessionId: ui.sessionId as string, prompt: FINAL_PROMPT },
      });
      await refetchSession();
    });
  }, [refetchSession, runAsync, submitFinal, ui.sessionId]);

  const onGetHint = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "SET_SHOW_HINT_MENU", value: false });
    void runAsync(async () => {
      const result = await requestHint({
        variables: { sessionId: ui.sessionId as string },
      });
      dispatch({ type: "SET_HINT_POPUP", value: result.data?.requestHint ?? null });
      await refetchSession();
    });
  }, [refetchSession, requestHint, runAsync, ui.sessionId]);

  const onSubmitReflection = useCallback(() => {
    if (!input.trim() || ui.sessionId === null) return;
    const text = input;
    setInput("");
    void runAsync(async () => {
      const result = await submitReflection({
        variables: { sessionId: ui.sessionId as string, text },
      });
      const next = result.data?.submitReflection;
      await refetchSession();
      if (next && next.phase !== "reflection") {
        dispatch({ type: "REFLECTION_DONE" });
      }
    });
  }, [input, refetchSession, runAsync, submitReflection, ui.sessionId]);

  const onGoToSummary = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "ENTER_SUMMARY_INPUT" });
    void runAsync(async () => {
      await goToSummary({
        variables: { sessionId: ui.sessionId as string, prompt: SUMMARY_PROMPT },
      });
      await refetchSession();
    });
  }, [goToSummary, refetchSession, runAsync, ui.sessionId]);

  const onProposeDifferentials = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "ENTER_DIFF_INPUT" });
    void runAsync(async () => {
      await proposeDifferentials({
        variables: { sessionId: ui.sessionId as string, prompt: DIFFERENTIALS_PROMPT },
      });
      await refetchSession();
    });
  }, [proposeDifferentials, refetchSession, runAsync, ui.sessionId]);

  const onInterpretResults = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "ENTER_INTERP_INPUT" });
    dispatch({ type: "SET_ACTIVE_TAB", tab: "investigations" });
    void runAsync(async () => {
      await interpretResults({
        variables: { sessionId: ui.sessionId as string, prompt: INTERPRET_PROMPT },
      });
      await refetchSession();
    });
  }, [interpretResults, refetchSession, runAsync, ui.sessionId]);

  const onSubmitFinalTransition = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "OPEN_FINAL_FORM", tab: "diagnosis" });
    void runAsync(async () => {
      await submitFinal({
        variables: { sessionId: ui.sessionId as string, prompt: FINAL_PROMPT },
      });
      await refetchSession();
    });
  }, [refetchSession, runAsync, submitFinal, ui.sessionId]);

  const onOrderInvestigations = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "ENTER_INTERP_INPUT" });
    void runAsync(async () => {
      await orderInvestigations({ variables: { sessionId: ui.sessionId as string } });
      await refetchSession();
    });
  }, [orderInvestigations, refetchSession, runAsync, ui.sessionId]);

  const onExit = useCallback(() => {
    parentStream.close();
    setInput("");
    setStreamText(null);
    dispatch({ type: "RETURN_TO_WELCOME" });
  }, [parentStream]);

  const onReflect = useCallback(() => {
    if (ui.sessionId === null) return;
    dispatch({ type: "ENTER_REFLECTION" });
    void runAsync(async () => {
      await reflect({ variables: { sessionId: ui.sessionId as string } });
      await refetchSession();
    });
  }, [reflect, refetchSession, runAsync, ui.sessionId]);

  useEffect(() => () => parentStream.close(), [parentStream]);

  const chatUi: ChatUi = useMemo(
    () => ({
      mode: ui.mode,
      activeTab: ui.activeTab,
      inputMode: ui.inputMode,
      input,
      showHintMenu: ui.showHintMenu,
      hintPopup: ui.hintPopup,
      showFinalForm: ui.showFinalForm,
      busy: ui.busy,
    }),
    [
      input,
      ui.activeTab,
      ui.busy,
      ui.hintPopup,
      ui.inputMode,
      ui.mode,
      ui.showFinalForm,
      ui.showHintMenu,
    ],
  );

  const callbacks: ChatCallbacks = useMemo(
    () => ({
      onSend,
      onOrderTests,
      onRequestExam,
      onSubmitSummary,
      onSubmitDifferentials,
      onSubmitInterpretation,
      onSubmitFinalAnswer,
      onRequestHint: () => dispatch({ type: "SET_SHOW_HINT_MENU", value: true }),
      onGetHint,
      onSubmitReflection,
      onSetTab: (tab) => dispatch({ type: "SET_ACTIVE_TAB", tab }),
      onSetInputMode: (inputMode) => dispatch({ type: "SET_INPUT_MODE", inputMode }),
      onShowHintMenu: (open) => dispatch({ type: "SET_SHOW_HINT_MENU", value: open }),
      onCloseHintPopup: () => dispatch({ type: "SET_HINT_POPUP", value: null }),
      onShowFinalForm: (open) => dispatch({ type: "SET_SHOW_FINAL_FORM", value: open }),
      onExit,
      onSeeNext: onExit,
      onReflect,
      onBrowse: onExit,
      onSetInput: setInput,
      onSetSummary,
      onSetDifferentials,
      onSetInterpText,
      onSetFinalAnswerField,
      proposeDifferentials: onProposeDifferentials,
      interpretResults: onInterpretResults,
      submitFinal: onSubmitFinalTransition,
      orderInvestigations: onOrderInvestigations,
      goToSummary: onGoToSummary,
    }),
    [
      onExit,
      onGetHint,
      onGoToSummary,
      onInterpretResults,
      onOrderInvestigations,
      onOrderTests,
      onProposeDifferentials,
      onReflect,
      onRequestExam,
      onSend,
      onSetDifferentials,
      onSetFinalAnswerField,
      onSetInterpText,
      onSetSummary,
      onSubmitDifferentials,
      onSubmitFinalAnswer,
      onSubmitFinalTransition,
      onSubmitInterpretation,
      onSubmitReflection,
      onSubmitSummary,
    ],
  );

  if (ui.screen === "welcome") {
    const seenSet = new Set(ui.seenCases);
    const allDone = CASE_LIST.every((c) => seenSet.has(c.id));
    return (
      <WelcomeScreen
        mode={ui.mode}
        seenCases={ui.seenCases}
        allDone={allDone}
        showBrowse={ui.showBrowse}
        onSetMode={(mode) => dispatch({ type: "SET_MODE", mode })}
        onStartRandom={onStartRandom}
        onStartCase={(caseId) => onStartCase(caseId, false)}
        onToggleBrowse={() =>
          dispatch({ type: "SET_SHOW_BROWSE", value: !ui.showBrowse })
        }
        onResetProgress={() => dispatch({ type: "RESET_PROGRESS" })}
      />
    );
  }

  if (ui.screen === "reflection_done") {
    const tutorMsgs = session?.messages.filter((m) => m.type === "tutor") ?? [];
    const tutorText = tutorMsgs.length > 0 ? tutorMsgs[tutorMsgs.length - 1].text : "";
    return <ReflectionDone tutorText={tutorText} onReturn={onExit} />;
  }

  if (session === null) return null;

  const caseData = caseQuery.data?.case;
  const caseMeta: CaseMeta = caseData
    ? { title: caseData.title, patient: caseData.patient, topic: caseData.topic }
    : { title: "", patient: "", topic: "" };

  const renderSession: Session =
    streamText !== null
      ? { ...session, messages: [...session.messages, streamingMessage(streamText)] }
      : session;

  return (
    <ChatScreen
      session={renderSession}
      caseMeta={caseMeta}
      ui={chatUi}
      callbacks={callbacks}
    />
  );
}
