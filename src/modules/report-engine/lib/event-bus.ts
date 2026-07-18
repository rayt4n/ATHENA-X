/**
 * Report Engine Event Bus
 *
 * Publishes lifecycle events when reports are generated, updated, failed,
 * or published. Subscribers (trader dashboard, audit log, notification
 * system) receive events in real-time — no polling.
 *
 * Event types:
 *   report:created   — generation succeeded, draft stored
 *   report:updated   — existing report regenerated (new version)
 *   report:failed    — generation threw an error
 *   report:published — draft promoted to published (visible to traders)
 */

import type { ReportEvent, StoredReport } from "./types";

type EventCallback = (event: ReportEvent, report?: StoredReport) => void;

class EventBus {
  private subscribers: Map<string, Set<EventCallback>> = new Map();

  subscribe(eventType: ReportEvent["type"], callback: EventCallback): () => void {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, new Set());
    }
    this.subscribers.get(eventType)!.add(callback);
    return () => {
      this.subscribers.get(eventType)?.delete(callback);
    };
  }

  publish(event: ReportEvent, report?: StoredReport): void {
    const subs = this.subscribers.get(event.type);
    if (subs) {
      for (const cb of subs) {
        try {
          cb(event, report);
        } catch (err) {
          console.error(`Event bus subscriber error for ${event.type}:`, err);
        }
      }
    }
    // Also log to console for the engineering console
    console.log(`[report-engine] ${event.type} — ${event.detail ?? ""} (hash: ${event.reportHash?.slice(0, 12) ?? "—"}…)`);
  }

  subscriberCount(eventType?: ReportEvent["type"]): number {
    if (eventType) return this.subscribers.get(eventType)?.size ?? 0;
    return Array.from(this.subscribers.values()).reduce((s, set) => s + set.size, 0);
  }
}

// Singleton — shared across all report-engine calls within the same process
let bus: EventBus | null = null;

export function getReportEventBus(): EventBus {
  if (!bus) bus = new EventBus();
  return bus;
}

/** Test helper — reset the singleton between tests. */
export function resetReportEventBus(): void {
  bus = null;
}
