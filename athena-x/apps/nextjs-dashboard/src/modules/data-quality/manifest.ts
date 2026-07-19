/**
 * Data Quality Dashboard Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const dataQualityManifest: ModuleManifest = {
    id: 'data-quality',
    name: 'Data Quality Dashboard',
    shortcut: 'QUALITY',
    description: 'Change 18 — per-provider health metrics',
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
