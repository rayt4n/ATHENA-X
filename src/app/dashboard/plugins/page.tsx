"use client";

import { usePluginStatus } from "@/lib/athena-api";
import { QueryBoundary, CertificationBadge } from "@/modules/athena-dashboard/widget-components";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PluginsPage() {
  const { data, isLoading, isError, error } = usePluginStatus();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Plugin Status</h1>
        <p className="text-[12px] text-muted-foreground">Validation certification for every runtime agent. Data from PluginValidationWorkspace via /trading/plugin-status.</p>
      </div>

      <QueryBoundary isLoading={isLoading} isError={isError} error={error} loadingLabel="Loading plugin status">
        {data && (
          <>
            <div className="grid grid-cols-4 gap-3">
              <Card className="bg-card/50"><CardContent className="p-3 text-center"><div className="text-[10px] text-muted-foreground uppercase">Total</div><div className="text-2xl font-bold">{data.summary.total}</div></CardContent></Card>
              <Card className="bg-card/50"><CardContent className="p-3 text-center"><div className="text-[10px] text-muted-foreground uppercase">Certified</div><div className="text-2xl font-bold text-green-500">{data.summary.certified}</div></CardContent></Card>
              <Card className="bg-card/50"><CardContent className="p-3 text-center"><div className="text-[10px] text-muted-foreground uppercase">Provisional</div><div className="text-2xl font-bold text-amber-500">{data.summary.provisional}</div></CardContent></Card>
              <Card className="bg-card/50"><CardContent className="p-3 text-center"><div className="text-[10px] text-muted-foreground uppercase">Needs Improvement</div><div className="text-2xl font-bold text-red-500">{data.summary.needs_improvement}</div></CardContent></Card>
            </div>

            <Card className="bg-card/50">
              <CardHeader><CardTitle className="text-[13px]">Certification Table</CardTitle></CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border text-[10px] text-muted-foreground uppercase">
                      <th className="text-left py-2">Plugin</th>
                      <th className="text-center">Version</th>
                      <th className="text-center">Exec Time</th>
                      <th className="text-center">Status</th>
                      <th className="text-center">Certification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.plugins.map((p) => (
                      <tr key={p.name} className="border-b border-border/50 text-[11px]">
                        <td className="py-2 font-mono">{p.name}</td>
                        <td className="text-center text-muted-foreground">{p.version}</td>
                        <td className="text-center font-mono">{p.exec_time_ms.toFixed(3)}ms</td>
                        <td className="text-center">
                          <Badge variant={p.status === "ok" ? "default" : "destructive"} className="text-[9px]">{p.status}</Badge>
                        </td>
                        <td className="text-center"><CertificationBadge status={p.certification} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </>
        )}
      </QueryBoundary>
    </div>
  );
}
