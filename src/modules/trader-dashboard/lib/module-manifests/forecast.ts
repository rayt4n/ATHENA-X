import type { ModuleManifest } from "../workspace-types";

export const forecastManifest: ModuleManifest = {
  id: "forecast",
  name: "Forecast Panel",
  description: "Bull / Base / Bear scenarios with horizon forecasts (5m → tomorrow) and calibration status.",
  category: "intelligence",
  defaultSize: { w: 4, h: 8 },
  minSize: { w: 3, h: 5 },
  detachable: true,
  stateful: true,
  icon: "TrendingUp",
  schemaVersion: "1.0",
  version: "1.0.0",
};
