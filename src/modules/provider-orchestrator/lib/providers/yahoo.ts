/**
 * Yahoo Finance Provider — Phase 2 live data adapter.
 *
 * Connects to Yahoo Finance's public API endpoints to fetch
 * real market data for SPY, ES, SPX, QQQ, and other symbols.
 *
 * Naming convention: yahoo.ts (not yahoo-finance.ts)
 *
 * Phase 2 objective: Prove the framework by connecting Yahoo Finance
 * and validating end-to-end data flow through the entire ATHENA-X pipeline.
 */

import type { DataRequest, MarketData, ProviderCertification, SupportedEndpoint } from "../types";
import { BaseProvider } from "./base-provider";

// Yahoo Finance chart API response shape
interface YahooChartResponse {
  chart: {
    result: Array<{
      meta: {
        regularMarketPrice: number;
        chartPreviousClose: number;
        previousClose: number;
        symbol: string;
        range: string;
        interval: string;
      };
      timestamp: number[];
      indicators: {
        quote: Array<{
          open: (number | null)[];
          high: (number | null)[];
          low: (number | null)[];
          close: (number | null)[];
          volume: (number | null)[];
        }>;
      };
    }> | null;
    error?: { code: string; description: string };
  };
}

export class YahooProvider extends BaseProvider {
  readonly id = "yahoo";
  readonly name = "Yahoo Finance";
  readonly type = "scrape" as const;
  readonly baseUrl = "https://query1.finance.yahoo.com";
  readonly apiKeyRequired = false;
  readonly qualityScore = 0.70;
  readonly supportedEndpoints: SupportedEndpoint[] = [
    { category: "quotes", symbols: "all", rateLimitPerMin: 60 },
    { category: "historical", symbols: "all", rateLimitPerMin: 60 },
  ];
  readonly certification: ProviderCertification = {
    adapterVersion: "1.0.0",
    providerVersion: "yahoo-finance-api-v8",
    reliability: 0.85,
    lastTested: 0,
    certified: false, // Will be set to true after Phase 2 validation passes
    testResults: [
      { endpoint: "quotes", passed: false, detail: "Pending Phase 2 validation" },
      { endpoint: "historical", passed: false, detail: "Pending Phase 2 validation" },
    ],
  };

  async testConnection(): Promise<boolean> {
    try {
      const url = `${this.baseUrl}/v8/finance/chart/AAPL?interval=1m&range=1d`;
      const res = await fetch(url, {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; ATHENA-X/1.0)" },
      });
      if (!res.ok) return false;
      const data = await res.json() as YahooChartResponse;
      return data.chart?.result?.[0]?.meta?.symbol === "AAPL";
    } catch {
      return false;
    }
  }

  async fetch(request: DataRequest, _apiKey: string | null): Promise<unknown> {
    const interval = request.interval ?? "1m";
    const yahooInterval = interval === "1m" ? "1m" : interval === "5m" ? "5m" : interval === "15m" ? "15m" : interval === "1h" ? "60m" : interval === "1d" ? "1d" : "1m";

    // Determine range based on request
    let range = "1d";
    if (request.startTime && request.endTime) {
      const daysDiff = Math.ceil((request.endTime - request.startTime) / 86_400_000);
      if (daysDiff <= 1) range = "1d";
      else if (daysDiff <= 5) range = "5d";
      else if (daysDiff <= 30) range = "1mo";
      else if (daysDiff <= 90) range = "3mo";
      else if (daysDiff <= 180) range = "6mo";
      else range = "1y";
    }

    const url = `${this.baseUrl}/v8/finance/chart/${encodeURIComponent(request.symbol)}?interval=${yahooInterval}&range=${range}`;
    const res = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; ATHENA-X/1.0)" },
    });

    if (!res.ok) {
      throw new Error(`Yahoo Finance returned ${res.status}: ${res.statusText}`);
    }

    return await res.json() as YahooChartResponse;
  }

  normalize(raw: unknown, symbol: string): MarketData[] {
    const response = raw as YahooChartResponse;
    const result = response.chart?.result?.[0];

    if (!result) {
      const errorMsg = response.chart?.error?.description ?? "No result in Yahoo response";
      throw new Error(errorMsg);
    }

    const timestamps = result.timestamp ?? [];
    const quotes = result.indicators?.quote?.[0];

    if (!quotes) {
      throw new Error("No quote data in Yahoo response");
    }

    const bars: MarketData[] = [];
    for (let i = 0; i < timestamps.length; i++) {
      const open = quotes.open?.[i];
      const high = quotes.high?.[i];
      const low = quotes.low?.[i];
      const close = quotes.close?.[i];
      const volume = quotes.volume?.[i];

      // Skip bars with null values (Yahoo returns null for market gaps)
      if (open === null || high === null || low === null || close === null || volume === null) {
        continue;
      }

      bars.push({
        symbol,
        timestamp: timestamps[i] * 1000, // Yahoo returns seconds, we use ms
        open,
        high,
        low,
        close,
        volume,
        provider: this.id,
        qualityScore: this.qualityScore,
      });
    }

    return bars;
  }
}
