import { NextRequest, NextResponse } from "next/server";
import { getMode, setMode } from "@/modules/provider-orchestrator/lib/registry";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** GET /api/providers/mode — get current provider mode */
export async function GET() {
  return NextResponse.json({ mode: getMode() });
}

/** PUT /api/providers/mode — set provider mode */
export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    const mode = body.mode as "free" | "custom" | "advanced";
    if (!["free", "custom", "advanced"].includes(mode)) {
      return NextResponse.json({ error: "Invalid mode" }, { status: 400 });
    }
    setMode(mode);
    return NextResponse.json({ mode, success: true });
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }
}
