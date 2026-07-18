"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  LayoutItem,
  ModuleId,
  Workspace,
  WorkspaceManagerState,
  WorkspacePreset,
} from "@/modules/trader-dashboard/lib/workspace-types";
import { loadWorkspaceState, resetWorkspaceState, saveWorkspaceState } from "@/modules/trader-dashboard/lib/workspace-store";
import { getModuleManifest } from "@/modules/trader-dashboard/lib/workspace-registry";
import { buildBuiltinWorkspaces } from "@/modules/trader-dashboard/lib/workspace-presets";

/**
 * Workspace Manager hook — the single source of truth for workspace state.
 *
 * Operations:
 *   - switchWorkspace(id)      — switch to a saved layout
 *   - moveModule(instanceId, x, y)  — drag a module
 *   - resizeModule(instanceId, w, h) — resize a module
 *   - toggleModuleVisible(instanceId) — hide/show
 *   - detachModule(instanceId) — pop out to new window
 *   - addModule(moduleId)      — add a new module instance
 *   - removeModule(instanceId) — remove a module
 *   - updateModuleState(instanceId, partial) — update module's own state
 *   - updateWorkspaceSettings(partial) — update workspace-level settings
 *   - saveAsCustom(name)       — save current layout as a custom workspace
 *   - deleteWorkspace(id)      — delete a custom workspace (built-ins protected)
 *   - resetToDefaults()        — reset everything
 */

let instanceCounter = 0;
function genInstanceId(moduleId: string): string {
  instanceCounter += 1;
  return `${moduleId}-${instanceCounter}-${Date.now().toString(36)}`;
}

export function useWorkspace() {
  const [state, setState] = useState<WorkspaceManagerState>(() => loadWorkspaceState());
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced save to localStorage
  const scheduleSave = useCallback((newState: WorkspaceManagerState) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => saveWorkspaceState(newState), 300);
  }, []);

  useEffect(() => {
    scheduleSave(state);
  }, [state, scheduleSave]);

  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, []);

  const activeWorkspace = state.workspaces.find((w) => w.id === state.activeWorkspaceId) ?? state.workspaces[0];

  const switchWorkspace = useCallback((workspaceId: string) => {
    setState((prev) => {
      if (!prev.workspaces.find((w) => w.id === workspaceId)) return prev;
      return { ...prev, activeWorkspaceId: workspaceId };
    });
  }, []);

  const updateActiveWorkspace = useCallback((updater: (ws: Workspace) => Workspace) => {
    setState((prev) => ({
      ...prev,
      workspaces: prev.workspaces.map((w) =>
        w.id === prev.activeWorkspaceId ? { ...updater(w), updatedAt: Date.now() } : w
      ),
    }));
  }, []);

  const moveModule = useCallback((instanceId: string, x: number, y: number) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.map((item) =>
        item.instanceId === instanceId ? { ...item, x, y } : item
      ),
    }));
  }, [updateActiveWorkspace]);

  const resizeModule = useCallback((instanceId: string, w: number, h: number) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.map((item) => {
        if (item.instanceId !== instanceId) return item;
        const manifest = getModuleManifest(item.moduleId);
        const minW = manifest?.minSize.w ?? 1;
        const minH = manifest?.minSize.h ?? 1;
        const maxW = manifest?.maxSize?.w ?? state.gridCols;
        const maxH = manifest?.maxSize?.h ?? 100;
        return {
          ...item,
          w: Math.max(minW, Math.min(maxW, w)),
          h: Math.max(minH, Math.min(maxH, h)),
        };
      }),
    }));
  }, [updateActiveWorkspace, state.gridCols]);

  const toggleModuleVisible = useCallback((instanceId: string) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.map((item) =>
        item.instanceId === instanceId ? { ...item, visible: !item.visible } : item
      ),
    }));
  }, [updateActiveWorkspace]);

  const detachModule = useCallback((instanceId: string) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.map((item) =>
        item.instanceId === instanceId ? { ...item, detached: !item.detached } : item
      ),
    }));
  }, [updateActiveWorkspace]);

  const addModule = useCallback((moduleId: ModuleId) => {
    const manifest = getModuleManifest(moduleId);
    if (!manifest) return;

    updateActiveWorkspace((ws) => {
      const newItem: LayoutItem = {
        instanceId: genInstanceId(moduleId),
        moduleId,
        x: 0,
        y: Math.max(0, ...ws.items.map((i) => i.y + i.h)),
        w: manifest.defaultSize.w,
        h: manifest.defaultSize.h,
        visible: true,
        detached: false,
        state: {},
      };
      return { ...ws, items: [...ws.items, newItem] };
    });
  }, [updateActiveWorkspace]);

  const removeModule = useCallback((instanceId: string) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.filter((item) => item.instanceId !== instanceId),
    }));
  }, [updateActiveWorkspace]);

  const updateModuleState = useCallback((instanceId: string, partial: Record<string, unknown>) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      items: ws.items.map((item) =>
        item.instanceId === instanceId
          ? { ...item, state: { ...item.state, ...partial } }
          : item
      ),
    }));
  }, [updateActiveWorkspace]);

  const updateWorkspaceSettings = useCallback((partial: Partial<Workspace["settings"]>) => {
    updateActiveWorkspace((ws) => ({
      ...ws,
      settings: { ...ws.settings, ...partial },
    }));
  }, [updateActiveWorkspace]);

  const saveAsCustom = useCallback((name: string) => {
    setState((prev) => {
      const current = prev.workspaces.find((w) => w.id === prev.activeWorkspaceId);
      if (!current) return prev;
      const customWorkspace: Workspace = {
        ...current,
        id: `ws-custom-${Date.now().toString(36)}`,
        name,
        preset: "custom" as WorkspacePreset,
        builtin: false,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        items: current.items.map((item) => ({ ...item, instanceId: genInstanceId(item.moduleId) })),
      };
      return {
        ...prev,
        workspaces: [...prev.workspaces, customWorkspace],
        activeWorkspaceId: customWorkspace.id,
      };
    });
  }, []);

  const deleteWorkspace = useCallback((workspaceId: string) => {
    setState((prev) => {
      const ws = prev.workspaces.find((w) => w.id === workspaceId);
      if (!ws || ws.builtin) return prev; // can't delete builtins
      const remaining = prev.workspaces.filter((w) => w.id !== workspaceId);
      const activeId = prev.activeWorkspaceId === workspaceId ? remaining[0].id : prev.activeWorkspaceId;
      return { ...prev, workspaces: remaining, activeWorkspaceId: activeId };
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    const fresh = resetWorkspaceState();
    setState(fresh);
  }, []);

  return {
    state,
    activeWorkspace,
    switchWorkspace,
    moveModule,
    resizeModule,
    toggleModuleVisible,
    detachModule,
    addModule,
    removeModule,
    updateModuleState,
    updateWorkspaceSettings,
    saveAsCustom,
    deleteWorkspace,
    resetToDefaults,
  };
}
