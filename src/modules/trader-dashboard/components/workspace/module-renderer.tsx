"use client";

import type { LayoutItem } from "@/modules/trader-dashboard/lib/workspace-types";
import { WatchlistModule } from "../modules/watchlist-module";
import { ChartModule } from "../modules/chart-module";
import { OrderBookModule } from "../modules/orderbook-module";
import { OptionsChainModule } from "../modules/optionschain-module";
import { NewsModule } from "../modules/news-module";
import { TradeSetupsModule } from "../modules/tradesetups-module";
import { ForecastModule } from "../modules/forecast-module";
import { DNAModule } from "../modules/dna-module";
import { PositionsModule } from "../modules/positions-module";
import { ReportsModule } from "../modules/reports-module";
import { MarketOverviewModule } from "../modules/marketoverview-module";
import { AlertsModule } from "../modules/alerts-module";

interface ModuleRendererProps {
  item: LayoutItem;
  selectedSymbol: string;
  timeframe: string;
  onSelectSymbol: (symbol: string) => void;
  onSelectTimeframe: (timeframe: string) => void;
  onModuleStateChange: (instanceId: string, partial: Record<string, unknown>) => void;
}

/**
 * Renders the correct module component based on the layout item's moduleId.
 * Each module receives its own state + a callback to update it, plus the
 * workspace-level selected symbol/timeframe.
 */
export function ModuleRenderer({
  item,
  selectedSymbol,
  timeframe,
  onSelectSymbol,
  onSelectTimeframe,
  onModuleStateChange,
}: ModuleRendererProps) {
  const updateState = (partial: Record<string, unknown>) => onModuleStateChange(item.instanceId, partial);

  switch (item.moduleId) {
    case "watchlist":
      return (
        <WatchlistModule
          state={item.state as never}
          onStateChange={updateState}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={onSelectSymbol}
        />
      );
    case "chart":
      return (
        <ChartModule
          state={{ ...item.state, symbol: selectedSymbol, timeframe: item.state.timeframe ?? timeframe } as never}
          onStateChange={updateState}
          selectedSymbol={selectedSymbol}
          onSelectTimeframe={onSelectTimeframe}
        />
      );
    case "orderbook":
      return <OrderBookModule selectedSymbol={selectedSymbol} />;
    case "optionschain":
      return (
        <OptionsChainModule
          state={{ ...item.state, symbol: selectedSymbol } as never}
          onStateChange={updateState}
          selectedSymbol={selectedSymbol}
        />
      );
    case "news":
      return <NewsModule state={item.state as never} onStateChange={updateState} />;
    case "tradesetups":
      return <TradeSetupsModule state={item.state as never} onStateChange={updateState} />;
    case "forecast":
      return (
        <ForecastModule
          state={item.state as never}
          onStateChange={updateState}
          selectedSymbol={selectedSymbol}
        />
      );
    case "dna":
      return <DNAModule state={item.state as never} onStateChange={updateState} />;
    case "positions":
      return <PositionsModule state={item.state as never} onStateChange={updateState} />;
    case "reports":
      return <ReportsModule state={item.state as never} onStateChange={updateState} />;
    case "marketoverview":
      return (
        <MarketOverviewModule
          state={item.state as never}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={onSelectSymbol}
        />
      );
    case "alerts":
      return <AlertsModule state={item.state as never} onStateChange={updateState} />;
    default:
      return <div className="p-4 text-[11px] text-muted-foreground">Unknown module: {item.moduleId}</div>;
  }
}
