/**
 * Base Provider — abstract class that all provider adapters must extend.
 * Defines the contract for fetching and normalizing data.
 *
 * Phase 1: Framework only — no live API connections.
 * Phase 2: Yahoo Finance adapter will extend this class.
 */

import type { DataRequest, MarketData, ProviderAdapter, SupportedEndpoint } from "../types";

export abstract class BaseProvider implements ProviderAdapter {
  abstract readonly id: string;
  abstract readonly name: string;
  abstract readonly type: "rest" | "websocket" | "scrape" | "internal";
  abstract readonly baseUrl: string;
  abstract readonly apiKeyRequired: boolean;
  abstract readonly supportedEndpoints: SupportedEndpoint[];
  abstract readonly qualityScore: number;
  readonly isBuiltin: boolean = true;

  /**
   * Test connectivity to the provider.
   * Phase 1: returns false (no live connection).
   * Phase 2: overridden by concrete providers.
   */
  async testConnection(_apiKey: string | null): Promise<boolean> {
    return false;
  }

  /**
   * Fetch data from the provider.
   * Phase 1: throws "not connected" error.
   * Phase 2: overridden by concrete providers to make real API calls.
   */
  async fetch(_request: DataRequest, _apiKey: string | null): Promise<unknown> {
    throw new Error(`Provider ${this.name} is not connected. Connect providers in Phase 2.`);
  }

  /**
   * Normalize raw provider JSON into unified MarketData.
   * Must be implemented by each concrete provider.
   */
  abstract normalize(raw: unknown, symbol: string): MarketData[];

  /**
   * Check if this provider supports the given data request.
   */
  supports(request: DataRequest): boolean {
    return this.supportedEndpoints.some(
      (ep) =>
        ep.category === request.category &&
        (ep.symbols === "all" || ep.symbols.includes(request.symbol.toUpperCase()))
    );
  }
}
