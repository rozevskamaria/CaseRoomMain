import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useParentStream } from "./useParentStream";

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  closed = false;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  close() {
    this.closed = true;
  }

  emit(data: string) {
    this.onmessage?.({ data } as MessageEvent<string>);
  }
}

beforeEach(() => {
  FakeEventSource.instances = [];
  vi.stubGlobal("EventSource", FakeEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useParentStream", () => {
  it("returns a stable handle across re-renders", () => {
    const { result, rerender } = renderHook(() => useParentStream({}));
    const first = result.current;
    rerender();
    rerender();
    expect(result.current).toBe(first);
    expect(result.current.open).toBe(first.open);
    expect(result.current.close).toBe(first.close);
  });

  it("opens one EventSource per open() and does not close it on re-render", () => {
    const { result, rerender } = renderHook(() => useParentStream({}));
    act(() => result.current.open("sid-1"));
    rerender();
    rerender();
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0].closed).toBe(false);
    expect(FakeEventSource.instances[0].url).toContain("/sse/parent/sid-1");
  });

  it("accumulates deltas and fires onDone with the full text, then closes", () => {
    const chunks: string[] = [];
    let done: string | null = null;
    const { result } = renderHook(() =>
      useParentStream({
        onChunk: (accumulated) => chunks.push(accumulated),
        onDone: (full) => {
          done = full;
        },
      }),
    );
    act(() => result.current.open("sid-2"));
    const source = FakeEventSource.instances[0];
    act(() => source.emit(JSON.stringify({ delta: "Hello " })));
    act(() => source.emit(JSON.stringify({ delta: "there." })));
    act(() => source.emit(JSON.stringify({ done: true })));
    expect(chunks).toEqual(["Hello ", "Hello there."]);
    expect(done).toBe("Hello there.");
    expect(source.closed).toBe(true);
  });
});
