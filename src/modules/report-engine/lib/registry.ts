/**
 * Report Definition Registry
 *
 * Loads and validates report manifests. Adding a new report type means
 * adding a new manifest file — the engine core never changes.
 */

import type { ReportManifest, ReportTypeId, SectionId } from "./types";
import { premarketManifest } from "../templates/premarket/manifest";
import { marketopenManifest } from "../templates/marketopen/manifest";
import { intradayManifest } from "../templates/intraday/manifest";
import { eventManifest } from "../templates/event/manifest";
import { endofdayManifest } from "../templates/endofday/manifest";
import { weeklyManifest } from "../templates/weekly/manifest";

const REGISTRY: Record<ReportTypeId, ReportManifest> = {
  premarket: premarketManifest,
  marketopen: marketopenManifest,
  intraday: intradayManifest,
  event: eventManifest,
  endofday: endofdayManifest,
  weekly: weeklyManifest,
};

export function listManifests(): ReportManifest[] {
  return Object.values(REGISTRY);
}

export function getManifest(type: ReportTypeId): ReportManifest | null {
  return REGISTRY[type] ?? null;
}

export function manifestExists(type: ReportTypeId): boolean {
  return type in REGISTRY;
}

/**
 * Validate that a manifest's sections are all known section IDs and that
 * the required DNA objects are present. Used at registry load time and
 * during report generation.
 */
export function validateManifest(m: ReportManifest): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  const knownSections: SectionId[] = [
    "executive_summary", "market_overview", "technical_intelligence",
    "options_intelligence", "market_intelligence", "narrative_intelligence",
    "forecast_intelligence", "trade_intelligence", "risk_summary", "explainability",
  ];
  for (const s of m.sections) {
    if (!knownSections.includes(s)) {
      errors.push(`Unknown section: ${s}`);
    }
  }
  if (m.sections.length === 0) {
    errors.push("Manifest must declare at least one section");
  }
  if (!m.requiredDNA || m.requiredDNA.length === 0) {
    errors.push("Manifest must declare at least one required DNA object");
  }
  return { ok: errors.length === 0, errors };
}

/** Run validation on every registered manifest at module load. */
export function validateAllManifests(): { ok: boolean; failures: { type: ReportTypeId; errors: string[] }[] } {
  const failures: { type: ReportTypeId; errors: string[] }[] = [];
  for (const [type, manifest] of Object.entries(REGISTRY) as [ReportTypeId, ReportManifest][]) {
    const v = validateManifest(manifest);
    if (!v.ok) failures.push({ type, errors: v.errors });
  }
  return { ok: failures.length === 0, failures };
}
