"use client";

import { useInstitutional, useMarketOverview } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";

export default function IntelligencePage() {
  const inst = useInstitutional();
  const mkt = useMarketOverview();

  // Filter institutional widgets to market-intelligence-relevant ones
  const marketWidgets = inst.data?.widgets.filter(w =>
    ["bond", "dollar", "asia", "europe", "mag7"].includes(w.id)
  ) || [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Market Intelligence</h1>
        <p className="text-[12px] text-muted-foreground">Cross-market snapshot: bonds, dollar, international sessions, MAG7. Data from hub.market via /trading/institutional.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        <QueryBoundary isLoading={inst.isLoading} isError={inst.isError} error={inst.error} loadingLabel="Loading market intelligence">
          {inst.data && marketWidgets.map((w) => (
            <WidgetCard key={w.id} title={w.name} plugin={w.plugin} status={w.status}>
              <div className="space-y-1">
                {Object.entries(w.data).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-[11px]">
                    <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}:</span>
                    <span className="font-mono font-medium">{String(v)}</span>
                  </div>
                ))}
              </div>
            </WidgetCard>
          ))}
        </QueryBoundary>
      </div>
      <WidgetCard title="Market Breadth & Rotation" plugin="hub.market" status="PROVISIONAL">
        <QueryBoundary isLoading={mkt.isLoading} isError={mkt.isError} error={mkt.error} loadingLabel="Loading breadth">
          {mkt.data && (
            <div className="grid grid-cols-2 gap-4">
              {mkt.data.widgets.filter(w => ["market_breadth", "sector_rotation", "market_regime"].includes(w.id)).map((w) => (
                <div key={w.id} className="space-y-1">
                  <div className="text-[11px] font-semibold text-muted-foreground uppercase">{w.name}</div>
                  {Object.entries(w.data).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[11px]">
                      <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}:</span>
                      <span className="font-mono">{typeof v === "number" ? v.toFixed(2) : String(v)}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </QueryBoundary>
      </WidgetCard>
    </div>
  );
}
