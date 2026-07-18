import type { ModuleManifest } from "../workspace-types";

export const alertsManifest: ModuleManifest = {
  id: "alerts",
  name: "Alerts",
  description: "Active alerts with severity, source, and acknowledgment. Filter by severity and status.",
  category: "ops",
  defaultSize: { w: 4, h: 6 },
  minSize: { w: 3, h: 4 },
  detachable: true,
  stateful: true,
  icon: "Bell",
  schemaVersion: "1.0",
  version: "1.0.0",
};
