import { NextRequest, NextResponse } from "next/server";
import { generateReport } from "@/modules/report-engine/lib/engine";
import { getTelemetry } from "@/modules/engineering-console/lib/mock-engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/reports/generate
 *
 * Same as POST /api/reports but explicitly named for clarity.
 * Generates a new report and returns the full stored report.
 */
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
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    // Auto-generate all 3 formats so they're available immediately
    return NextResponse.json({
      report: result.report,
      markdown: result.report.content.sections.map((s) => s.markdown).join("\n\n---\n\n"),
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
