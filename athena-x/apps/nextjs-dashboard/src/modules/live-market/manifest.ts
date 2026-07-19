/**
 * Live Market Data Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const liveMarketManifest: ModuleManifest = {
    id: 'live-market',
    name: 'Live Market Data',
    shortcut: 'MKT',
    description: 'Real-time market data ingestion display',
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
