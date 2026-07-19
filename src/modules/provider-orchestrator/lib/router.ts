/**
 * Smart Router — selects the best provider for each data request.
 *
 * Selection algorithm:
 *   1. Filter: providers that support the endpoint AND are enabled AND healthy
 *   2. Sort: priority (asc) → latency (asc) → rate_limit_remaining (desc) → quality (desc)
 *   3. Try each in order until one succeeds
 *   4. All fail → return cached data
 */

import type { DataRequest, ProviderConfig, ProviderMode, RoutingRule } from "./types";

export interface RouteResult {
  providerId: string;
  fromCache: boolean;
  attempted: string[];   // provider IDs tried in order
}

/**
 * Get the ordered list of provider IDs to try for a given request.
 * Considers mode (free/custom/advanced), routing rules, and provider health.
 */
export function getProviderOrder(
  request: DataRequest,
  providers: ProviderConfig[],
  routingRules: RoutingRule[],
  mode: ProviderMode
): string[] {
  // In Advanced mode, use routing rules per category
  if (mode === "advanced") {
    const rule = routingRules.find((r) => r.enabled && r.category === request.category);
    if (rule) {
      return filterAndSort(rule.providerIds, providers, request);
    }
  }

  // In Free/Custom mode, use default priority stack
  const orderedIds = providers
    .filter((p) => p.enabled)
    .sort((a, b) => a.priority - b.priority)
    .map((p) => p.id);

  return filterAndSort(orderedIds, providers, request);
}

/**
 * Filter provider IDs to only those that:
 *   - Exist in the provider list
 *   - Are enabled
 *   - Are healthy (or cache/warming)
 *   - Support the requested endpoint
 *
 * Then sort by: priority → latency → rate limit remaining → quality
 */
function filterAndSort(
  providerIds: string[],
  providers: ProviderConfig[],
  request: DataRequest
): string[] {
  return providerIds
    .map((id) => providers.find((p) => p.id === id))
    .filter((p): p is ProviderConfig => p !== undefined)
    .filter((p) => p.enabled)
    .filter((p) => p.health === "connected" || p.health === "warming" || p.id === "cache")
    .filter((p) => supportsEndpoint(p, request))
    .filter((p) => p.rateLimitRemaining > 0 || p.id === "cache")
    .sort((a, b) => {
      // Priority first (lower = higher priority)
      if (a.priority !== b.priority) return a.priority - b.priority;
      // Then latency (lower = better)
      if (a.latencyMs !== b.latencyMs) return a.latencyMs - b.latencyMs;
      // Then rate limit remaining (higher = better)
      if (a.rateLimitRemaining !== b.rateLimitRemaining) return b.rateLimitRemaining - a.rateLimitRemaining;
      // Then quality (higher = better)
      return b.qualityScore - a.qualityScore;
    })
    .map((p) => p.id);
}

/**
 * Check if a provider supports the requested endpoint.
 */
function supportsEndpoint(provider: ProviderConfig, request: DataRequest): boolean {
  return provider.supportedEndpoints.some(
    (ep) =>
      ep.category === request.category &&
      (ep.symbols === "all" || ep.symbols.includes(request.symbol.toUpperCase()))
  );
}

/**
 * Determine the route for a request without actually fetching.
 * Used for display/logging purposes.
 */
export function planRoute(
  request: DataRequest,
  providers: ProviderConfig[],
  routingRules: RoutingRule[],
  mode: ProviderMode
): RouteResult {
  const order = getProviderOrder(request, providers, routingRules, mode);

  // If cache is in the list, it's the fallback
  const hasCache = order.includes("cache");
  const realProviders = order.filter((id) => id !== "cache");

  return {
    providerId: realProviders[0] ?? "cache",
    fromCache: realProviders.length === 0 && hasCache,
    attempted: order,
  };
}
