"use client";

import Link from "next/link";
import { Beaker, ExternalLink, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";

/**
 * Engineering Console Layout
 *
 * This layout is completely separate from the trader dashboard layout.
 * It applies the dark engineering cockpit theme and renders an isolated
 * navigation that is NOT reachable from any trader-facing surface.
 *
 * The trader dashboard at `/` has no link to `/engineering-console`.
 * Internal users reach this route via direct URL only.
 */
export default function EngineeringConsoleLayout({ children }: { children: React.ReactNode }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="dark min-h-screen bg-background text-foreground cockpit-grid">
      {/* Top banner — makes it crystal clear this is an internal tool */}
      <div className="border-b border-status-critical/30 bg-status-critical/5 px-4 py-1.5 flex items-center justify-between text-[10.5px] font-mono">
        <div className="flex items-center gap-2 text-status-critical">
          <Beaker className="h-3 w-3" />
          <span className="font-semibold uppercase tracking-wider">Internal Engineering Tool</span>
          <span className="text-muted-foreground">— not for trader use</span>
        </div>
        <div className="flex items-center gap-3 text-muted-foreground">
          <span>UTC+08 · SG · {new Date(now).toLocaleTimeString("en-US", { hour12: false })}</span>
          <Link
            href="/"
            className="flex items-center gap-1 hover:text-foreground transition-colors"
            title="Back to trader dashboard"
          >
            <span>exit to trader terminal</span>
            <ExternalLink className="h-2.5 w-2.5" />
          </Link>
        </div>
      </div>

      {children}
    </div>
  );
}
