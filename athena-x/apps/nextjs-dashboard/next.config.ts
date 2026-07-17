import type { NextConfig } from 'next';

const config: NextConfig = {
    turbopack: {
        transpilePackages: ['@athena-x/ui-kit', '@athena-x/event-schema', '@athena-x/types'],
    },
    webpack: (cfg) => {
        cfg.externals = cfg.externals || [];
        return cfg;
    },
    experimental: {
        serverActions: { bodySizeLimit: '10mb' },
    },
};

export default config;
