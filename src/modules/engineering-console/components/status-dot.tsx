"use client";

import { cn } from "@/lib/utils";
import { healthColor } from "@/modules/engineering-console/lib/format";

interface StatusDotProps {
  state: string;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  className?: string;
}

export function StatusDot({ state, size = "sm", pulse = true, className }: StatusDotProps) {
  const dim = size === "lg" ? 10 : size === "md" ? 8 : 6;
  return (
    <span
      className={cn("inline-block rounded-full shrink-0", pulse && state !== "down" && "pulse-live", className)}
      style={{
        width: dim,
        height: dim,
        backgroundColor: healthColor(state),
        boxShadow: `0 0 ${dim}px ${healthColor(state)}66`,
      }}
    />
  );
}
