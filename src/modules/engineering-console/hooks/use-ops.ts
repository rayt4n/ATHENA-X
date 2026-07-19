"use client";

import { useEffect, useRef, useState } from "react";
import { advanceOpsTelemetry, getOpsTelemetry, resetOpsTelemetry } from "@/modules/engineering-console/lib/ops-engine";
import type { OpsTelemetry } from "@/modules/engineering-console/lib/ops-types";

/**
 * Subscribes a component to the live ops telemetry stream.
 * New logs and traces arrive every tick — feels like a real ops console.
 */
export function useOps(intervalMs = 2000) {
  const [ops, setOps] = useState<OpsTelemetry>(() => getOpsTelemetry());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setOps(advanceOpsTelemetry());
    }, intervalMs);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [intervalMs]);

  const reset = () => setOps(resetOpsTelemetry());

  return { ops, reset };
}
