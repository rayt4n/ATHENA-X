/**
 * Base Provider — abstract class that all provider adapters must extend.
 * Defines the contract for fetching, normalizing, and certifying data.
 *
 * Naming convention: yahoo.ts, finnhub.ts, twelvedata.ts, fmp.ts, fred.ts
 */

import type { DataRequest, MarketData, ProviderAdapter, ProviderCertification, SupportedEndpoint } from "../types";

export abstract class BaseProvider implements ProviderAdapter {
  abstract readonly id: string;
  abstract readonly name: string;
  abstract readonly type: "rest" | "websocket" | "scrape" | "internal";
  abstract readonly baseUrl: string;
  abstract readonly apiKeyRequired: boolean;
  abstract readonly supportedEndpoints: SupportedEndpoint[];
  abstract readonly qualityScore: number;
  readonly isBuiltin: boolean = true;

  /** Provider certification — every adapter must declare this */
  abstract readonly certification: ProviderCertification;

  /**
   * Test connectivity to the provider.
   * Override in concrete providers to make real API calls.
   */
  async testConnection(_apiKey: string | null): Promise<boolean> {
    return false;
  }

  /**
   * Fetch data from the provider.
   * Override in concrete providers to make real API calls.
   */
  async fetch(_request: DataRequest, _apiKey: string | null): Promise<unknown> {
    throw new Error(`Provider ${this.name} is not connected.`);
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

  /**
   * Get a diagnostics snapshot: fetch raw → normalize → validate.
   * Used by the Provider Diagnostics UI for debugging.
   */
  async getDiagnostics(request: DataRequest, apiKey: string | null): Promise<{
    raw: unknown;
    normalized: MarketData[];
    validCount: number;
    invalidCount: number;
    errors: string[];
    responseTimeMs: number;
  }> {
    const startTime = Date.now();
    const errors: string[] = [];

    // Step 1: Fetch raw data
    let raw: unknown;
    try {
      raw = await this.fetch(request, apiKey);
    } catch (err) {
      return {
        raw: null,
        normalized: [],
        validCount: 0,
        invalidCount: 0,
        errors: [`Fetch failed: ${err instanceof Error ? err.message : String(err)}`],
        responseTimeMs: Date.now() - startTime,
      };
    }

    // Step 2: Normalize
    let normalized: MarketData[] = [];
    try {
      normalized = this.normalize(raw, request.symbol);
    } catch (err) {
      errors.push(`Normalize failed: ${err instanceof Error ? err.message : String(err)}`);
    }

    // Step 3: Validate
    const { validateMarketData } = await import("../normalizer");
    let validCount = 0;
    let invalidCount = 0;
    for (const item of normalized) {
      const result = validateMarketData(item);
      if (result.valid) {
        validCount++;
      } else {
        invalidCount++;
        errors.push(...result.errors);
      }
    }

    return {
      raw,
      normalized,
      validCount,
      invalidCount,
      errors,
      responseTimeMs: Date.now() - startTime,
    };
  }
}
