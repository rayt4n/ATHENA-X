import { NextResponse } from "next/server";
import { spawn } from "child_process";
import { mkdtemp, readFile, rm } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const GENERATOR_SCRIPT = "/home/z/my-project/scripts/audit/generate_certification_report.py";

/**
 * GET /api/certification-report
 *
 * Generates and returns the ATHENA-X Version 1 Production Certification
 * Report as a PDF. This is the final institutional go-live checklist.
 */
export async function GET() {
  const tmpDir = await mkdtemp(join(tmpdir(), "athena-cert-report-"));
  const outputPath = join(tmpDir, "athena-x-v1-production-certification.pdf");

  const result = await new Promise<{ ok: boolean; stderr: string }>((resolve) => {
    const proc = spawn("python3", [GENERATOR_SCRIPT, "--output", outputPath], {
      env: { ...process.env },
    });
    let stderr = "";
    proc.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    proc.on("error", (err) => resolve({ ok: false, stderr: `spawn error: ${err.message}\n${stderr}` }));
    proc.on("close", (code) => resolve({ ok: code === 0, stderr }));
  });

  if (!result.ok) {
    try { await rm(tmpDir, { recursive: true, force: true }); } catch {}
    return NextResponse.json({ error: "Report generation failed", detail: result.stderr.slice(-2000) }, { status: 500 });
  }

  const pdfBuffer = await readFile(outputPath);
  try { await rm(tmpDir, { recursive: true, force: true }); } catch {}

  return new NextResponse(pdfBuffer, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="athena-x-v1-production-certification.pdf"`,
      "Content-Length": pdfBuffer.length.toString(),
      "Cache-Control": "no-store, no-cache, must-revalidate",
    },
  });
}
