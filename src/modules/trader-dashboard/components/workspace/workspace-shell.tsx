"use client";

import { useState, type ReactNode } from "react";
import { Layout, Plus, Save, Trash2, RotateCcw, ChevronDown } from "lucide-react";
import type { ModuleId, Workspace } from "@/modules/trader-dashboard/lib/workspace-types";
import { listModuleManifests } from "@/modules/trader-dashboard/lib/workspace-registry";

interface WorkspaceShellProps {
  workspaces: Workspace[];
  activeWorkspace: Workspace;
  onSwitch: (id: string) => void;
  onAddModule: (moduleId: ModuleId) => void;
  onSaveAsCustom: (name: string) => void;
  onDeleteWorkspace: (id: string) => void;
  onReset: () => void;
  children: ReactNode;
}

export function WorkspaceShell({
  workspaces,
  activeWorkspace,
  onSwitch,
  onAddModule,
  onSaveAsCustom,
  onDeleteWorkspace,
  onReset,
  children,
}: WorkspaceShellProps) {
  const [showModuleMenu, setShowModuleMenu] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [customName, setCustomName] = useState("");
  const [showLayoutMenu, setShowLayoutMenu] = useState(false);

  const manifests = listModuleManifests();

  const handleSave = () => {
    if (customName.trim()) {
      onSaveAsCustom(customName.trim());
      setCustomName("");
      setShowSaveDialog(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Top bar — workspace switcher + actions */}
      <header className="border-b border-border bg-card/40 backdrop-blur-md shrink-0">
        <div className="px-4 py-2 flex items-center justify-between gap-4">
          {/* Left — branding + layout switcher */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/15 border border-primary/30">
                <Layout className="h-3.5 w-3.5 text-primary" />
              </div>
              <div className="hidden sm:block">
                <div className="text-[12px] font-semibold tracking-wide">ATHENA-X</div>
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground">Trader Terminal · Stage 16</div>
              </div>
            </div>

            {/* Layout switcher dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowLayoutMenu(!showLayoutMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border/60 hover:bg-accent/50 text-[11px] font-medium transition-colors"
              >
                <span className="text-muted-foreground">Layout:</span>
                <span>{activeWorkspace.name}</span>
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              </button>
              {showLayoutMenu && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowLayoutMenu(false)} />
                  <div className="absolute top-full left-0 mt-1 w-72 rounded-md border border-border bg-popover shadow-xl z-20 overflow-hidden">
                    <div className="px-3 py-2 border-b border-border/60 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-card/40">
                      Switch Workspace
                    </div>
                    <div className="max-h-80 overflow-y-auto scroll-thin">
                      {workspaces.map((ws) => (
                        <button
                          key={ws.id}
                          onClick={() => {
                            onSwitch(ws.id);
                            setShowLayoutMenu(false);
                          }}
                          className={`w-full text-left px-3 py-2 hover:bg-accent/40 transition-colors border-b border-border/30 ${ws.id === activeWorkspace.id ? "bg-primary/8" : ""}`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="min-w-0">
                              <div className="text-[11.5px] font-medium truncate">{ws.name}</div>
                              <div className="text-[9.5px] text-muted-foreground/70 truncate">
                                {ws.items.length} modules · {ws.items.filter((i) => i.visible).length} visible
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              {ws.builtin ? (
                                <span className="text-[8px] font-mono px-1 py-0.5 rounded bg-accent/40 text-muted-foreground/70 border border-border/30">BUILTIN</span>
                              ) : (
                                <span className="text-[8px] font-mono px-1 py-0.5 rounded bg-primary/15 text-primary border border-primary/30">CUSTOM</span>
                              )}
                              {ws.id === activeWorkspace.id && (
                                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                              )}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right — actions */}
          <div className="flex items-center gap-2">
            {/* Add module */}
            <div className="relative">
              <button
                onClick={() => setShowModuleMenu(!showModuleMenu)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-primary text-primary-foreground text-[11px] font-medium hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-3 w-3" />
                <span className="hidden sm:inline">Add Module</span>
              </button>
              {showModuleMenu && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowModuleMenu(false)} />
                  <div className="absolute top-full right-0 mt-1 w-72 rounded-md border border-border bg-popover shadow-xl z-20 overflow-hidden">
                    <div className="px-3 py-2 border-b border-border/60 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-card/40">
                      Add Module to Workspace
                    </div>
                    <div className="max-h-96 overflow-y-auto scroll-thin">
                      {manifests.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => {
                            onAddModule(m.id);
                            setShowModuleMenu(false);
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-accent/40 transition-colors border-b border-border/30"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="min-w-0">
                              <div className="text-[11.5px] font-medium truncate">{m.name}</div>
                              <div className="text-[9.5px] text-muted-foreground/70 truncate">{m.description}</div>
                            </div>
                            <span className="text-[8px] font-mono px-1 py-0.5 rounded bg-accent/40 text-muted-foreground/70 border border-border/30 shrink-0">
                              {m.category}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Save as custom */}
            <button
              onClick={() => setShowSaveDialog(true)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border/60 hover:bg-accent/50 text-[11px] font-medium transition-colors"
              title="Save current layout as custom workspace"
            >
              <Save className="h-3 w-3" />
              <span className="hidden sm:inline">Save As</span>
            </button>

            {/* Delete current (custom only) */}
            {!activeWorkspace.builtin && (
              <button
                onClick={() => onDeleteWorkspace(activeWorkspace.id)}
                className="p-1.5 rounded-md border border-border/60 hover:bg-status-critical/20 text-muted-foreground hover:text-status-critical transition-colors"
                title="Delete this custom workspace"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            )}

            {/* Reset */}
            <button
              onClick={() => {
                if (confirm("Reset all workspaces to defaults? Custom workspaces will be lost.")) {
                  onReset();
                }
              }}
              className="p-1.5 rounded-md border border-border/60 hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
              title="Reset to defaults"
            >
              <RotateCcw className="h-3 w-3" />
            </button>

            {/* Active symbol + timeframe indicator */}
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-background/40 border border-border/40 text-[10.5px] font-mono">
              <span className="text-primary font-semibold">{activeWorkspace.settings.selectedSymbol}</span>
              <span className="text-muted-foreground/50">·</span>
              <span className="text-muted-foreground">{activeWorkspace.settings.timeframe}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Workspace grid area */}
      <main className="flex-1 overflow-auto scroll-thin relative">
        {children}
      </main>

      {/* Save dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="rounded-lg border border-border bg-card p-6 w-80 shadow-xl">
            <div className="flex items-center gap-2 mb-3">
              <Save className="h-4 w-4 text-primary" />
              <h3 className="text-[13px] font-semibold">Save Workspace As</h3>
            </div>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="e.g. My Intraday Setup"
              className="w-full px-3 py-2 rounded-md bg-background border border-border text-[12px] focus:outline-none focus:border-primary/50"
              autoFocus
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
            />
            <div className="flex items-center gap-2 mt-4">
              <button
                onClick={handleSave}
                disabled={!customName.trim()}
                className="flex-1 px-3 py-2 rounded-md bg-primary text-primary-foreground text-[11px] font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => { setShowSaveDialog(false); setCustomName(""); }}
                className="px-3 py-2 rounded-md border border-border/60 hover:bg-accent/50 text-[11px] transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
