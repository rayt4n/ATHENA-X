import { NextRequest, NextResponse } from "next/server";
import { generateReport, listReports } from "@/modules/report-engine/lib/engine";
import { getTelemetry } from "@/modules/engineering-console/lib/mock-engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/reports
 * List all stored reports, optionally filtered by ?type= or ?sessionDate=
 *
 * POST /api/reports
 * Generate a new report. Body: { type, eventSubtype?, sessionDate? }
 */
export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const type = url.searchParams.get("type") as Parameters<typeof listReports>[0]["type"];
  const sessionDate = url.searchParams.get("sessionDate");
  const status = url.searchParams.get("status") as Parameters<typeof listReports>[0]["status"];

  const reports = listReports({ type: type ?? undefined, sessionDate: sessionDate ?? undefined, status: status ?? undefined });
  return NextResponse.json({ reports, count: reports.length });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { type, eventSubtype, sessionDate } = body;

    if (!type) {
      return NextResponse.json({ error: "Missing required field: type" }, { status: 400 });
    }

    const telemetry = getTelemetry();
    const result = generateReport(
      { type, eventSubtype, sessionDate },
      {
        telemetry,
        platform: {
          buildHash: "athx-15.0.0+sha.stage15",
          forecastVersion: "fc-ensemble-v11.2",
        },
      },
    );

    if (!result.success) {
      return NextResponse.json({ error: result.error, durationMs: result.durationMs }, { status: 500 });
    }

    return NextResponse.json({
      report: result.report,
      durationMs: result.durationMs,
      success: true,
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Internal server error", detail: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
