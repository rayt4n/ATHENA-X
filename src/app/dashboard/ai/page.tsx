"use client";

import { useAIForecast } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary } from "@/modules/athena-dashboard/widget-components";
import { Progress } from "@/components/ui/progress";

export default function AIPage() {
  const { data, isLoading, isError, error } = useAIForecast();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">AI Analysis</h1>
        <p className="text-[12px] text-muted-foreground">Bull/neutral/bear probability, probability tree, expected range, volatility, and multi-horizon projections. Data from hub.forecast via /trading/ai-forecast.</p>
      </div>
      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading AI forecast">
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <WidgetCard title="Bias — Bull / Neutral / Bear" plugin="hub.forecast" status="PROVISIONAL">
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-green-500 font-medium">Bull</span>
                    <span className="font-mono">{(data.bias.bull * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={data.bias.bull * 100} className="h-2 bg-muted [&>div]:bg-green-600" />
                </div>
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-amber-500 font-medium">Neutral</span>
                    <span className="font-mono">{(data.bias.neutral * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={data.bias.neutral * 100} className="h-2 bg-muted [&>div]:bg-amber-600" />
                </div>
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-red-500 font-medium">Bear</span>
                    <span className="font-mono">{(data.bias.bear * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={data.bias.bear * 100} className="h-2 bg-muted [&>div]:bg-red-600" />
                </div>
              </div>
            </WidgetCard>

            <WidgetCard title="Probability Tree" plugin="hub.forecast" status="PROVISIONAL">
              <div className="space-y-2">
                {Object.entries(data.probability_tree).map(([k, v]) => (
                  <div key={k} className="p-2 rounded bg-muted/50 border-l-2 border-primary">
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="font-semibold capitalize">{k.replace("_scenario", "")}</span>
                      <span className="font-mono text-amber-500">{(v.probability * 100).toFixed(0)}%</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">Target: <span className="font-mono">{v.target}</span></div>
                    <div className="text-[10px] text-muted-foreground">{v.condition}</div>
                  </div>
                ))}
              </div>
            </WidgetCard>

            <WidgetCard title="Expected Range" plugin="hub.forecast" status="PROVISIONAL">
              <div className="space-y-2">
                <div className="flex justify-between text-[11px]"><span className="text-muted-foreground">Low:</span><span className="font-mono font-medium text-red-400">{data.expected_range.low}</span></div>
                <div className="flex justify-between text-[11px]"><span className="text-muted-foreground">Mid:</span><span className="font-mono font-medium">{data.expected_range.mid}</span></div>
                <div className="flex justify-between text-[11px]"><span className="text-muted-foreground">High:</span><span className="font-mono font-medium text-green-400">{data.expected_range.high}</span></div>
                <div className="flex justify-between text-[11px] pt-2 border-t border-border"><span className="text-muted-foreground">Confidence:</span><span className="font-mono text-amber-500">{(data.expected_range.confidence * 100).toFixed(0)}%</span></div>
              </div>
            </WidgetCard>

            <WidgetCard title="Projections" plugin="hub.forecast" status="PROVISIONAL">
              <div className="space-y-2">
                {Object.entries(data.projections).map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center text-[11px] py-1 border-b border-border/50 last:border-0">
                    <div>
                      <span className="font-semibold uppercase">{k}</span>
                      <span className="text-muted-foreground ml-2 font-mono">{v.expected_change}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={v.direction === "bullish" ? "text-green-500" : v.direction === "bearish" ? "text-red-500" : "text-muted-foreground"}>{v.direction}</span>
                      <span className="text-[9px] text-amber-500 font-mono">{(v.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </WidgetCard>
          </div>
        )}
      </QueryBoundary>
    </div>
  );
}
