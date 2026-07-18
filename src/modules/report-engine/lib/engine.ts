/**
 * ATHENA-X Institutional Report Engine — Top-level orchestrator
 *
 * The engine is READ-ONLY. It performs NO calculations — every value in
 * every report originates from validated canonical databases or one of
 * the seven DNA intelligence objects.
 *
 * Flow:
 *   ComposerInput → composeReport → buildAuditMetadata → saveReport
 *                                                       → generateMarkdown
 *                                                       → generateJson
 *                                                       → generatePdf (on demand)
 *                                                       → event bus publish
 */

import { composeReport, telemetryToComposerInput } from "./composer";
import { buildAuditMetadata } from "./audit";
import { markReportFailed, saveReport } from "./storage";
import { getManifest, validateAllManifests } from "./registry";
import type {
  GenerateReportRequest,
  GenerateReportResult,
  ReportContent,
  StoredReport,
} from "./types";
import type { DashboardTelemetry } from "@/modules/engineering-console/lib/types";

export interface EngineContext {
  telemetry: DashboardTelemetry;
  platform: {
    buildHash: string;
    forecastVersion: string;
  };
}

/**
 * Generate a report. The engine reads from `ctx.telemetry` (which in
 * production would be the canonical DBs + DNA objects) and composes
 * a structured report. No calculations are performed.
 */
export function generateReport(
  request: GenerateReportRequest,
  ctx: EngineContext,
): GenerateReportResult {
  const t0 = Date.now();

  try {
    // Validate manifest exists
    const manifest = getManifest(request.type);
    if (!manifest) {
      throw new Error(`Unknown report type: ${request.type}`);
    }

    // Validate event subtype if applicable
    if (manifest.acceptsEventSubtype && request.eventSubtype === undefined) {
      throw new Error(`Report type ${request.type} requires an eventSubtype`);
    }

    // Build composer input from telemetry (READ-ONLY)
    const sessionDate = request.sessionDate ?? new Date().toISOString().slice(0, 10);
    const input = telemetryToComposerInput(ctx.telemetry, {
      sessionDate,
      eventSubtype: request.eventSubtype,
      workspace: "default",
      user: "system",
    });

    // Compose — no calculations, just format DNA + canonical into sections
    const content: ReportContent = composeReport(request.type, input);

    // Build audit metadata
    const audit = buildAuditMetadata(content, input, ctx.platform, {
      workspace: "default",
      user: "system",
    });

    // Save (also publishes report:created event)
    const report = saveReport(content, audit);

    return {
      report,
      success: true,
      durationMs: Date.now() - t0,
    };
  } catch (err) {
    markReportFailed(request, err instanceof Error ? err.message : String(err));
    return {
      report: null as unknown as StoredReport,
      success: false,
      error: err instanceof Error ? err.message : String(err),
      durationMs: Date.now() - t0,
    };
  }
}

/** Validate all registered manifests at engine startup. */
export function validateEngine(): { ok: boolean; failures: { type: string; errors: string[] }[] } {
  return validateAllManifests();
}

export { listReports, getReport, publishReport, getReportFormat, getReportStats, resetReportStore } from "./storage";
export { listManifests, getManifest, validateAllManifests, validateManifest } from "./registry";
export { getReportEventBus } from "./event-bus";
export { generateMarkdown } from "./generators/markdown";
export { generateJson } from "./generators/json";
export { hashContent, verifyIntegrity } from "./audit";
