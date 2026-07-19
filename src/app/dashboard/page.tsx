"use client";

import { useMarketOverview } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";
import { cn } from "@/lib/utils";

function MarketWidgetContent({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  return (
    <div className="space-y-1">
      {entries.map(([key, val]) => (
        <div key={key} className="flex justify-between text-[11px]">
          <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}:</span>
          <span className="font-mono font-medium">
            {typeof val === "number" ? val.toFixed(2) : typeof val === "boolean" ? (val ? "Yes" : "No") : String(val)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function MarketOverviewPage() {
  const { data, isLoading, isError, error } = useMarketOverview();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Market Overview</h1>
        <p className="text-[12px] text-muted-foreground">
          Live market regime, trend detection, breadth, and macro indicators. Data from hub.market, ta.trend, ta.adx, ta.wyckoff, ta.support_resistance.
        </p>
      </div>

      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading market overview">
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.widgets.map((w) => (
              <WidgetCard key={w.id} title={w.name} plugin={w.plugin} status={w.status}>
                <MarketWidgetContent data={w.data} />
              </WidgetCard>
            ))}
          </div>
        )}
      </QueryBoundary>
    </div>
  );
}
