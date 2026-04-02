"use client";

import { useRef, useEffect } from "react";
import { Tldraw } from "tldraw";
import "tldraw/tldraw.css";
import type { Editor } from "tldraw";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyElement = any;

// Keep the same imperative API shape as before so page.tsx needs minimal changes
export interface ExcalidrawAPI {
  updateScene: (scene: { elements: AnyElement[] }) => void;
  scrollToContent: (elements?: AnyElement[], opts?: unknown) => void;
}

interface CanvasProps {
  elements: AnyElement[];
  onElementsChange: (elements: AnyElement[]) => void;
  onApiReady?: (api: ExcalidrawAPI) => void;
}

export default function Canvas({ elements, onElementsChange, onApiReady }: CanvasProps) {
  // Store editor in a ref — NOT useState — so updates never trigger re-renders
  const editorRef = useRef<Editor | null>(null);
  // Track which shape IDs have been sent to tldraw to avoid re-adding
  const addedIdsRef = useRef<Set<string>>(new Set());

  // When elements prop updates (SSE delivers new tldraw shapes), add only the new ones
  useEffect(() => {
    if (!editorRef.current || elements.length === 0) return;
    const newEls = elements.filter(
      (el: AnyElement) => el?.id && !addedIdsRef.current.has(el.id)
    );
    if (newEls.length === 0) return;
    // Shapes are already in tldraw-native format — pass directly
    editorRef.current.createShapes(newEls);
    setTimeout(
      () => editorRef.current?.zoomToFit({ animation: { duration: 300 } }),
      100
    );
    newEls.forEach((el: AnyElement) => addedIdsRef.current.add(el.id));
  }, [elements]);

  return (
    <div className="w-full h-full">
      <Tldraw
        onMount={(editor: Editor) => {
          // Store in ref — NOT state
          editorRef.current = editor;

          // Expose the same imperative API the parent expects
          onApiReady?.({
            updateScene: ({ elements: els }) => {
              const newEls = (els as AnyElement[]).filter(
                (el) => el?.id && !addedIdsRef.current.has(el.id)
              );
              if (newEls.length) {
                editor.createShapes(newEls);
                newEls.forEach((el) => addedIdsRef.current.add(el.id));
              }
            },
            scrollToContent: () => {
              editor.zoomToFit({ animation: { duration: 300 } });
            },
          });

          // Debounced save: propagate user-driven canvas changes to parent
          editor.store.listen(
            () => {
              onElementsChange(editor.getCurrentPageShapes() as unknown as AnyElement[]);
            },
            { source: "user", scope: "document" }
          );
        }}
      />
    </div>
  );
}
