#!/usr/bin/env tsx
/**
 * Regenerate TypeScript + Python event types from schemas/events/*.yaml.
 * Run: pnpm --filter @athena-x/event-schema generate
 */
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';

const SCHEMA_DIR = 'schemas/events';
const TS_OUT = 'packages/event-schema/src/generated.ts';
const PY_OUT = 'runtime/event-bus/src/athena_x_runtime_event_bus/generated.py';

function main() {
    const files = readdirSync(SCHEMA_DIR).filter(f => f.endsWith('.yaml'));
    const namespaces: Record<string, any> = {};

    for (const f of files) {
        const content = readFileSync(join(SCHEMA_DIR, f), 'utf8');
        const parsed = parse(content);
        namespaces[parsed.namespace] = parsed;
    }

    // Generate TypeScript
    const ts = generateTypeScript(namespaces);
    writeFileSync(TS_OUT, ts);
    console.log(`✓ Wrote ${TS_OUT}`);

    // Generate Python
    const py = generatePython(namespaces);
    writeFileSync(PY_OUT, py);
    console.log(`✓ Wrote ${PY_OUT}`);
}

function generateTypeScript(ns: Record<string, any>): string {
    return `// AUTO-GENERATED — do not edit. Run: pnpm --filter @athena-x/event-schema generate

` +
        `export const EVENT_NAMESPACES = ${JSON.stringify(Object.keys(ns), null, 2)} as const;
`;
}

function generatePython(ns: Record<string, any>): string {
    return `# AUTO-GENERATED — do not edit.

EVENT_NAMESPACES = ${JSON.stringify(list(ns.keys()))}
`;
}

main();
