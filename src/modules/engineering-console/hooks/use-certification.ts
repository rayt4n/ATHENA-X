"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { emptyCertificationState, runFullCertification } from "@/modules/engineering-console/lib/certification-engine";
import type { CertificationState } from "@/modules/engineering-console/lib/certification-types";
import type { DashboardTelemetry } from "@/modules/engineering-console/lib/types";

/**
 * Drives the Stage 14.5 certification flow.
 *
 * The runner simulates sequential module execution so the UI shows a
 * realistic progress bar. Each module completes with a small delay before
 * the next starts — the final state is computed in one pass by the
 * certification engine, but the staged reveal makes the certification
 * feel like a real audit run.
 */
export function useCertification(telemetry: DashboardTelemetry) {
  // Initialize with a one-shot certification run against the first telemetry snapshot.
  // Subsequent re-renders do not re-run unless the user explicitly clicks "Run".
  const [state, setState] = useState<CertificationState>(() => runFullCertification(telemetry));
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const run = useCallback(() => {
    setState((current) => {
      if (current.isRunning) return current;
      return {
        ...emptyCertificationState(),
        isRunning: true,
        currentModule: "data",
        startedAt: Date.now(),
        progress: 0.05,
      };
    });

    // Stage 1 — show "running" briefly, then compute the full result
    timerRef.current = setTimeout(() => {
      setState(runFullCertification(telemetry));
    }, 1800);
  }, [telemetry]);

  const reset = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setState(emptyCertificationState());
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { state, run, reset };
}
