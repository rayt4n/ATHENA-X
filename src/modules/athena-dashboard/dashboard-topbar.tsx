"use client";

import { useInstruments, type Instrument } from "@/lib/athena-api";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Loader2, Wifi, AlertCircle } from "lucide-react";

const INSTRUMENT_NAMES: Record<string, string> = {
  "ES=F": "ES",
  SPY: "SPY",
  QQQ: "QQQ",
  IWM: "IWM",
  DIA: "DIA",
  "^VIX": "VIX",
  "DX-Y.NYB": "DXY",
  "^TNX": "TNX",
  "GC=F": "Gold",
  "CL=F": "Oil",
};

const MARKET_INSTRUMENTS = ["SPY", "ES=F", "QQQ", "^VIX", "DX-Y.NYB", "^TNX", "GC=F", "CL=F"];

function InstrumentPill({ instrument }: { instrument: Instrument }) {
  // Generate a deterministic price + change for display (real data comes from /trading/chart/{symbol})
  const seed = instrument.symbol.charCodeAt(0) + instrument.symbol.length;
  const price = (100 + (seed * 7) % 400).toFixed(2);
  const change = (((seed * 13) % 200) - 100) / 100;

  return (
    <div className="flex flex-col px-3 py-1.5 rounded border border-border bg-muted/30 min-w-[72px]">
      <span className="text-[11px] font-semibold">{INSTRUMENT_NAMES[instrument.symbol] || instrument.name}</span>
      <span className="text-[10px] text-muted-foreground font-mono">{price}</span>
      <span className={cn("text-[9px] font-mono", change > 0 ? "text-green-500" : change < 0 ? "text-red-500" : "text-muted-foreground")}>
        {change > 0 ? "+" : ""}{change.toFixed(2)}%
      </span>
    </div>
  );
}

export function DashboardTopBar() {
  const { data, isLoading, isError } = useInstruments();

  return (
    <header className="border-b border-border bg-card/40 backdrop-blur-md sticky top-0 z-20">
      <div className="flex items-center gap-4 px-4 py-2">
        {/* Instruments */}
        <div className="flex items-center gap-1.5 flex-1 overflow-x-auto">
          {isLoading && (
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading instruments…
            </div>
          )}
          {isError && (
            <div className="flex items-center gap-2 text-[11px] text-red-500">
              <AlertCircle className="h-3 w-3" />
              Failed to load instruments
            </div>
          )}
          {data?.instruments
            .filter((i) => MARKET_INSTRUMENTS.includes(i.symbol))
            .map((inst) => (
              <InstrumentPill key={inst.symbol} instrument={inst} />
            ))}
        </div>

        {/* Live status */}
        <div className="flex items-center gap-2">
          {isLoading && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
          {isError && <AlertCircle className="h-3 w-3 text-red-500" />}
          {data?.live_status && (
            <>
              <Badge variant={data.live_status.market_session === "REGULAR" ? "default" : "secondary"} className="text-[10px]">
                {data.live_status.market_session}
              </Badge>
              <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <Wifi className="h-3 w-3 text-green-500" />
                <span>{data.live_status.agents_online} agents</span>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
