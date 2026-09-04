# StudyNexs DNS And Cloudflare Inventory

> Operational DNS and Cloudflare deployment facts only. Do not store secrets here.

**Owner:** Avinash Reddy Masapeta  
**Last updated:** 2026-09-04

---

## Production domains

| Hostname | Intended surface | Current repo deployment anchor | Status |
|---|---|---|---|
| `studynexs.com` | Marketing site | Root Wrangler config target `studynexs-web` in `wrangler.toml` | Configured in repo |
| `api.studynexs.com` | API origin | Oracle VM origin at `140.245.202.69`; operator SSH target `ubuntu@140.245.202.69` | VM origin confirmed |
| `demo.studynexs.com` | Admin web custom domain | Admin web OpenNext/Wrangler target `academix-platform` in `apps/admin-web/wrangler.jsonc` | Live Cloudflare mapping unresolved |
| `app.studynexs.com` | Admin web custom domain | Admin web OpenNext/Wrangler target `academix-platform` in `apps/admin-web/wrangler.jsonc` | Live Cloudflare mapping unresolved |

---

## Cloudflare config anchors in this repo

| Surface | Config file | Configured target |
|---|---|---|
| Marketing site | `wrangler.toml` | `studynexs-web` |
| Admin web | `apps/admin-web/wrangler.jsonc` | `academix-platform` |
| Admin web package name | `apps/admin-web/package.json` | `academix-platform` |

`academix-platform` came from the admin web Cloudflare config and package metadata, not from the repository folder name. Running Wrangler inside `apps/admin-web` makes Wrangler resolve that local config name as the deployment target identifier.

---

## Cloudflare verification performed on 2026-09-04

Authenticated account verification completed locally with Wrangler.

Verified facts:

1. `wrangler whoami` succeeded for the currently authenticated account.
2. Worker deployment lookup for `academix-platform` failed with Cloudflare error `10007` (`This Worker does not exist on your account`).
3. Pages deployment lookup for `academix-platform` failed with Cloudflare error `8000007` (`Project not found`).
4. `wrangler pages project list` returned no Pages projects on the currently authenticated account.

Conclusion:

- The repo-configured admin web target name is `academix-platform`.
- On the currently authenticated Cloudflare account, `academix-platform` is not a live Worker script and not a live Pages project.
- Exact live custom-domain mapping for `demo.studynexs.com` and `app.studynexs.com` cannot be proven from this account alone.

Most likely explanations:

1. The live admin web is deployed from a different Cloudflare account.
2. The live admin web uses a different Worker or Pages project name than the repo config.
3. The Cloudflare deployment has not been created yet for this account.

---

## Next verification path

To close the mapping gap, verify one of the following in the correct Cloudflare account:

1. The Pages project list for the live account.
2. The live Worker script name if OpenNext is deploying as Workers.
3. The custom-domain bindings for `demo.studynexs.com` and `app.studynexs.com` in the Cloudflare dashboard.

Until that check is completed, treat the admin web Cloudflare mapping as unresolved in inventory rather than inferred.