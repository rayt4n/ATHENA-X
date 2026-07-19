import type { ReportManifest } from "../types";

export const eventManifest: ReportManifest = {
  type: "event",
  name: "Event Report",
  description: "Generated immediately after a major event: CPI, FOMC, NFP, earnings, treasury auction, or geopolitical event.",
  sections: [
    "executive_summary",
    "market_overview",
    "narrative_intelligence",
    "options_intelligence",
    "market_intelligence",
    "forecast_intelligence",
    "trade_intelligence",
    "risk_summary",
    "explainability",
  ],
  trigger: { kind: "event" },
  acceptsEventSubtype: true,
  requiredDNA: ["technical", "options", "market", "narrative", "forecast", "trade"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
