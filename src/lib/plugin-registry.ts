/**
 * Plugin Registry — the Admin Dashboard reads this to build navigation
 * and discover workspace widgets. Plugins register themselves at module
 * load time. The sidebar reads getPlugins() to render the Plugins section.
 *
 * Future plugins (Research Lab, Strategy Builder, etc.) call
 * pluginRegistry.register(manifest) — no dashboard edits needed.
 */

import type { ComponentType } from "react";

// ============================================================================
// Types
// ============================================================================

export interface PluginRoute {
  path: string;
  label: string;
  icon?: string;
}

export interface WidgetRegistration {
  zone: "topbar" | "left" | "center" | "right" | "bottom";
  id: string;
  component: ComponentType<Record<string, unknown>>;
  order?: number;
  props?: Record<string, unknown>;
}

export interface PluginManifest {
  id: string;
  name: string;
  icon?: string;
  routes: PluginRoute[];
  widgets?: WidgetRegistration[];
  permissions?: string[];
  version: string;
  dependencies?: string[];
}

// ============================================================================
// Registry
// ============================================================================

class PluginRegistryImpl {
  private plugins = new Map<string, PluginManifest>();

  register(manifest: PluginManifest): void {
    this.plugins.set(manifest.id, manifest);
  }

  getPlugins(): PluginManifest[] {
    return Array.from(this.plugins.values());
  }

  getPlugin(id: string): PluginManifest | undefined {
    return this.plugins.get(id);
  }

  /** All routes from all plugins — for sidebar rendering */
  getRoutes(): { pluginId: string; pluginName: string; routes: PluginRoute[] }[] {
    return this.getPlugins().map((p) => ({
      pluginId: p.id,
      pluginName: p.name,
      routes: p.routes,
    }));
  }
}

export const pluginRegistry = new PluginRegistryImpl();
