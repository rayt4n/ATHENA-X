import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { writeFile, mkdtemp, readFile, rm } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { getReport } from "@/modules/report-engine/lib/storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const GENERATOR_SCRIPT = "/home/z/my-project/scripts/report-engine/generate_report_pdf.py";

/**
 * GET /api/reports/[id]/pdf
 *
 * Generates and returns a PDF rendering of the report.
 */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  const report = getReport(id);
  if (!report) {
    return NextResponse.json({ error: "Report not found", id }, { status: 404 });
  }

  // Write the report payload (content + audit) to a temp file
  const tmpDir = await mkdtemp(join(tmpdir(), "athena-report-"));
  const inputPath = join(tmpDir, "input.json");
  const outputPath = join(tmpDir, "report.pdf");

  const payload = {
    content: report.content,
    audit: report.audit,
  };
  await writeFile(inputPath, JSON.stringify(payload), "utf-8");

  // Invoke Python generator
  const result = await new Promise<{ ok: boolean; stderr: string }>((resolve) => {
    const proc = spawn("python3", [GENERATOR_SCRIPT, "--input", inputPath, "--output", outputPath], {
      env: { ...process.env },
    });

    let stderr = "";
    proc.stderr.on("data", (chunk) => { stderr += chunk.toString(); });

    proc.on("error", (err) => {
      resolve({ ok: false, stderr: `spawn error: ${err.message}\n${stderr}` });
    });

    proc.on("close", (code) => {
      resolve({ ok: code === 0, stderr });
    });
  });

  if (!result.ok) {
    console.error("Report PDF generation failed:", result.stderr);
    try { await rm(tmpDir, { recursive: true, force: true }); } catch {}
    return NextResponse.json(
      { error: "PDF generation failed", detail: result.stderr.slice(-2000) },
      { status: 500 },
    );
  }

  const pdfBuffer = await readFile(outputPath);
  try { await rm(tmpDir, { recursive: true, force: true }); } catch {}

  return new NextResponse(pdfBuffer, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${report.content.id}.pdf"`,
      "Content-Length": pdfBuffer.length.toString(),
      "Cache-Control": "no-store, no-cache, must-revalidate",
    },
  });
}
