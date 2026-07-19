"use client";

import { useCallback, useEffect, useState } from "react";
import type { ProviderConfig, ProviderMode, RoutingRule, HealthSnapshot } from "../lib/types";
import * as registry from "../lib/registry";
import { getOrchestratorHealth } from "../lib/orchestrator";

export function useProviders() {
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [mode, setModeState] = useState<ProviderMode>("free");
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>([]);
  const [healthSnapshots, setHealthSnapshots] = useState<HealthSnapshot[]>([]);
  const [cacheStats, setCacheStats] = useState({ entries: 0, totalSize: 0 });

  const refresh = useCallback(() => {
    setProviders(registry.getProviders());
    setModeState(registry.getMode());
    setRoutingRules(registry.getRoutingRules());
    const health = getOrchestratorHealth();
    setHealthSnapshots(health.snapshots);
    setCacheStats(health.cache);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const changeMode = useCallback((newMode: ProviderMode) => {
    registry.setMode(newMode);
    refresh();
  }, [refresh]);

  const toggleProvider = useCallback((id: string) => {
    const provider = registry.getProvider(id);
    if (provider) {
      registry.updateProvider(id, { enabled: !provider.enabled });
      refresh();
    }
  }, [refresh]);

  const updateApiKey = useCallback((id: string, apiKey: string) => {
    registry.updateProvider(id, { apiKey: apiKey || null });
    refresh();
  }, [refresh]);

  const reorder = useCallback((orderedIds: string[]) => {
    registry.reorderProviders(orderedIds);
    refresh();
  }, [refresh]);

  const removeProvider = useCallback((id: string) => {
    registry.removeProvider(id);
    refresh();
  }, [refresh]);

  const updateRoutingRule = useCallback((ruleId: string, updates: Partial<RoutingRule>) => {
    registry.updateRoutingRule(ruleId, updates);
    refresh();
  }, [refresh]);

  const reset = useCallback(() => {
    registry.resetToDefaults();
    refresh();
  }, [refresh]);

  return {
    providers,
    mode,
    routingRules,
    healthSnapshots,
    cacheStats,
    refresh,
    changeMode,
    toggleProvider,
    updateApiKey,
    reorder,
    removeProvider,
    updateRoutingRule,
    reset,
  };
}
