import { NextRequest, NextResponse } from "next/server";
import { getReport } from "@/modules/report-engine/lib/storage";
import { generateMarkdown } from "@/modules/report-engine/lib/generators/markdown";
import { generateJson } from "@/modules/report-engine/lib/generators/json";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/reports/[id]?format=markdown|json
 *
 * Returns a single report in the requested format.
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(req.url);
  const format = (url.searchParams.get("format") ?? "json") as "markdown" | "json";

  const report = getReport(id);
  if (!report) {
    return NextResponse.json({ error: "Report not found", id }, { status: 404 });
  }

  if (format === "markdown") {
    const md = generateMarkdown(report.content);
    return new NextResponse(md, {
      headers: {
        "Content-Type": "text/markdown; charset=utf-8",
        "Content-Disposition": `inline; filename="${report.content.id}.md"`,
      },
    });
  }

  const json = generateJson(report.content, report.audit);
  return new NextResponse(json, {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": `inline; filename="${report.content.id}.json"`,
    },
  });
}
