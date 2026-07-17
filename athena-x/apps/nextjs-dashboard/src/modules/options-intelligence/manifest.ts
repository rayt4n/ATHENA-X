/**
 * Options Intelligence Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const optionsIntelligenceManifest: ModuleManifest = {
    id: 'options-intelligence',
    name: 'Options Intelligence',
    shortcut: 'OPT',
    description: '15 options agents + chain + IV surface',
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
