import { NextResponse } from "next/server";
import { listManifests, validateAllManifests } from "@/modules/report-engine/lib/engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/report-templates
 *
 * Lists all registered report templates (manifests) and their validation status.
 */
export async function GET() {
  const manifests = listManifests();
  const validation = validateAllManifests();
  return NextResponse.json({
    templates: manifests,
    count: manifests.length,
    validation,
  });
}
