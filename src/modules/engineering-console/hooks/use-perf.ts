"use client";

import { useEffect, useState } from "react";
import { getPerfTelemetry, resetPerfTelemetry } from "@/modules/engineering-console/lib/perf-engine";
import type { PerfTelemetry } from "@/modules/engineering-console/lib/perf-types";

/**
 * Subscribes a component to the performance certification telemetry.
 * Stage 15.6 metrics don't tick as frequently as ops telemetry — they
 * represent certification results, not live probes — so we refresh
 * every 10s to simulate ongoing measurement.
 */
export function usePerf(intervalMs = 10000) {
  const [perf, setPerf] = useState<PerfTelemetry>(() => getPerfTelemetry());

  useEffect(() => {
    const t = setInterval(() => {
      // Re-read the (potentially updated) state
      setPerf({ ...getPerfTelemetry() });
    }, intervalMs);
    return () => clearInterval(t);
  }, [intervalMs]);

  const reset = () => setPerf(resetPerfTelemetry());

  return { perf, reset };
}
