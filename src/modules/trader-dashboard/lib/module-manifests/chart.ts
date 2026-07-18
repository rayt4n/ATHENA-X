import type { ModuleManifest } from "../workspace-types";

export const chartManifest: ModuleManifest = {
  id: "chart",
  name: "Price Chart",
  description: "Candlestick / line / area chart with timeframe selector and indicator overlays (EMA, VWAP, RSI).",
  category: "market_data",
  defaultSize: { w: 6, h: 10 },
  minSize: { w: 4, h: 6 },
  detachable: true,
  stateful: true,
  icon: "CandlestickChart",
  schemaVersion: "1.0",
  version: "1.0.0",
};
