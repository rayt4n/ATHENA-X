"use client";

import { useReport } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";

export default function TradePage() {
  const { data, isLoading, isError, error } = useReport();

  const tradePlan = data?.sections.find(s => s.id === "trade_plan");
  const risk = data?.sections.find(s => s.id === "risk");
  const invalidation = data?.sections.find(s => s.id === "invalidation");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Trade Setup</h1>
        <p className="text-[12px] text-muted-foreground">Trade plan, risk assessment, and invalidation levels. Data from hub.trade via /trading/report.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <WidgetCard title="Trade Plan" plugin="hub.trade" status="PROVISIONAL" className="md:col-span-2">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading trade plan">
            {tradePlan && <p className="text-[12px] text-foreground leading-relaxed">{tradePlan.content}</p>}
          </QueryBoundary>
        </WidgetCard>
        <WidgetCard title="Risk Assessment" plugin="hub.trade" status="PROVISIONAL">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading risk">
            {risk && <p className="text-[12px] text-foreground leading-relaxed">{risk.content}</p>}
          </QueryBoundary>
        </WidgetCard>
        <WidgetCard title="Invalidation Levels" plugin="hub.trade + ta.support_resistance" status="PROVISIONAL" className="md:col-span-3">
          <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading invalidation">
            {invalidation && <p className="text-[12px] text-foreground leading-relaxed">{invalidation.content}</p>}
          </QueryBoundary>
        </WidgetCard>
      </div>
    </div>
  );
}
