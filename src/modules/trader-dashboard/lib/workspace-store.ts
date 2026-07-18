/**
 * Workspace Store — persists workspace state to localStorage.
 *
 * In production this would be Supabase (per-user workspaces synced across
 * devices). For the trader dashboard MVP, localStorage is sufficient and
 * keeps the workspace state isolated per-browser.
 */

import type { Workspace, WorkspaceManagerState } from "./workspace-types";
import { buildBuiltinWorkspaces } from "./workspace-presets";
import { listModuleManifests, validateAllManifests } from "./workspace-registry";

const STORAGE_KEY = "athena-x-workspaces-v1";
const SCHEMA_VERSION = "1.0";

interface PersistedState {
  schemaVersion: string;
  workspaces: Workspace[];
  activeWorkspaceId: string;
  savedAt: number;
}

function buildDefaultState(): WorkspaceManagerState {
  const workspaces = buildBuiltinWorkspaces();
  return {
    workspaces,
    activeWorkspaceId: workspaces[0].id,
    registeredModules: listModuleManifests(),
    gridCols: 12,
    rowHeight: 32,
  };
}

export function loadWorkspaceState(): WorkspaceManagerState {
  // Validate manifests at load time
  const validation = validateAllManifests();
  if (!validation.ok) {
    console.warn("Module manifest validation failures:", validation.failures);
  }

  if (typeof window === "undefined") {
    return buildDefaultState();
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const defaultState = buildDefaultState();
      saveWorkspaceState(defaultState);
      return defaultState;
    }

    const persisted = JSON.parse(raw) as PersistedState;
    if (persisted.schemaVersion !== SCHEMA_VERSION) {
      // Schema changed — reset to defaults
      const defaultState = buildDefaultState();
      saveWorkspaceState(defaultState);
      return defaultState;
    }

    // Merge persisted custom workspaces with built-in presets
    const builtinWorkspaces = buildBuiltinWorkspaces();
    const customWorkspaces = persisted.workspaces.filter((w) => !w.builtin);

    // For builtin workspaces, always use the latest preset definition
    // (allows us to update presets in code without losing user customizations
    // to custom workspaces)
    const allWorkspaces = [...builtinWorkspaces, ...customWorkspaces];

    // Verify activeWorkspaceId still exists
    const activeId = allWorkspaces.find((w) => w.id === persisted.activeWorkspaceId)
      ? persisted.activeWorkspaceId
      : allWorkspaces[0].id;

    return {
      workspaces: allWorkspaces,
      activeWorkspaceId: activeId,
      registeredModules: listModuleManifests(),
      gridCols: 12,
      rowHeight: 32,
    };
  } catch (err) {
    console.warn("Failed to load workspace state, resetting:", err);
    const defaultState = buildDefaultState();
    saveWorkspaceState(defaultState);
    return defaultState;
  }
}

export function saveWorkspaceState(state: WorkspaceManagerState): void {
  if (typeof window === "undefined") return;

  const persisted: PersistedState = {
    schemaVersion: SCHEMA_VERSION,
    workspaces: state.workspaces,
    activeWorkspaceId: state.activeWorkspaceId,
    savedAt: Date.now(),
  };

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  } catch (err) {
    console.warn("Failed to save workspace state:", err);
  }
}

export function resetWorkspaceState(): WorkspaceManagerState {
  const defaultState = buildDefaultState();
  saveWorkspaceState(defaultState);
  return defaultState;
}

export { SCHEMA_VERSION as WORKSPACE_SCHEMA_VERSION };
