// Auto-generated. Run `pnpm generate` to regenerate.
// Source: schemas/events/*.yaml

export type EventBusVersion = "1.0.0";

export interface BusEventMeta {
  eventId: string;
  eventType: string;
  timestamp: string;
  provider: string;
  latency: number;
  confidence: number;
  dataVersion: string;
  retryCount: number;
  agentId: string;
  processingTime: number;
}

export interface BusEvent<T = unknown> extends BusEventMeta {
  payload: T;
}

export type EventNamespace =
  | "market"
  | "ta"
  | "options"
  | "news"
  | "macro"
  | "cross_market"
  | "decision"
  | "forecast"
  | "probability"
  | "supervisor"
  | "validator"
  | "learning"
  | "report"
  | "ui"
  | "system";

export type EventBusPattern = string;
