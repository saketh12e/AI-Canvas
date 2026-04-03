import { useCallback, useRef, useState } from "react";

export interface SSECallbacks {
  onPlanReady?: (data: {
    intent: string;
    visual_goal: string;
    canvas_title: string;
  }) => void;
  onResearchReady?: (
    sources: string[],
    sourceDetails: Array<{
      title: string;
      url: string;
      source_type: string;
    }>,
    connectors: string[],
    researchReport: {
      connectors_used?: string[];
      source_count?: number;
    }
  ) => void;
  onExplanationReady?: (data: {
    explanation: string;
    key_concepts: string[];
    code_example: string;
  }) => void;
  onCanvasReady?: (elements: unknown[], sessionId: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

export interface RuntimeKeysPayload {
  gemini_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  xai_api_key?: string;
  firecrawl_api_key?: string;
  tavily_api_key?: string;
}

export function useSSEStream() {
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(
    async (
      query: string,
      sessionId: string,
      baseX: number,
      baseY: number,
      provider: string,
      runtimeKeys: RuntimeKeysPayload,
      callbacks: SSECallbacks
    ) => {
      // Cancel any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);

      try {
        const response = await fetch("http://localhost:8000/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            session_id: sessionId,
            base_x: baseX,
            base_y: baseY,
            provider,
            runtime_keys: runtimeKeys,
          }),
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          callbacks.onError?.(`HTTP ${response.status}`);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          // Keep the last (possibly incomplete) line in the buffer
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);

              switch (event.type) {
                case "plan_ready":
                  callbacks.onPlanReady?.({
                    intent: event.intent ?? "",
                    visual_goal: event.visual_goal ?? "",
                    canvas_title: event.canvas_title ?? "",
                  });
                  break;
                case "research_ready":
                  callbacks.onResearchReady?.(
                    event.sources ?? [],
                    event.source_details ?? [],
                    event.connectors ?? [],
                    event.research_report ?? {}
                  );
                  break;
                case "explanation_ready":
                  callbacks.onExplanationReady?.({
                    explanation: event.explanation ?? "",
                    key_concepts: event.key_concepts ?? [],
                    code_example: event.code_example ?? "",
                  });
                  break;
                case "canvas_ready":
                  callbacks.onCanvasReady?.(
                    event.elements ?? [],
                    event.session_id ?? sessionId
                  );
                  break;
                case "done":
                  callbacks.onDone?.();
                  break;
                case "error":
                  callbacks.onError?.(event.message ?? "Unknown error");
                  break;
              }
            } catch {
              // Malformed JSON line — skip
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          callbacks.onError?.(err.message);
        }
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setLoading(false);
  }, []);

  return { stream, loading, cancel };
}
