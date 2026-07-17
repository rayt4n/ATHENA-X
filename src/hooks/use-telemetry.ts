"use client";

import { useEffect, useRef, useState } from "react";
import { advanceTelemetry, getTelemetry, resetTelemetry } from "@/lib/dashboard/mock-engine";
import type { DashboardTelemetry } from "@/lib/dashboard/types";

/**
 * Subscribes a component to the live telemetry stream.
 *
 * The mock engine ticks at the requested interval (default 1.5s, which feels
 * alive without thrashing the React reconciler). The returned object is
 * replaced on every tick — components should rely on referential equality
 * of nested arrays only within a single render pass.
 */
export function useTelemetry(intervalMs = 1500) {
  const [telemetry, setTelemetry] = useState<DashboardTelemetry>(() => getTelemetry());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTelemetry(advanceTelemetry());
    }, intervalMs);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [intervalMs]);

  const reset = () => setTelemetry(resetTelemetry());

  return { telemetry, reset };
}
