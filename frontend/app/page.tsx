"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import InputBar from "./components/InputBar";
import SessionSidebar from "./components/SessionSidebar";
import Canvas from "./components/Canvas";
import { useSSEStream } from "./lib/sse";
import {
  mergeElements,
  getNextBaseX,
  type ExcalidrawElement,
} from "./lib/canvas-utils";
import type { ExcalidrawAPI } from "./components/Canvas";

interface ExplanationPreview {
  query: string;
  explanation: string;
  key_concepts: string[];
  timestamp: number;
  provider: string;
}

export default function Home() {
  // elements holds the SSE/Supabase Excalidraw-format elements.
  // Canvas reads this prop and adds new shapes to tldraw reactively.
  const [elements, setElements] = useState<ExcalidrawElement[]>([]);
  const [history, setHistory] = useState<ExplanationPreview[]>([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState("gemini");

  useEffect(() => {
    const stored = localStorage.getItem("langcanvas_session_id");
    const storedProvider = localStorage.getItem("langcanvas_provider");
    if (stored) {
      setSessionId(stored);
    } else {
      const newId = crypto.randomUUID();
      localStorage.setItem("langcanvas_session_id", newId);
      setSessionId(newId);
    }
    if (storedProvider) {
      setSelectedProvider(storedProvider);
    }
  }, []);

  const canvasApiRef = useRef<ExcalidrawAPI | null>(null);
  // Holds Supabase-loaded elements if they arrive before the canvas API is ready
  const pendingElementsRef = useRef<ExcalidrawElement[] | null>(null);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { stream, loading, cancel } = useSSEStream();

  // Load saved canvas from Supabase once session ID is available
  useEffect(() => {
    if (!sessionId) return;
    fetch(`http://localhost:8000/sessions/${sessionId}/canvas`)
      .then((r) => r.json())
      .then((data) => {
        if (data.elements?.length > 0) {
          setElements(data.elements);
          if (canvasApiRef.current) {
            canvasApiRef.current.updateScene({ elements: data.elements });
          } else {
            pendingElementsRef.current = data.elements;
          }
        }
      })
      .catch(() => {});
  }, [sessionId]);

  // Save canvas to Supabase (debounced 2s after user stops editing).
  // Does NOT call setElements — tldraw shapes must not overwrite SSE elements state,
  // which would loop back into the canvas via the elements prop.
  const handleElementsChange = useCallback(
    (updated: ExcalidrawElement[]) => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        fetch(`http://localhost:8000/sessions/${sessionId}/canvas`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ elements: updated }),
        }).catch(() => {});
      }, 2000);
    },
    [sessionId]
  );

  const handleQuery = useCallback(
    (query: string, provider: string) => {
      if (!sessionId) return;
      const baseX = getNextBaseX(elements);
      const baseY = 0;

      stream(query, sessionId, baseX, baseY, provider, {
        onPlanReady: (plan) => {
          setStatusMessage(
            `Planning a ${plan.visual_goal.replace("_", " ")} canvas…`
          );
        },
        onResearchReady: (sources) => {
          setStatusMessage(
            sources.length > 0
              ? `Collected ${sources.length} source${sources.length === 1 ? "" : "s"}…`
              : "Gathering context…"
          );
        },
        onExplanationReady: (data) => {
          setStatusMessage("Designing the canvas scene…");
          setHistory((prev) => [
            ...prev,
            {
              query,
              explanation: data.explanation,
              key_concepts: data.key_concepts,
              timestamp: Date.now(),
              provider,
            },
          ]);
        },
        onCanvasReady: (newElements) => {
          setStatusMessage("Rendering on canvas…");
          setElements((prev) =>
            mergeElements(prev, newElements as ExcalidrawElement[])
          );
        },
        onDone: () => {
          setStatusMessage("");
        },
        onError: (msg) => {
          setStatusMessage(`Error: ${msg}`);
          setTimeout(() => setStatusMessage(""), 4000);
        },
      });
    },
    [elements, sessionId, stream]
  );

  return (
    <main className="w-screen h-screen overflow-hidden bg-gray-50 relative">
      <SessionSidebar history={history} sessionId={sessionId} />
      <div className="w-full h-full">
        <Canvas
          elements={elements}
          onElementsChange={handleElementsChange}
          onApiReady={(api) => {
            canvasApiRef.current = api;
            if (pendingElementsRef.current) {
              api.updateScene({ elements: pendingElementsRef.current });
              pendingElementsRef.current = null;
            }
          }}
        />
      </div>
      <InputBar
        onSubmit={handleQuery}
        loading={loading}
        onCancel={cancel}
        statusMessage={statusMessage}
        provider={selectedProvider}
        onProviderChange={(provider) => {
          setSelectedProvider(provider);
          localStorage.setItem("langcanvas_provider", provider);
        }}
      />
    </main>
  );
}
