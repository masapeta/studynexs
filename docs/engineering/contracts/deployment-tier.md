# Contract: deployment tier configuration (design only — P-R8)

No deployed configuration has been changed. Rolling these values out is a separate,
owner-approved configuration change.

| Variable | Where | Values | Default when unset |
|---|---|---|---|
| `DEPLOYMENT_TIER` | API | `development`, `internal`, `staging`, `demo`, `production` | `production` if `ENVIRONMENT=production`, else `development` |
| `NEXT_PUBLIC_DEPLOYMENT_TIER` | web (build-time) | same | `development` if `NODE_ENV=development`, else `production` |
| `NEXT_PUBLIC_DEMO_LOGIN_ENABLED` | web | `true` / unset | unset (off) |

- Internal tiers: `development`, `internal`. Only these mount the platform router and serve
  `/platform/engineering-status` (404 elsewhere) and the `/dashboard/platform/engineering` page
  (`notFound()` elsewhere).
- Production boot guard: `ENVIRONMENT=production` requires an explicit `DEPLOYMENT_TIER` of
  `staging`, `demo` or `production`. Missing, empty, invalid, `development` and `internal` all
  refuse to start, so internal engineering surfaces can never be served in production mode.
  `development`/`internal` remain valid only with `ENVIRONMENT=development`.
  **Deploying this change without setting it fails fast — set it before deploy.**
- Demo login picker shows only when the tier is `development` or `demo` **and**
  `NEXT_PUBLIC_DEMO_LOGIN_ENABLED=true`. No credentials are bundled; E2E harnesses read
  `E2E_PASSWORD_<USERNAME>` or `E2E_PASSWORD`. `npm run check:bundle` fails a build that contains
  demo credentials.
