"use client";

import { useRef, useState, type ReactNode } from "react";
import { X, Minus, Square, ExternalLink, GripVertical, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LayoutItem } from "@/modules/trader-dashboard/lib/workspace-types";
import { getModuleManifest } from "@/modules/trader-dashboard/lib/workspace-registry";

interface ModuleFrameProps {
  item: LayoutItem;
  gridCols: number;
  rowHeight: number;
  onMove: (instanceId: string, x: number, y: number) => void;
  onResize: (instanceId: string, w: number, h: number) => void;
  onToggleVisible: (instanceId: string) => void;
  onDetach: (instanceId: string) => void;
  onRemove: (instanceId: string) => void;
  children: ReactNode;
}

/**
 * ModuleFrame — the draggable / resizable / hideable / detachable wrapper
 * around every workspace module. Renders a header with the module name and
 * window controls, then the module body.
 *
 * Dragging: grab the header to move the module. Snaps to grid.
 * Resizing: grab the bottom-right corner to resize. Snaps to grid.
 */
export function ModuleFrame({
  item,
  gridCols,
  rowHeight,
  onMove,
  onResize,
  onToggleVisible,
  onDetach,
  onRemove,
  children,
}: ModuleFrameProps) {
  const manifest = getModuleManifest(item.moduleId);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const dragStart = useRef<{ mouseX: number; mouseY: number; x: number; y: number } | null>(null);
  const resizeStart = useRef<{ mouseX: number; mouseY: number; w: number; h: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleDragStart = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    e.preventDefault();
    setIsDragging(true);
    dragStart.current = { mouseX: e.clientX, mouseY: e.clientY, x: item.x, y: item.y };

    const handleMove = (moveE: MouseEvent) => {
      if (!dragStart.current || !containerRef.current) return;
      const parent = containerRef.current.parentElement;
      if (!parent) return;
      const parentRect = parent.getBoundingClientRect();
      const colWidth = parentRect.width / gridCols;
      const deltaX = moveE.clientX - dragStart.current.mouseX;
      const deltaY = moveE.clientY - dragStart.current.mouseY;
      const newX = Math.max(0, Math.min(gridCols - item.w, dragStart.current.x + Math.round(deltaX / colWidth)));
      const newY = Math.max(0, dragStart.current.y + Math.round(deltaY / rowHeight));
      onMove(item.instanceId, newX, newY);
    };

    const handleUp = () => {
      setIsDragging(false);
      dragStart.current = null;
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleUp);
    };

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleUp);
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    resizeStart.current = { mouseX: e.clientX, mouseY: e.clientY, w: item.w, h: item.h };

    const handleMove = (moveE: MouseEvent) => {
      if (!resizeStart.current || !containerRef.current) return;
      const parent = containerRef.current.parentElement;
      if (!parent) return;
      const parentRect = parent.getBoundingClientRect();
      const colWidth = parentRect.width / gridCols;
      const deltaX = moveE.clientX - resizeStart.current.mouseX;
      const deltaY = moveE.clientY - resizeStart.current.mouseY;
      const newW = Math.max(1, Math.min(gridCols - item.x, resizeStart.current.w + Math.round(deltaX / colWidth)));
      const newH = Math.max(1, resizeStart.current.h + Math.round(deltaY / rowHeight));
      onResize(item.instanceId, newW, newH);
    };

    const handleUp = () => {
      setIsResizing(false);
      resizeStart.current = null;
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleUp);
    };

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleUp);
  };

  if (!manifest) return null;

  return (
    <div
      ref={containerRef}
      className={cn(
        "absolute rounded-lg border border-border bg-card/80 backdrop-blur-sm overflow-hidden flex flex-col",
        "shadow-[0_4px_12px_-4px_rgba(0,0,0,0.3)]",
        isDragging && "opacity-80 cursor-move z-50",
        isResizing && "z-50"
      )}
      style={{
        left: `${(item.x / gridCols) * 100}%`,
        top: `${item.y * rowHeight}px`,
        width: `${(item.w / gridCols) * 100}%`,
        height: `${item.h * rowHeight}px`,
      }}
    >
      {/* Header — draggable */}
      <header
        className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border bg-card/60 cursor-move select-none shrink-0"
        onMouseDown={handleDragStart}
      >
        <div className="flex items-center gap-2 min-w-0">
          <GripVertical className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
          <span className="text-[11px] font-semibold truncate">{manifest.name}</span>
          {item.detached && (
            <span className="text-[8.5px] font-mono px-1 py-0.5 rounded bg-status-info/15 text-status-info border border-status-info/30">
              DETACHED
            </span>
          )}
        </div>
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            onClick={() => onToggleVisible(item.instanceId)}
            className="p-1 rounded hover:bg-accent/60 text-muted-foreground hover:text-foreground transition-colors"
            title="Minimize"
          >
            <Minus className="h-3 w-3" />
          </button>
          {manifest.detachable && (
            <button
              onClick={() => onDetach(item.instanceId)}
              className="p-1 rounded hover:bg-accent/60 text-muted-foreground hover:text-foreground transition-colors"
              title="Detach"
            >
              <ExternalLink className="h-3 w-3" />
            </button>
          )}
          <button
            onClick={() => onRemove(item.instanceId)}
            className="p-1 rounded hover:bg-status-critical/20 text-muted-foreground hover:text-status-critical transition-colors"
            title="Remove"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      </header>

      {/* Body — module content */}
      <div className="flex-1 overflow-auto scroll-thin min-h-0">
        {children}
      </div>

      {/* Resize handle */}
      <div
        className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
        onMouseDown={handleResizeStart}
      >
        <div className="absolute bottom-1 right-1 w-2 h-2 border-r-2 border-b-2 border-muted-foreground/40" />
      </div>
    </div>
  );
}
