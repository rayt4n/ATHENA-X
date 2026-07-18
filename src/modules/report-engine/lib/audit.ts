/**
 * Audit metadata builder.
 *
 * Computes a deterministic SHA-256 hash of the report content so identical
 * inputs always produce identical hashes. The hash is stored with the report
 * and used to verify integrity during replay.
 */

import { createHash } from "crypto";
import type { AuditMetadata, ComposerInput, ReportContent } from "./types";

const SCHEMA_VERSION = "1.0";
const GENERATOR_VERSION = "athena-x-report-engine-v15.0.0";

export function buildAuditMetadata(
  content: ReportContent,
  input: ComposerInput,
  platform: { buildHash: string; forecastVersion: string },
  options: { workspace: string; user: string; priorVersion?: string },
): AuditMetadata {
  const hash = hashContent(content);
  return {
    schemaVersion: SCHEMA_VERSION,
    buildVersion: platform.buildHash,
    generatorVersion: GENERATOR_VERSION,
    dnaVersions: {
      technical: input.dna.technical.version,
      options: input.dna.options.version,
      market: input.dna.market.version,
      narrative: input.dna.narrative.version,
      forecast: input.dna.forecast.version,
      trade: input.dna.trade.version,
      operations: input.dna.operations.version,
    },
    forecastVersion: platform.forecastVersion,
    workspace: options.workspace,
    user: options.user,
    hash,
    priorVersion: options.priorVersion,
  };
}

/**
 * Deterministic hash of report content. Same content → same hash.
 * Used for audit integrity and replay verification.
 */
export function hashContent(content: ReportContent): string {
  // Build a canonical JSON string with sorted keys for determinism
  const canonical = JSON.stringify({
    id: content.id,
    type: content.type,
    eventSubtype: content.eventSubtype,
    title: content.title,
    subtitle: content.subtitle,
    sessionDate: content.sessionDate,
    generatedAt: content.generatedAt,
    sections: content.sections.map((s) => ({
      id: s.id,
      title: s.title,
      data: s.data,
      sources: s.sources,
      // Note: markdown excluded from hash because it's derived from data —
      // including it would make the hash sensitive to formatting changes.
    })),
    dnaSnapshot: content.dnaSnapshot,
  }, Object.keys(content).sort());

  return createHash("sha256").update(canonical).digest("hex");
}

export function verifyIntegrity(content: ReportContent, expectedHash: string): boolean {
  return hashContent(content) === expectedHash;
}

export { SCHEMA_VERSION, GENERATOR_VERSION };
