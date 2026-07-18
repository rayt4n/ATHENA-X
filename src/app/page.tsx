"use client";

import { useWorkspace } from "@/modules/trader-dashboard/hooks/use-workspace";
import { WorkspaceShell } from "@/modules/trader-dashboard/components/workspace/workspace-shell";
import { ModuleFrame } from "@/modules/trader-dashboard/components/workspace/module-frame";
import { ModuleRenderer } from "@/modules/trader-dashboard/components/workspace/module-renderer";

/**
 * ATHENA-X Stage 16 — Trader Dashboard
 *
 * Workspace Manager architecture:
 *   - 10 module types, each with its own manifest (like plugins)
 *   - 6 built-in layouts (Pre-Market, Market Open, Intraday, Options, Research, Post-Market)
 *   - Modules are movable, resizable, hideable, detachable
 *   - Each module maintains its own state independently
 *   - Layouts persist to localStorage (Supabase-ready)
 *   - Custom layouts can be saved and deleted
 *
 * Switch contexts with one click — no manual rearranging.
 */
export default function Home() {
  const {
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
  } = useWorkspace();

  if (!activeWorkspace) {
    return <div className="h-screen flex items-center justify-center text-muted-foreground">No workspace loaded</div>;
  }

  const visibleItems = activeWorkspace.items.filter((item) => item.visible && !item.detached);
  const totalRows = Math.max(...activeWorkspace.items.map((i) => i.y + i.h), 20);
  const gridHeight = totalRows * state.rowHeight;

  return (
    <WorkspaceShell
      workspaces={state.workspaces}
      activeWorkspace={activeWorkspace}
      onSwitch={switchWorkspace}
      onAddModule={addModule}
      onSaveAsCustom={saveAsCustom}
      onDeleteWorkspace={deleteWorkspace}
      onReset={resetToDefaults}
    >
      {/* Grid layout area */}
      <div
        className="relative w-full"
        style={{ height: `${gridHeight}px`, minHeight: "100%" }}
      >
        {visibleItems.map((item) => (
          <ModuleFrame
            key={item.instanceId}
            item={item}
            gridCols={state.gridCols}
            rowHeight={state.rowHeight}
            onMove={moveModule}
            onResize={resizeModule}
            onToggleVisible={toggleModuleVisible}
            onDetach={detachModule}
            onRemove={removeModule}
          >
            <ModuleRenderer
              item={item}
              selectedSymbol={activeWorkspace.settings.selectedSymbol}
              timeframe={activeWorkspace.settings.timeframe}
              onSelectSymbol={(sym) => updateWorkspaceSettings({ selectedSymbol: sym })}
              onSelectTimeframe={(tf) => updateWorkspaceSettings({ timeframe: tf })}
              onModuleStateChange={updateModuleState}
            />
          </ModuleFrame>
        ))}

        {/* Empty state */}
        {visibleItems.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <div className="text-[14px] font-semibold mb-1">Empty Workspace</div>
            <div className="text-[12px] text-muted-foreground mb-4">Click "Add Module" in the top bar to add modules to this workspace.</div>
          </div>
        )}
      </div>
    </WorkspaceShell>
  );
}
