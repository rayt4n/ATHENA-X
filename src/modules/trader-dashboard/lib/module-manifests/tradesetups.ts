import type { ModuleManifest } from "../workspace-types";

export const tradesetupsManifest: ModuleManifest = {
  id: "tradesetups",
  name: "Trade Setups",
  description: "Qualified 0DTE setups from Trade DNA — entry, stop, target, R/R, confidence, 5-DNA contribution bars.",
  category: "trading",
  defaultSize: { w: 5, h: 10 },
  minSize: { w: 3, h: 6 },
  detachable: true,
  stateful: true,
  icon: "Target",
  schemaVersion: "1.0",
  version: "1.0.0",
};
