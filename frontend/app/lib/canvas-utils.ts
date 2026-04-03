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

export interface CanvasPlacement {
  baseX: number;
  baseY: number;
}

const DEFAULT_CLUSTER_WIDTH = 1160;
const DEFAULT_CLUSTER_HEIGHT = 920;
const DEFAULT_GAP_X = 140;
const DEFAULT_GAP_Y = 180;
const DEFAULT_WRAP_WIDTH = 2800;

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
 * Returns the next placement for a new cluster.
 * The V2 layout wraps after the board becomes too wide instead of appending forever.
 */
export function getNextCanvasPlacement(
  elements: ExcalidrawElement[]
): CanvasPlacement {
  if (elements.length === 0) {
    return { baseX: 0, baseY: 0 };
  }

  const rightmost = getRightmostX(elements);
  const bottommost = Math.max(
    ...elements.map((el) => (el.y ?? 0) + (el.props?.h ?? el.height ?? 0))
  );

  const nextX = rightmost + DEFAULT_GAP_X;
  if (nextX + DEFAULT_CLUSTER_WIDTH <= DEFAULT_WRAP_WIDTH) {
    return { baseX: nextX, baseY: 0 };
  }

  return {
    baseX: 0,
    baseY: bottommost + DEFAULT_GAP_Y,
  };
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
