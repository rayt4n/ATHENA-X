/**
 * JSON Generator
 *
 * Produces a structured JSON document containing the same content as the
 * Markdown version, but in machine-readable form. Used for trader dashboard
 * consumption, API responses, and audit replay.
 */

import type { ReportContent, AuditMetadata } from "../types";

export function generateJson(content: ReportContent, audit: AuditMetadata): string {
  const doc = {
    schemaVersion: audit.schemaVersion,
    generatorVersion: audit.generatorVersion,
    buildVersion: audit.buildVersion,
    report: {
      id: content.id,
      type: content.type,
      eventSubtype: content.eventSubtype,
      title: content.title,
      subtitle: content.subtitle,
      sessionDate: content.sessionDate,
      generatedAt: content.generatedAt,
      generatedAtISO: new Date(content.generatedAt).toISOString(),
    },
    audit: {
      workspace: audit.workspace,
      user: audit.user,
      hash: audit.hash,
      dnaVersions: audit.dnaVersions,
      forecastVersion: audit.forecastVersion,
      priorVersion: audit.priorVersion,
    },
    dnaSnapshot: content.dnaSnapshot,
    sections: content.sections.map((s) => ({
      id: s.id,
      title: s.title,
      data: s.data,
      sources: s.sources,
      // Note: markdown is included for convenience but the `data` field is
      // the authoritative machine-readable representation
      markdown: s.markdown,
    })),
  };

  return JSON.stringify(doc, null, 2);
}
