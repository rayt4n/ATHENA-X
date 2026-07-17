/**
 * Technical Analysis Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const technicalAnalysisManifest: ModuleManifest = {
    id: 'technical-analysis',
    name: 'Technical Analysis',
    shortcut: 'TA',
    description: '23 TA agents + indicator matrix',
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
