/**
 * Mock Provider — simulated provider for framework testing.
 * Generates realistic MarketData without any live API calls.
 */

import type { DataRequest, MarketData, ProviderCertification, SupportedEndpoint } from "../types";
import { BaseProvider } from "./base-provider";

export class MockProvider extends BaseProvider {
  readonly id = "mock";
  readonly name = "Mock Provider (Framework Test)";
  readonly type = "internal" as const;
  readonly baseUrl = "internal://mock";
  readonly apiKeyRequired = false;
  readonly qualityScore = 0.85;
  readonly supportedEndpoints: SupportedEndpoint[] = [
    { category: "quotes", symbols: "all", rateLimitPerMin: 9999 },
    { category: "historical", symbols: "all", rateLimitPerMin: 9999 },
  ];
  readonly certification: ProviderCertification = {
    adapterVersion: "1.0.0",
    providerVersion: "internal-mock-v1",
    reliability: 1.0,
    lastTested: Date.now(),
    certified: true,
    testResults: [
      { endpoint: "quotes", passed: true, detail: "Generates valid OHLCV data" },
      { endpoint: "historical", passed: true, detail: "Generates 60 bars per request" },
    ],
  };

  async testConnection(): Promise<boolean> {
    return true;
  }

  async fetch(request: DataRequest): Promise<unknown> {
    const bars: Record<string, unknown>[] = [];
    const basePrice = 380 + (request.symbol.charCodeAt(0) % 30) * 5;
    const interval = request.interval ?? "1m";
    const intervalMs = interval === "1m" ? 60_000 : interval === "5m" ? 300_000 : interval === "1h" ? 3_600_000 : 86_400_000;
    const count = 60;
    const now = Date.now();
    for (let i = 0; i < count; i++) {
      const ts = now - (count - i) * intervalMs;
      const open = basePrice + (Math.random() - 0.5) * 4;
      const close = open + (Math.random() - 0.5) * 3;
      const high = Math.max(open, close) + Math.random() * 1.5;
      const low = Math.min(open, close) - Math.random() * 1.5;
      const volume = Math.floor(50_000 + Math.random() * 200_000);
      bars.push({ timestamp: ts, open, high, low, close, volume });
    }
    return { symbol: request.symbol, bars };
  }

  normalize(raw: unknown, symbol: string): MarketData[] {
    const data = raw as { bars: Array<{ timestamp: number; open: number; high: number; low: number; close: number; volume: number }> };
    return data.bars.map((b) => ({
      symbol, timestamp: b.timestamp, open: b.open, high: b.high, low: b.low, close: b.close, volume: b.volume,
      provider: this.id, qualityScore: this.qualityScore,
    }));
  }
}
