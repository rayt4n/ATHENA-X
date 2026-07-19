import { NextRequest, NextResponse } from "next/server";
import { getOrchestratorHealth, getRequestLog, getComparison } from "@/modules/provider-orchestrator/lib/orchestrator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** GET /api/providers/health — health status, request log, and comparison data */
export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const comparisonSymbol = url.searchParams.get("comparison");

  const health = getOrchestratorHealth();
  const requestLog = getRequestLog();
  const comparison = comparisonSymbol ? getComparison(comparisonSymbol) : null;

  return NextResponse.json({
    ...health,
    requestLog: requestLog.slice(0, 100),
    comparison,
  });
}
