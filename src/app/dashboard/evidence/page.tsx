"use client";

import { useEvidence } from "@/lib/athena-api";
import { WidgetCard, QueryBoundary, CertificationBadge } from "@/modules/athena-dashboard/widget-components";
import { type EvidenceContributor } from "@/lib/athena-api";

function ContributorItem({ c, type }: { c: EvidenceContributor; type: "primary" | "supporting" | "contextual" | "conflict" }) {
  const borderColor = type === "primary" ? "border-l-green-500" : type === "supporting" ? "border-l-blue-500" : type === "conflict" ? "border-l-red-500" : "border-l-muted-foreground";
  return (
    <div className={`p-2 rounded bg-muted/40 border-l-2 ${borderColor} mb-1`}>
      <div className="flex justify-between text-[11px] mb-0.5">
        <span className="font-mono font-medium">{c.agent_id}</span>
        <span className="text-amber-500 font-mono text-[10px]">{(c.confidence * 100).toFixed(0)}%</span>
      </div>
      <div className="text-[10px] text-muted-foreground">{c.reason}</div>
    </div>
  );
}

export default function EvidencePage() {
  const { data, isLoading, isError, error } = useEvidence("demo");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Evidence Engine</h1>
        <p className="text-[12px] text-muted-foreground">Every conclusion traced to its contributing agents. Primary, supporting, contextual, and conflicting evidence with confidence scores. Data from InstitutionalWorkspace via /trading/evidence.</p>
      </div>
      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading evidence">
        {data && (
          <>
            <WidgetCard title="Final Conclusion" plugin="InstitutionalWorkspace evidence report" status="VERIFIED">
              <p className="text-[14px] font-semibold text-foreground">{data.final_conclusion}</p>
            </WidgetCard>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
              <WidgetCard title={`Primary (${data.primary_contributors.length})`} plugin="Layer 3+4+5 agents" status="VERIFIED">
                <div className="space-y-0">
                  {data.primary_contributors.map((c, i) => <ContributorItem key={i} c={c} type="primary" />)}
                </div>
              </WidgetCard>
              <WidgetCard title={`Supporting (${data.supporting_contributors.length})`} plugin="Layer 2 indicators" status="VERIFIED">
                <div className="space-y-0">
                  {data.supporting_contributors.map((c, i) => <ContributorItem key={i} c={c} type="supporting" />)}
                </div>
              </WidgetCard>
              <WidgetCard title={`Contextual (${data.contextual_contributors.length})`} plugin="Layer 1 market structure" status="VERIFIED">
                <div className="space-y-0">
                  {data.contextual_contributors.map((c, i) => <ContributorItem key={i} c={c} type="contextual" />)}
                </div>
              </WidgetCard>
              <WidgetCard title={`Conflicts (${data.conflicting_evidence.length})`} plugin="Disagreeing agents" status="PROVISIONAL">
                <div className="space-y-0">
                  {data.conflicting_evidence.map((c, i) => <ContributorItem key={i} c={c} type="conflict" />)}
                </div>
              </WidgetCard>
            </div>

            <WidgetCard title="Historical Accuracy" plugin="PluginValidationWorkspace" status="VERIFIED" className="mt-3">
              <div className="flex flex-wrap gap-3">
                {Object.entries(data.historical_accuracy).map(([agent, acc]) => (
                  <div key={agent} className="flex items-center gap-2 text-[11px]">
                    <span className="text-muted-foreground font-mono">{agent}:</span>
                    <span className="font-mono font-medium text-amber-500">{acc}</span>
                  </div>
                ))}
              </div>
            </WidgetCard>
          </>
        )}
      </QueryBoundary>
    </div>
  );
}
