/**
 * Market Intelligence Module Manifest
 */
import type { ModuleManifest } from '@/lib/module-registry/contract';

export const marketIntelligenceManifest: ModuleManifest = {
    id: 'market-intelligence',
    name: 'Market Intelligence',
    shortcut: 'MI',
    description: 'Forecast + Scenario + Regime + Volatility + Expected Move + Prob Tree + Consensus',
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
