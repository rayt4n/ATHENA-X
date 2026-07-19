"use client";

import { useReport } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";

export default function ReportPage() {
  const { data, isLoading, isError, error } = useReport();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Institutional Report</h1>
        <p className="text-[12px] text-muted-foreground">11-section report aggregating all intelligence hubs. Data from /trading/report.</p>
      </div>
      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Generating report">
        {data && (
          <>
            <div className="text-[11px] text-muted-foreground">
              Generated: <span className="font-mono">{data.generated_at}</span> · Symbol: <span className="font-mono font-medium">{data.symbol}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.sections.map((s) => (
                <WidgetCard key={s.id} title={s.title} plugin={s.source} status="PROVISIONAL" className="md:col-span-2">
                  <p className="text-[12px] text-foreground leading-relaxed">{s.content}</p>
                </WidgetCard>
              ))}
            </div>
          </>
        )}
      </QueryBoundary>
    </div>
  );
}
