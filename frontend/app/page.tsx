"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import InputBar from "./components/InputBar";
import SettingsPanel, { type RuntimeKeys } from "./components/SettingsPanel";
import SessionSidebar from "./components/SessionSidebar";
import Canvas from "./components/Canvas";
import { useSSEStream, type RuntimeKeysPayload } from "./lib/sse";
import {
  mergeElements,
  getNextCanvasPlacement,
  type ExcalidrawElement,
} from "./lib/canvas-utils";
import type { ExcalidrawAPI } from "./components/Canvas";

interface SourcePreview {
  title: string;
  url: string;
  source_type: string;
}

interface RuntimeCapability {
  key: string;
  label: string;
  available: boolean;
  reason: string;
}

interface ExplanationPreview {
  query: string;
  explanation: string;
  key_concepts: string[];
  timestamp: number;
  provider: string;
  sources: SourcePreview[];
}

export default function Home() {
  // elements holds the SSE/Supabase Excalidraw-format elements.
  // Canvas reads this prop and adds new shapes to tldraw reactively.
  const [elements, setElements] = useState<ExcalidrawElement[]>([]);
  const [history, setHistory] = useState<ExplanationPreview[]>([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [providerCapabilities, setProviderCapabilities] = useState<
    RuntimeCapability[]
  >([]);
  const [connectorCapabilities, setConnectorCapabilities] = useState<
    RuntimeCapability[]
  >([]);
  const [runtimeKeys, setRuntimeKeys] = useState<RuntimeKeys>({
    gemini_api_key: "",
    openai_api_key: "",
    anthropic_api_key: "",
    xai_api_key: "",
    github_token: "",
    firecrawl_api_key: "",
    tavily_api_key: "",
  });

  useEffect(() => {
    const stored = localStorage.getItem("langcanvas_session_id");
    const storedProvider = localStorage.getItem("langcanvas_provider");
    const storedRuntimeKeys = localStorage.getItem("langcanvas_runtime_keys");
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
    if (storedRuntimeKeys) {
      try {
        setRuntimeKeys((prev) => ({
          ...prev,
          ...(JSON.parse(storedRuntimeKeys) as RuntimeKeys),
        }));
      } catch {}
    }
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/runtime/capabilities")
      .then((r) => r.json())
      .then((data) => {
        setProviderCapabilities(data.providers ?? []);
        setConnectorCapabilities(data.connectors ?? []);
      })
      .catch(() => {});
  }, []);

  const canvasApiRef = useRef<ExcalidrawAPI | null>(null);
  const pendingElementsRef = useRef<ExcalidrawElement[] | null>(null);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingSourcesRef = useRef<SourcePreview[]>([]);
  const { stream, loading, cancel } = useSSEStream();

  const effectiveProviderCapabilities = useMemo(() => {
    const runtimePresence: Record<string, boolean> = {
      gemini: Boolean(runtimeKeys.gemini_api_key),
      openai: Boolean(runtimeKeys.openai_api_key),
      anthropic: Boolean(runtimeKeys.anthropic_api_key),
      grok: Boolean(runtimeKeys.xai_api_key),
    };

    return providerCapabilities.map((item) => {
      const available = item.available || runtimePresence[item.key];
      return {
        ...item,
        available,
        reason: available ? "Configured in browser settings or .env" : item.reason,
      };
    });
  }, [providerCapabilities, runtimeKeys]);

  const effectiveConnectorCapabilities = useMemo(() => {
    const runtimePresence: Record<string, boolean> = {
      firecrawl: Boolean(runtimeKeys.firecrawl_api_key),
      tavily: Boolean(runtimeKeys.tavily_api_key),
      github: Boolean(runtimeKeys.github_token),
      context7: true,
      mcpdoc: true,
    };

    return connectorCapabilities.map((item) => {
      const available = item.available || runtimePresence[item.key];
      return {
        ...item,
        available,
        reason: available ? "Available in browser settings or server config" : item.reason,
      };
    });
  }, [connectorCapabilities, runtimeKeys]);

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
      const effectiveProviderReady =
        effectiveProviderCapabilities.find((item) => item.key === provider)?.available ||
        Boolean(
          runtimeKeys[
            (
              {
                gemini: "gemini_api_key",
                openai: "openai_api_key",
                anthropic: "anthropic_api_key",
                grok: "xai_api_key",
              } as const
            )[provider as "gemini" | "openai" | "anthropic" | "grok"]
          ]
      );
      const selectedProviderCapability = effectiveProviderCapabilities.find(
        (item) => item.key === provider
      );
      if (selectedProviderCapability && !effectiveProviderReady) {
        setStatusMessage(
          `${selectedProviderCapability.label} is not configured yet. Add its API key in Settings or .env before testing.`
        );
        setTimeout(() => setStatusMessage(""), 4500);
        return;
      }
      const placement = getNextCanvasPlacement(elements);
      pendingSourcesRef.current = [];

      stream(
        query,
        sessionId,
        placement.baseX,
        placement.baseY,
        provider,
        runtimeKeys as RuntimeKeysPayload,
        {
        onPlanReady: (plan) => {
          setStatusMessage(
            `Planning a ${plan.visual_goal.replace("_", " ")} canvas…`
          );
        },
        onResearchReady: (sources, sourceDetails, connectors, researchReport) => {
          pendingSourcesRef.current = sourceDetails;
          const connectorsUsed = researchReport.connectors_used ?? connectors;
          const connectorLabel =
            connectorsUsed.length > 0
              ? ` via ${connectorsUsed.join(" + ")}`
              : "";
          setStatusMessage(
            sources.length > 0
              ? `Collected ${sources.length} source${sources.length === 1 ? "" : "s"}${connectorLabel}…`
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
              sources: pendingSourcesRef.current,
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
    [elements, effectiveProviderCapabilities, runtimeKeys, sessionId, stream]
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
        providerCapabilities={effectiveProviderCapabilities}
        connectorCapabilities={effectiveConnectorCapabilities}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <SettingsPanel
        open={settingsOpen}
        runtimeKeys={runtimeKeys}
        onClose={() => setSettingsOpen(false)}
        onRuntimeKeyChange={(key, value) => {
          const next = { ...runtimeKeys, [key]: value };
          setRuntimeKeys(next);
          localStorage.setItem("langcanvas_runtime_keys", JSON.stringify(next));
        }}
      />
    </main>
  );
}
