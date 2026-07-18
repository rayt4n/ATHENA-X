/**
 * Module Registry — loads and validates module manifests.
 * Adding a new module means adding a new manifest file — the workspace
 * manager core never changes. This is the same plugin pattern used
 * throughout ATHENA-X.
 */

import type { ModuleId, ModuleManifest } from "./workspace-types";
import { watchlistManifest } from "./module-manifests/watchlist";
import { chartManifest } from "./module-manifests/chart";
import { orderbookManifest } from "./module-manifests/orderbook";
import { optionschainManifest } from "./module-manifests/optionschain";
import { newsManifest } from "./module-manifests/news";
import { tradesetupsManifest } from "./module-manifests/tradesetups";
import { forecastManifest } from "./module-manifests/forecast";
import { dnaManifest } from "./module-manifests/dna";
import { positionsManifest } from "./module-manifests/positions";
import { reportsManifest } from "./module-manifests/reports";
import { marketoverviewManifest } from "./module-manifests/marketoverview";
import { alertsManifest } from "./module-manifests/alerts";

const REGISTRY: Record<ModuleId, ModuleManifest> = {
  watchlist: watchlistManifest,
  chart: chartManifest,
  orderbook: orderbookManifest,
  optionschain: optionschainManifest,
  news: newsManifest,
  tradesetups: tradesetupsManifest,
  forecast: forecastManifest,
  dna: dnaManifest,
  positions: positionsManifest,
  reports: reportsManifest,
  marketoverview: marketoverviewManifest,
  alerts: alertsManifest,
};

export function listModuleManifests(): ModuleManifest[] {
  return Object.values(REGISTRY);
}

export function getModuleManifest(id: ModuleId): ModuleManifest | null {
  return REGISTRY[id] ?? null;
}

export function moduleExists(id: ModuleId): boolean {
  return id in REGISTRY;
}

export function validateManifest(m: ModuleManifest): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!m.id) errors.push("Manifest missing id");
  if (!m.name) errors.push("Manifest missing name");
  if (!m.defaultSize || m.defaultSize.w <= 0 || m.defaultSize.h <= 0) errors.push("Invalid defaultSize");
  if (!m.minSize || m.minSize.w <= 0 || m.minSize.h <= 0) errors.push("Invalid minSize");
  if (m.minSize.w > m.defaultSize.w || m.minSize.h > m.defaultSize.h) errors.push("minSize cannot exceed defaultSize");
  return { ok: errors.length === 0, errors };
}

export function validateAllManifests(): { ok: boolean; failures: { id: string; errors: string[] }[] } {
  const failures: { id: string; errors: string[] }[] = [];
  for (const [id, manifest] of Object.entries(REGISTRY)) {
    const v = validateManifest(manifest);
    if (!v.ok) failures.push({ id, errors: v.errors });
  }
  return { ok: failures.length === 0, failures };
}
