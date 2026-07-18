import type { ModuleManifest } from "../workspace-types";

export const optionschainManifest: ModuleManifest = {
  id: "optionschain",
  name: "Options Chain",
  description: "Strikes, expirations, Greeks, IV, and volume for the active symbol. Switch Greek view (delta/gamma/theta/vega).",
  category: "intelligence",
  defaultSize: { w: 6, h: 10 },
  minSize: { w: 4, h: 6 },
  detachable: true,
  stateful: true,
  icon: "Table",
  schemaVersion: "1.0",
  version: "1.0.0",
};
