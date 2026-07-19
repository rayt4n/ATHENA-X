import { NextRequest, NextResponse } from "next/server";
import { getProviders, getMode, getRoutingRules, setMode, addProvider, removeProvider, updateProvider, reorderProviders, resetToDefaults } from "@/modules/provider-orchestrator/lib/registry";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** GET /api/providers — list all providers and mode */
export async function GET() {
  return NextResponse.json({
    providers: getProviders(),
    mode: getMode(),
    routingRules: getRoutingRules(),
  });
}

/** POST /api/providers — add a custom provider (Custom/Advanced mode only) */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    if (getMode() === "free") {
      return NextResponse.json({ error: "Cannot add providers in Free mode" }, { status: 403 });
    }
    const provider = addProvider(body);
    return NextResponse.json({ provider, success: true });
  } catch (err) {
    return NextResponse.json({ error: "Invalid provider config", detail: String(err) }, { status: 400 });
  }
}

/** PUT /api/providers — update mode or reorder */
export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    if (body.mode) {
      setMode(body.mode);
    }
    if (body.reorder) {
      reorderProviders(body.reorder);
    }
    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ error: "Invalid update", detail: String(err) }, { status: 400 });
  }
}

/** DELETE /api/providers?id=xxx — remove a custom provider */
export async function DELETE(req: NextRequest) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (!id) return NextResponse.json({ error: "Missing id parameter" }, { status: 400 });
  if (getMode() === "free") {
    return NextResponse.json({ error: "Cannot remove providers in Free mode" }, { status: 403 });
  }
  removeProvider(id);
  return NextResponse.json({ success: true });
}
