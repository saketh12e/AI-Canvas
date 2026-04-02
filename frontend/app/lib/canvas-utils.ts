export interface ExcalidrawElement {
  id: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  // tldraw-native shapes store dimensions in props
  props?: { w?: number; h?: number; [key: string]: unknown };
  [key: string]: unknown;
}

/**
 * Returns the rightmost x coordinate across all existing elements.
 * Handles both tldraw-native shapes (props.w) and legacy shapes (width).
 */
export function getRightmostX(elements: ExcalidrawElement[]): number {
  if (elements.length === 0) return 0;
  return Math.max(
    ...elements.map((el) => (el.x ?? 0) + (el.props?.w ?? el.width ?? 0))
  );
}

/**
 * Returns the next base_x for a new cluster — rightmost + 100px gap.
 */
export function getNextBaseX(elements: ExcalidrawElement[]): number {
  const rightmost = getRightmostX(elements);
  return rightmost === 0 ? 0 : rightmost + 100;
}

/**
 * Merge new elements into existing ones, avoiding ID collisions.
 */
export function mergeElements(
  existing: ExcalidrawElement[],
  incoming: ExcalidrawElement[]
): ExcalidrawElement[] {
  const existingIds = new Set(existing.map((el) => el.id));
  const deduplicated = incoming.filter((el) => !existingIds.has(el.id));
  return [...existing, ...deduplicated];
}

/**
 * Generate a stable session ID for this browser session.
 * Persists in sessionStorage so refreshing the same tab reuses the same session.
 */
export function getOrCreateSessionId(): string {
  const key = "langcanvas_session_id";
  const existing =
    typeof window !== "undefined" ? sessionStorage.getItem(key) : null;
  if (existing) return existing;
  const id = crypto.randomUUID();
  if (typeof window !== "undefined") sessionStorage.setItem(key, id);
  return id;
}
