"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function Panel({ title, subtitle, icon, actions, children, className, bodyClassName }: PanelProps) {
  return (
    <section
      className={cn(
        "flex flex-col rounded-lg border border-border/70 bg-card/60 backdrop-blur-sm overflow-hidden",
        "shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_8px_24px_-12px_rgba(0,0,0,0.6)]",
        className
      )}
    >
      <header className="flex items-center justify-between gap-3 border-b border-border/60 px-4 py-2.5 bg-card/40">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon && <span className="text-primary/80 shrink-0">{icon}</span>}
          <div className="min-w-0">
            <h3 className="text-[12px] font-semibold tracking-wide text-foreground uppercase truncate">{title}</h3>
            {subtitle && <p className="text-[10.5px] text-muted-foreground/80 truncate">{subtitle}</p>}
          </div>
        </div>
        {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
      </header>
      <div className={cn("flex-1 p-4 min-h-0", bodyClassName)}>{children}</div>
    </section>
  );
}

export function PanelGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid grid-cols-12 gap-3", className)}>{children}</div>;
}
