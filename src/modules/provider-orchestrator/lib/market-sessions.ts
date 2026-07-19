/**
 * Market Session Awareness — knows when the market is expected to produce data.
 *
 * Prevents false failures on weekends, holidays, and outside supported sessions.
 * Symbols have different session expectations (equities vs futures vs forex).
 */

export type AssetClass = "equity" | "future" | "index" | "forex" | "commodity" | "volatility";

export interface SymbolCapability {
  symbol: string;
  assetClass: AssetClass;
  yahooSymbol: string;
  sessions: MarketSession[];
  supportedIntervals: string[];
  premarketData: boolean;
  afterHoursData: boolean;
  weekendData: boolean;
}

export interface MarketSession {
  name: string;
  days: number[];      // 0=Sun, 1=Mon, ..., 6=Sat
  startHour: number;   // ET hour (e.g., 9.5 = 9:30 AM)
  endHour: number;     // ET hour (e.g., 16 = 4:00 PM)
  timezone: string;    // "America/New_York"
}

export interface SessionStatus {
  isOpen: boolean;
  sessionName: string | null;
  reason: string;
  isHoliday: boolean;
  nextOpen: number | null;  // epoch ms
}

// US Market Holidays (simplified — in production, use a holiday calendar API)
const US_HOLIDAYS_2026: string[] = [
  "2026-01-01", // New Year's Day
  "2026-01-19", // MLK Day
  "2026-02-16", // Presidents Day
  "2026-04-03", // Good Friday
  "2026-05-25", // Memorial Day
  "2026-06-19", // Juneteenth
  "2026-07-03", // Independence Day (observed)
  "2026-09-07", // Labor Day
  "2026-11-26", // Thanksgiving
  "2026-12-25", // Christmas
];

const REGULAR_SESSION: MarketSession = {
  name: "RTH",
  days: [1, 2, 3, 4, 5],  // Mon-Fri
  startHour: 9.5,           // 9:30 AM ET
  endHour: 16,              // 4:00 PM ET
  timezone: "America/New_York",
};

const FUTURES_SESSION: MarketSession = {
  name: "Futures",
  days: [0, 1, 2, 3, 4, 5, 6], // 23h on weekdays, limited weekend
  startHour: 18,               // 6:00 PM ET (previous day)
  endHour: 17,                 // 5:00 PM ET
  timezone: "America/New_York",
};

const FOREX_SESSION: MarketSession = {
  name: "Forex",
  days: [0, 1, 2, 3, 4, 5, 6], // 24/5
  startHour: 17,               // 5:00 PM ET Sunday
  endHour: 17,                 // 5:00 PM ET Friday
  timezone: "America/New_York",
};

export const SYMBOL_CAPABILITIES: Record<string, SymbolCapability> = {
  "SPY":     { symbol: "SPY", assetClass: "equity", yahooSymbol: "SPY", sessions: [REGULAR_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: true, afterHoursData: true, weekendData: false },
  "QQQ":     { symbol: "QQQ", assetClass: "equity", yahooSymbol: "QQQ", sessions: [REGULAR_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: true, afterHoursData: true, weekendData: false },
  "ES=F":    { symbol: "ES=F", assetClass: "future", yahooSymbol: "ES=F", sessions: [FUTURES_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: true, afterHoursData: true, weekendData: false },
  "GC=F":    { symbol: "GC=F", assetClass: "commodity", yahooSymbol: "GC=F", sessions: [FUTURES_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: true, afterHoursData: true, weekendData: false },
  "CL=F":    { symbol: "CL=F", assetClass: "commodity", yahooSymbol: "CL=F", sessions: [FUTURES_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: true, afterHoursData: true, weekendData: false },
  "^VIX":    { symbol: "^VIX", assetClass: "index", yahooSymbol: "^VIX", sessions: [REGULAR_SESSION], supportedIntervals: ["1m", "5m", "15m", "1h", "1d"], premarketData: false, afterHoursData: false, weekendData: false },
  "DX-Y.NYB":{ symbol: "DX-Y.NYB", assetClass: "index", yahooSymbol: "DX-Y.NYB", sessions: [REGULAR_SESSION], supportedIntervals: ["1d"], premarketData: false, afterHoursData: false, weekendData: false },
};

export function getSymbolCapability(symbol: string): SymbolCapability | null {
  return SYMBOL_CAPABILITIES[symbol] ?? null;
}

export function isHoliday(date: Date): boolean {
  const dateStr = date.toISOString().slice(0, 10);
  return US_HOLIDAYS_2026.includes(dateStr);
}

export function getSessionStatus(symbol: string, now: Date = new Date()): SessionStatus {
  const cap = getSymbolCapability(symbol);
  if (!cap) {
    return { isOpen: false, sessionName: null, reason: "Unknown symbol", isHoliday: false, nextOpen: null };
  }

  // Check holiday
  if (isHoliday(now)) {
    return { isOpen: false, sessionName: null, reason: "Market holiday", isHoliday: true, nextOpen: null };
  }

  const etHour = now.getUTCHours() - 5 + now.getUTCMinutes() / 60; // Approximate ET (ignoring DST)
  const day = now.getUTCDay();

  // Check if any session is open
  for (const session of cap.sessions) {
    if (!session.days.includes(day)) continue;

    if (session.startHour < session.endHour) {
      // Normal session (e.g., 9:30 to 16:00)
      if (etHour >= session.startHour && etHour < session.endHour) {
        return { isOpen: true, sessionName: session.name, reason: "Market open", isHoliday: false, nextOpen: null };
      }
    } else {
      // Overnight session (e.g., 18:00 to 17:00 next day)
      if (etHour >= session.startHour || etHour < session.endHour) {
        return { isOpen: true, sessionName: session.name, reason: "Market open (overnight)", isHoliday: false, nextOpen: null };
      }
    }
  }

  // Weekend check
  if (day === 0 || day === 6) {
    if (!cap.weekendData) {
      return { isOpen: false, sessionName: null, reason: "Weekend — market closed", isHoliday: false, nextOpen: null };
    }
  }

  return { isOpen: false, sessionName: null, reason: "Outside market hours", isHoliday: false, nextOpen: null };
}

export function shouldExpectData(symbol: string, interval: string = "1m", now: Date = new Date()): { expected: boolean; reason: string } {
  const cap = getSymbolCapability(symbol);
  if (!cap) {
    return { expected: false, reason: "Unknown symbol — cannot determine expectations" };
  }

  // Check interval support
  if (!cap.supportedIntervals.includes(interval)) {
    return { expected: false, reason: `Interval ${interval} not supported for ${symbol} (supported: ${cap.supportedIntervals.join(", ")})` };
  }

  const session = getSessionStatus(symbol, now);
  if (!session.isOpen) {
    return { expected: false, reason: session.reason };
  }

  return { expected: true, reason: `Market open (${session.sessionName})` };
}
