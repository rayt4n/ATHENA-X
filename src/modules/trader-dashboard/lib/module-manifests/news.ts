import type { ModuleManifest } from "../workspace-types";

export const newsManifest: ModuleManifest = {
  id: "news",
  name: "News Feed",
  description: "Streaming headlines with impact level, source, and sentiment. Filter by severity and search.",
  category: "research",
  defaultSize: { w: 4, h: 8 },
  minSize: { w: 3, h: 5 },
  detachable: true,
  stateful: true,
  icon: "Newspaper",
  schemaVersion: "1.0",
  version: "1.0.0",
};
