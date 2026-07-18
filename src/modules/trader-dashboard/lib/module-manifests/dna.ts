import type { ModuleManifest } from "../workspace-types";

export const dnaManifest: ModuleManifest = {
  id: "dna",
  name: "DNA Confidence",
  description: "Live confidence for all 7 DNA objects (Technical, Options, Market, Narrative, Forecast, Trade, Operations).",
  category: "intelligence",
  defaultSize: { w: 4, h: 6 },
  minSize: { w: 3, h: 4 },
  detachable: true,
  stateful: true,
  icon: "Beaker",
  schemaVersion: "1.0",
  version: "1.0.0",
};
