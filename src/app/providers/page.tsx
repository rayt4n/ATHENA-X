"use client";

import { ProviderSettings } from "@/modules/provider-orchestrator/components/provider-settings";

/**
 * Provider Settings page — Stage 16A.
 *
 * This is NOT the trader terminal (/) or the engineering console (/engineering-console).
 * It's a standalone settings page for the Provider Orchestrator.
 */
export default function ProvidersPage() {
  return <ProviderSettings />;
}
