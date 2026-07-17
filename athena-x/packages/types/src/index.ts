// Domain types — stable, hand-curated.

export type Symbol = string;
export type AssetClass = 'equity' | 'etf' | 'index' | 'future' | 'option' | 'currency' | 'commodity' | 'yield' | 'volatility' | 'crypto';
export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1D' | '1W' | '1M';
export type Direction = 'long' | 'short' | 'neutral';
export type SignalStrength = 'weak' | 'moderate' | 'strong';
export type ProviderName = 'yahoo' | 'finnhub' | 'polygon' | 'flashalpha' | 'fred' | 'alphavantage' | 'simulated';
export type MarketRegime =
  | 'trending'
  | 'ranging'
  | 'breakout'
  | 'mean-reversion'
  | 'high-vol'
  | 'low-vol'
  | 'news-driven'
  | 'option-driven'
  | 'dealer-controlled';

export interface Quote {
  symbol: Symbol;
  last: number;
  bid: number;
  ask: number;
  high: number;
  low: number;
  open: number;
  prevClose: number;
  volume: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

export interface Bar {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AgentId {
  readonly agentId: string;
  readonly layer: 'data-collection' | 'raw-intelligence' | 'decision-intelligence' | 'supervisor' | 'validator' | 'self-correction' | 'automation';
  readonly module: string;
  readonly sub: string;
}

export interface Confidence {
  readonly score: number;  // 0..1
  readonly evidence: number;
  readonly sources: number;
  readonly agreement: number;  // 0..1
}

export const MAIN_INDICATORS = ['ES', 'SPY'] as const;
export type MainIndicator = typeof MAIN_INDICATORS[number];
