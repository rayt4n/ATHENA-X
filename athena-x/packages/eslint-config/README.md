# @athena-x/eslint-config

Shared ESLint configuration enforcing module boundaries, no circular imports,
no dead code, no hardcoded values, and the **no-calc-in-dashboard** rule.

## Key rules

- `import/no-boundaries` — enforces the module dependency graph
- `import/no-cycle` — no circular imports
- `no-unused-vars` — no dead code (error, not warning)
- `no-constant-binary-expression` — catches dead branches
- `@athena-x/no-calc-in-dashboard` — bans arithmetic in `apps/nextjs-dashboard/**`
  except in approved utility files
- `@athena-x/no-hardcoded-values` — requires config extraction for magic numbers

## Usage

```json
// .eslintrc.json
{
  "extends": "@athena-x/eslint-config"
}
```
