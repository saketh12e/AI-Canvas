"use client";

import { useState } from "react";

interface ExplanationPreview {
  query: string;
  explanation: string;
  key_concepts: string[];
  timestamp: number;
  provider: string;
}

interface SessionSidebarProps {
  history: ExplanationPreview[];
  sessionId: string;
}

export default function SessionSidebar({
  history,
  sessionId,
}: SessionSidebarProps) {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed top-20 left-4 z-50 bg-white border border-gray-200 rounded-xl shadow p-2 text-gray-500 hover:text-gray-800 transition-colors"
        title="Open history"
      >
        ☰
      </button>
    );
  }

  return (
    <aside className="fixed top-16 left-0 h-[calc(100%-4rem)] w-64 z-40 bg-white border-r border-gray-200 flex flex-col shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <span className="font-semibold text-gray-800 text-sm">LangCanvas</span>
        <button
          onClick={() => setOpen(false)}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none"
        >
          ×
        </button>
      </div>

      {/* Session ID badge */}
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
        <p className="text-xs text-gray-400 font-mono truncate">
          Session: {sessionId.slice(0, 8)}…
        </p>
      </div>

      {/* Query history */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {history.length === 0 && (
          <p className="text-xs text-gray-400 mt-4 text-center">
            Your queries will appear here
          </p>
        )}
        {[...history].reverse().map((item) => (
          <div
            key={item.timestamp}
            className="rounded-lg border border-gray-100 bg-gray-50 p-3 space-y-1"
          >
            <p className="text-xs font-semibold text-gray-700 truncate">
              {item.query}
            </p>
            <p className="text-xs text-gray-500 line-clamp-2">
              {item.explanation.slice(0, 120)}…
            </p>
            <p className="text-[10px] uppercase tracking-wide text-gray-400">
              {item.provider}
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {item.key_concepts.slice(0, 3).map((c) => (
                <span
                  key={c}
                  className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-medium"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-100">
        <p className="text-[10px] text-gray-300 text-center">
          AI canvas powered by LangGraph
        </p>
      </div>
    </aside>
  );
}
