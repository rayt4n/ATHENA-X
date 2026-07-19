import { NextResponse } from "next/server";
import { getOrchestratorHealth } from "@/modules/provider-orchestrator/lib/orchestrator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** GET /api/providers/health — health status for all providers */
export async function GET() {
  const health = getOrchestratorHealth();
  return NextResponse.json(health);
}
