"use client";

import { useState, useRef, KeyboardEvent } from "react";

interface InputBarProps {
  onSubmit: (query: string, provider: string) => void;
  loading: boolean;
  onCancel: () => void;
  statusMessage: string;
  provider: string;
  onProviderChange: (provider: string) => void;
}

export default function InputBar({
  onSubmit,
  loading,
  onCancel,
  statusMessage,
  provider,
  onProviderChange,
}: InputBarProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSubmit(trimmed, provider);
    setQuery("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 px-6 pt-4 pointer-events-none">
      <div className="max-w-3xl mx-auto pointer-events-auto">
        {/* Status message */}
        {statusMessage && (
          <div className="mb-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 text-sm font-medium animate-pulse">
            {statusMessage}
          </div>
        )}

        {/* Input row */}
        <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-2xl shadow-lg px-4 py-3">
          <select
            value={provider}
            onChange={(e) => onProviderChange(e.target.value)}
            disabled={loading}
            className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700 outline-none"
          >
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="grok">Grok</option>
          </select>

          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder='Ask for a diagram, explanation, or architecture map…'
            disabled={loading}
            className="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400 text-sm disabled:opacity-50"
          />

          {loading ? (
            <button
              onClick={onCancel}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block" />
              Cancel
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!query.trim()}
              className="px-5 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Ask
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
