/**
 * Dashboard preset — adds the no-calc-in-dashboard rule (Change 15).
 * Applied only to apps/nextjs-dashboard.
 */
module.exports = {
  extends: ['../index.js'],
  rules: {
    '@athena-x/no-calc-in-dashboard': 'error',
  },
  overrides: [
    {
      files: ['lib/utils/**', 'lib/format/**'],
      rules: { '@athena-x/no-calc-in-dashboard': 'off' },
    },
  ],
};
