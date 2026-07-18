import type { ModuleManifest } from "../workspace-types";

export const reportsManifest: ModuleManifest = {
  id: "reports",
  name: "Reports",
  description: "Recent institutional reports from the Stage 15 Report Engine. Generate, view, and download PDFs.",
  category: "research",
  defaultSize: { w: 6, h: 10 },
  minSize: { w: 4, h: 6 },
  detachable: true,
  stateful: true,
  icon: "FileText",
  schemaVersion: "1.0",
  version: "1.0.0",
};
