"use client";

import { useMemo } from "react";

export interface RuntimeKeys {
  gemini_api_key: string;
  openai_api_key: string;
  anthropic_api_key: string;
  xai_api_key: string;
  firecrawl_api_key: string;
  tavily_api_key: string;
  github_token: string;
}

interface SettingsPanelProps {
  open: boolean;
  runtimeKeys: RuntimeKeys;
  onClose: () => void;
  onRuntimeKeyChange: (key: keyof RuntimeKeys, value: string) => void;
}

const FIELD_LABELS: Array<{ key: keyof RuntimeKeys; label: string; placeholder: string }> = [
  { key: "gemini_api_key", label: "Gemini API Key", placeholder: "AIza..." },
  { key: "openai_api_key", label: "OpenAI API Key", placeholder: "sk-..." },
  { key: "anthropic_api_key", label: "Anthropic API Key", placeholder: "sk-ant-..." },
  { key: "xai_api_key", label: "Grok / xAI API Key", placeholder: "xai-..." },
  { key: "github_token", label: "GitHub Token", placeholder: "ghp_..." },
  { key: "firecrawl_api_key", label: "Firecrawl API Key", placeholder: "fc-..." },
  { key: "tavily_api_key", label: "Tavily API Key", placeholder: "tvly-..." },
];

function maskValue(value: string) {
  if (!value) return "Not set";
  if (value.length <= 8) return "Saved locally";
  return `${value.slice(0, 4)}••••${value.slice(-4)}`;
}

export default function SettingsPanel({
  open,
  runtimeKeys,
  onClose,
  onRuntimeKeyChange,
}: SettingsPanelProps) {
  const filledCount = useMemo(
    () => Object.values(runtimeKeys).filter(Boolean).length,
    [runtimeKeys]
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-slate-900/25 backdrop-blur-sm flex items-start justify-center px-4 pt-24">
      <div className="w-full max-w-3xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Runtime Settings</h2>
            <p className="text-sm text-slate-500">
              Store BYOK values in this browser only. {filledCount} key{filledCount === 1 ? "" : "s"} saved locally.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
          >
            Close
          </button>
        </div>

        <div className="grid gap-4 p-6 md:grid-cols-2">
          {FIELD_LABELS.map((field) => (
            <label key={field.key} className="block space-y-2">
              <span className="block text-sm font-medium text-slate-700">
                {field.label}
              </span>
              <input
                type="password"
                value={runtimeKeys[field.key]}
                onChange={(e) => onRuntimeKeyChange(field.key, e.target.value)}
                placeholder={field.placeholder}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-sky-300 focus:bg-white"
              />
              <span className="block text-xs text-slate-400">
                {maskValue(runtimeKeys[field.key])}
              </span>
            </label>
          ))}
        </div>

        <div className="border-t border-slate-100 bg-slate-50 px-6 py-4 text-xs text-slate-500">
          Keys stay in localStorage and are sent only with your requests from this browser. Nothing is committed to the repo.
        </div>
      </div>
    </div>
  );
}
