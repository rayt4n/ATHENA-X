"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle } from "lucide-react";
import { type ReactNode } from "react";

// ============================================================================
// Loading state
// ============================================================================

export function WidgetLoading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center h-full min-h-[80px] text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin mr-2" />
      <span className="text-[11px]">{label}…</span>
    </div>
  );
}

// ============================================================================
// Error state
// ============================================================================

export function WidgetError({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-full min-h-[80px] text-red-500">
      <AlertCircle className="h-4 w-4 mr-2 shrink-0" />
      <span className="text-[11px]">{message}</span>
    </div>
  );
}

// ============================================================================
// Certification badge
// ============================================================================

export function CertificationBadge({ status }: { status: string }) {
  const variant =
    status === "CERTIFIED" || status === "VERIFIED"
      ? "default"
      : status === "PROVISIONAL"
        ? "secondary"
        : "destructive";
  const color =
    status === "CERTIFIED" || status === "VERIFIED"
      ? "bg-green-600 hover:bg-green-600 text-white"
      : status === "PROVISIONAL"
        ? "bg-amber-600 hover:bg-amber-600 text-white"
        : "bg-red-600 hover:bg-red-600 text-white";
  return (
    <Badge variant={variant} className={cn("text-[9px] px-1.5 py-0", color)}>
      {status}
    </Badge>
  );
}

// ============================================================================
// Widget card — standard container for every widget
// ============================================================================

export function WidgetCard({
  title,
  plugin,
  status,
  children,
  className,
  action,
}: {
  title: string;
  plugin?: string;
  status?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}) {
  return (
    <Card className={cn("border-border bg-card/50", className)}>
      <CardHeader className="pb-2 px-3 pt-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[12px] font-semibold">{title}</CardTitle>
          <div className="flex items-center gap-1.5">
            {action}
            {status && <CertificationBadge status={status} />}
          </div>
        </div>
        {plugin && <div className="text-[9px] text-muted-foreground font-mono">{plugin}</div>}
      </CardHeader>
      <CardContent className="px-3 pb-3">{children}</CardContent>
    </Card>
  );
}

// ============================================================================
// Query wrapper — handles loading + error states automatically
// ============================================================================

export function QueryBoundary({
  isLoading,
  isError,
  error,
  loadingLabel,
  children,
}: {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  loadingLabel?: string;
  children: ReactNode;
}) {
  if (isLoading) return <WidgetLoading label={loadingLabel} />;
  if (isError)
    return <WidgetError message={error?.message || "Failed to load data"} />;
  return <>{children}</>;
}
