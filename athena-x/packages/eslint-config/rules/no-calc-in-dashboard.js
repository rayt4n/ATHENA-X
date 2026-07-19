/**
 * Custom ESLint rule: bans arithmetic and Math.* calls in dashboard components.
 * Dashboard MUST only display, never calculate (Change 15).
 */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ban calculations in dashboard components (Change 15)',
      category: 'ATHENA-X Architectural Rules',
    },
    schema: [],
    messages: {
      noArithmetic: 'Dashboard cannot perform arithmetic ({{op}}). Calculations belong in the Python backend.',
      noMathCall: 'Dashboard cannot call Math.{{fn}}. Calculations belong in the Python backend.',
    },
  },
  create(context) {
    const filename = context.getFilename();
    if (!filename.includes('apps/nextjs-dashboard')) return {};
    return {
      BinaryExpression(node) {
        if (['+', '-', '*', '/', '%', '**'].includes(node.operator)) {
          context.report({ node, messageId: 'noArithmetic', data: { op: node.operator } });
        }
      },
      MemberExpression(node) {
        if (node.object?.name === 'Math') {
          context.report({ node, messageId: 'noMathCall', data: { fn: node.property?.name } });
        }
      },
    };
  },
};
