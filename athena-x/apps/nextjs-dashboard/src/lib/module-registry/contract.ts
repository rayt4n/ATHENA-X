/**
 * ModuleManifest — the canonical contract every dashboard module implements.
 * Full implementation in STEP 4.
 */
export interface ModuleCapabilities {
    launchable: boolean;
    multiInstance: boolean;
    headless: boolean;
    defaultHotkey: string;
}

export interface ModuleManifest {
    id: string;
    name: string;
    shortcut: string;
    description: string;
    version: string;
    capabilities: ModuleCapabilities;
    configSchema: unknown | null;
    instanceStateSchema: unknown | null;
    subscriptions: string[];
    publications: string[];
    publicAPI: Record<string, unknown>;
    panelComponent: React.ComponentType<unknown> | null;
    agentFactory: (() => unknown) | null;
}
