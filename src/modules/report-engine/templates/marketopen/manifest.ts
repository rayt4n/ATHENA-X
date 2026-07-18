import type { ReportManifest } from "../types";

export const marketopenManifest: ReportManifest = {
  type: "marketopen",
  name: "Market Open Report",
  description: "Generated at the opening bell. Opening gap, range, breadth, liquidity, dealer positioning, trade readiness, institutional checklist.",
  sections: [
    "executive_summary",
    "market_overview",
    "technical_intelligence",
    "options_intelligence",
    "market_intelligence",
    "trade_intelligence",
    "risk_summary",
    "explainability",
  ],
  trigger: { kind: "cron", spec: "30 9 * * 1-5" }, // 9:30 AM ET
  requiredDNA: ["technical", "options", "market", "trade"],
  schemaVersion: "1.0",
  author: "ATHENA-X Report Engine",
  version: "1.0.0",
};
