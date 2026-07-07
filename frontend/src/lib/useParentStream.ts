import { useCallback, useEffect, useMemo, useRef } from "react";

const DEFAULT_SSE_BASE = "";

interface ParentDeltaFrame {
  delta: string;
}

interface ParentDoneFrame {
  done: true;
}

type ParentFrame = ParentDeltaFrame | ParentDoneFrame;

export interface ParentStreamCallbacks {
  onChunk?: (accumulated: string, delta: string) => void;
  onDone?: (fullText: string) => void;
  onError?: (error: Event) => void;
}

export interface ParentStreamHandle {
  open: (sessionId: string) => void;
  close: () => void;
}

function parentStreamUrl(sessionId: string): string {
  const base = import.meta.env.VITE_SSE_BASE || DEFAULT_SSE_BASE;
  return `${base}/sse/parent/${sessionId}`;
}

function isDoneFrame(frame: ParentFrame): frame is ParentDoneFrame {
  return "done" in frame && frame.done === true;
}

export function useParentStream(callbacks: ParentStreamCallbacks): ParentStreamHandle {
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  const sourceRef = useRef<EventSource | null>(null);
  const accumulatedRef = useRef("");

  const close = useCallback(() => {
    if (sourceRef.current !== null) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
  }, []);

  const open = useCallback(
    (sessionId: string) => {
      close();
      accumulatedRef.current = "";

      const source = new EventSource(parentStreamUrl(sessionId), {
        withCredentials: true,
      });
      sourceRef.current = source;

      source.onmessage = (event: MessageEvent<string>) => {
        const frame = JSON.parse(event.data) as ParentFrame;
        if (isDoneFrame(frame)) {
          callbacksRef.current.onDone?.(accumulatedRef.current);
          close();
          return;
        }
        accumulatedRef.current += frame.delta;
        callbacksRef.current.onChunk?.(accumulatedRef.current, frame.delta);
      };

      source.onerror = (event: Event) => {
        callbacksRef.current.onError?.(event);
        close();
      };
    },
    [close],
  );

  useEffect(() => close, [close]);

  return useMemo(() => ({ open, close }), [open, close]);
}
