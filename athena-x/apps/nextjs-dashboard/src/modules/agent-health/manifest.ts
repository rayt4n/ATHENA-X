/**
 * Agent Health Dashboard Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const agentHealthManifest: ModuleManifest = {
    id: 'agent-health',
    name: 'Agent Health Dashboard',
    shortcut: 'HEALTH',
    description: 'Change 17 — live monitoring of all AI agents',
    version: '0.1.0',
    capabilities: {
        launchable: true,
        multiInstance: false,
        headless: false,
        defaultHotkey: '',
    },
    configSchema: null,  // STEP 4
    instanceStateSchema: null,  // STEP 4
    subscriptions: [],
    publications: [],
    publicAPI: {},  // STEP 4
    panelComponent: null,  // STEP 4
    agentFactory: null,
};
