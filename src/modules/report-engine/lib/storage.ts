/**
 * Report Storage
 *
 * In-memory versioned store for generated reports. In production this
 * would be Supabase Storage + a reports table; here we use an in-memory
 * map that survives across requests within the same Next.js dev server.
 *
 * Every stored report carries:
 *   - content (composed from DNA + canonical)
 *   - audit metadata (versioning, hash, DNA versions)
 *   - status (draft → published → archived)
 *   - formats (markdown / json / pdf storage URIs)
 *   - lifecycle events (created / updated / failed / published)
 */

import { generateMarkdown } from "./generators/markdown";
import { generateJson } from "./generators/json";
import { getReportEventBus } from "./event-bus";
import type {
  AuditMetadata,
  GenerateReportRequest,
  GenerateReportResult,
  ReportContent,
  ReportEvent,
  ReportTypeId,
  StoredReport,
} from "./types";

interface Store {
  reports: Map<string, StoredReport>;
  /** Index by type for fast listing */
  byType: Map<ReportTypeId, string[]>;
  /** Index by session date for fast listing */
  byDate: Map<string, string[]>;
}

// Use globalThis to persist the store across Next.js hot reloads and
// worker boundaries in dev mode. In production this would be replaced
// by Supabase Storage + a reports table.
const globalStore: { __athenaReportStore?: Store } = globalThis as unknown as { __athenaReportStore?: Store };

function getStore(): Store {
  if (!globalStore.__athenaReportStore) {
    globalStore.__athenaReportStore = {
      reports: new Map(),
      byType: new Map(),
      byDate: new Map(),
    };
  }
  return globalStore.__athenaReportStore;
}

/** Test helper — reset store between test runs. */
export function resetReportStore(): void {
  globalStore.__athenaReportStore = undefined;
}

export function listReports(filter?: { type?: ReportTypeId; sessionDate?: string; status?: StoredReport["status"] }): StoredReport[] {
  const s = getStore();
  let ids: string[] | undefined;

  if (filter?.type) {
    ids = s.byType.get(filter.type);
  } else if (filter?.sessionDate) {
    ids = s.byDate.get(filter.sessionDate);
  }

  if (!ids) {
    ids = Array.from(s.reports.keys());
  }

  let reports = ids.map((id) => s.reports.get(id)).filter((r): r is StoredReport => r !== undefined);

  if (filter?.status) {
    reports = reports.filter((r) => r.status === filter.status);
  }

  return reports.sort((a, b) => b.createdAt - a.createdAt);
}

export function getReport(id: string): StoredReport | null {
  return getStore().reports.get(id) ?? null;
}

export function getReportByHash(hash: string): StoredReport | null {
  const s = getStore();
  for (const report of s.reports.values()) {
    if (report.audit.hash === hash) return report;
  }
  return null;
}

export function saveReport(
  content: ReportContent,
  audit: AuditMetadata,
  options: { priorVersion?: string } = {},
): StoredReport {
  const s = getStore();

  // If there's an existing report with the same type+sessionDate, mark it as superseded
  const existing = listReports({ type: content.type, sessionDate: content.sessionDate })
    .filter((r) => r.status !== "archived");

  const isUpdate = existing.length > 0 || options.priorVersion !== undefined;

  const report: StoredReport = {
    id: content.id,
    content,
    audit,
    status: "draft",
    formats: {
      markdown: `s3://reports/${content.id}.md`,
      json: `s3://reports/${content.id}.json`,
      pdf: `s3://reports/${content.id}.pdf`,
    },
    events: [],
    createdAt: Date.now(),
  };

  // Archive prior versions
  for (const old of existing) {
    if (old.id !== report.id) {
      old.status = "archived";
      old.archivedAt = Date.now();
    }
  }

  // Store
  s.reports.set(report.id, report);

  // Index by type
  if (!s.byType.has(content.type)) s.byType.set(content.type, []);
  s.byType.get(content.type)!.unshift(report.id);

  // Index by date
  if (!s.byDate.has(content.sessionDate)) s.byDate.set(content.sessionDate, []);
  s.byDate.get(content.sessionDate)!.unshift(report.id);

  // Publish lifecycle event
  const bus = getReportEventBus();
  const eventType: ReportEvent["type"] = isUpdate ? "report:updated" : "report:created";
  const event: ReportEvent = {
    type: eventType,
    timestamp: Date.now(),
    detail: `${content.title} for ${content.sessionDate}`,
    reportHash: audit.hash,
  };
  report.events.push(event);
  bus.publish(event, report);

  return report;
}

export function markReportFailed(
  request: GenerateReportRequest,
  error: string,
): void {
  const bus = getReportEventBus();
  const event: ReportEvent = {
    type: "report:failed",
    timestamp: Date.now(),
    detail: `Failed to generate ${request.type} report: ${error}`,
  };
  bus.publish(event);
}

export function publishReport(id: string): StoredReport | null {
  const s = getStore();
  const report = s.reports.get(id);
  if (!report) return null;

  report.status = "published";
  report.publishedAt = Date.now();

  const event: ReportEvent = {
    type: "report:published",
    timestamp: Date.now(),
    detail: `${report.content.title} published`,
    reportHash: report.audit.hash,
  };
  report.events.push(event);
  getReportEventBus().publish(event, report);

  return report;
}

export function getReportFormat(id: string, format: "markdown" | "json" | "pdf"): string | null {
  const report = getReport(id);
  if (!report) return null;

  if (format === "markdown") return generateMarkdown(report.content);
  if (format === "json") return generateJson(report.content, report.audit);
  // PDF is generated on-demand by the PDF endpoint
  return null;
}

/** Stats for the engineering console. */
export function getReportStats(): {
  total: number;
  byType: Record<ReportTypeId, number>;
  byStatus: Record<StoredReport["status"], number>;
  recentEvents: ReportEvent[];
} {
  const s = getStore();
  const reports = Array.from(s.reports.values());
  const byType = {} as Record<ReportTypeId, number>;
  const byStatus = {} as Record<StoredReport["status"], number>;
  const recentEvents: ReportEvent[] = [];

  for (const r of reports) {
    byType[r.content.type] = (byType[r.content.type] ?? 0) + 1;
    byStatus[r.status] = (byStatus[r.status] ?? 0) + 1;
    recentEvents.push(...r.events);
  }

  recentEvents.sort((a, b) => b.timestamp - a.timestamp);

  return {
    total: reports.length,
    byType,
    byStatus,
    recentEvents: recentEvents.slice(0, 20),
  };
}
