"use client";

import { useInstitutional } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";

function InstWidget({ name, plugin, status, data }: { name: string; plugin: string; status: string; data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  return (
    <WidgetCard title={name} plugin={plugin} status={status}>
      <div className="space-y-1">
        {entries.map(([key, val]) => (
          <div key={key} className="flex justify-between text-[11px]">
            <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}:</span>
            <span className="font-mono font-medium">{typeof val === "number" ? val.toFixed(2) : String(val)}</span>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

export default function OptionsPage() {
  const { data, isLoading, isError, error } = useInstitutional();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Options Intelligence</h1>
        <p className="text-[12px] text-muted-foreground">Gamma exposure, dealer positioning, max pain, option flow, dark pool, 0DTE. Data from hub.options and ta.liquidity.</p>
      </div>
      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading options data">
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.widgets.map((w) => (
              <InstWidget key={w.id} name={w.name} plugin={w.plugin} status={w.status} data={w.data} />
            ))}
          </div>
        )}
      </QueryBoundary>
    </div>
  );
}
