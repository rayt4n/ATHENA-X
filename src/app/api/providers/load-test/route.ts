import { NextRequest, NextResponse } from "next/server";
import { startLoadTest, stopLoadTest, getLoadTestStatus, getLoadTestMetrics, evaluateCertification, DEFAULT_LOAD_CONFIG } from "@/modules/provider-orchestrator/lib/load-validator";
import { generateEvidenceReport } from "@/modules/provider-orchestrator/lib/evidence-report";
import type { LoadTestConfig } from "@/modules/provider-orchestrator/lib/load-validator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** GET /api/providers/load-test — get current load test status + metrics + certification + evidence report */
export async function GET(req: NextRequest) {
  const status = getLoadTestStatus();
  const metrics = getLoadTestMetrics();
  const durationHours = metrics ? (Date.now() - metrics.startedAt) / 3_600_000 : 0;
  const certification = evaluateCertification(metrics, durationHours);

  // Generate evidence report if we have metrics
  const evidence = metrics && metrics.totalRequests > 0
    ? generateEvidenceReport(metrics, certification, status.config?.providerId ?? "yahoo")
    : null;

  return NextResponse.json({
    isRunning: status.isRunning,
    config: status.config,
    metrics,
    certification,
    evidence,
  });
}

/** POST /api/providers/load-test — start a load test */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const config: LoadTestConfig = {
      symbols: body.symbols ?? DEFAULT_LOAD_CONFIG.symbols,
      categories: body.categories ?? DEFAULT_LOAD_CONFIG.categories,
      intervalMs: body.intervalMs ?? DEFAULT_LOAD_CONFIG.intervalMs,
      durationMin: body.durationMin ?? DEFAULT_LOAD_CONFIG.durationMin,
      providerId: body.providerId ?? DEFAULT_LOAD_CONFIG.providerId,
    };

    const result = startLoadTest(config);
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json({ error: "Failed to start load test", detail: String(err) }, { status: 500 });
  }
}

/** DELETE /api/providers/load-test — stop the load test */
export async function DELETE() {
  const result = stopLoadTest();
  return NextResponse.json(result);
}
