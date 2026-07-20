/**
 * ATHENA-X Plugin Manifest
 *
 * Registers ATHENA-X as a plugin in the Admin Dashboard.
 * The sidebar reads routes from this manifest.
 * The workspace reads widgets from this manifest.
 *
 * To add a new plugin (e.g., "Research Lab"), create a similar
 * manifest file and import it in layout.tsx. No dashboard edits needed.
 */

import { pluginRegistry, type PluginManifest } from "@/lib/plugin-registry";
import { workspaceRegistry } from "@/lib/workspace-registry";

// ============================================================================
// Plugin Manifest
// ============================================================================

const athenaManifest: PluginManifest = {
  id: "athena-x",
  name: "ATHENA-X",
  icon: "trending-up",
  version: "17.4.0",
  routes: [
    { path: "/dashboard/athena/workspace", label: "Trading Workspace", icon: "activity" },
    { path: "/dashboard/athena/technical", label: "Technical", icon: "layers" },
    { path: "/dashboard/athena/options", label: "Options", icon: "cpu" },
    { path: "/dashboard/athena/ai", label: "AI", icon: "brain" },
    { path: "/dashboard/athena/evidence", label: "Evidence", icon: "shield" },
    { path: "/dashboard/athena/reports", label: "Reports", icon: "file-text" },
    { path: "/dashboard/athena/plugins", label: "Plugins", icon: "puzzle" },
  ],
  widgets: [],
  permissions: [],
  dependencies: [],
};

// ============================================================================
// Register
// ============================================================================

pluginRegistry.register(athenaManifest);

// Workspace widgets are registered dynamically in workspace-composition.tsx
// because they need React component references (which must be imported in
// a .tsx file, not a .ts file).

export { athenaManifest };
