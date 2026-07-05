# StudyNexs static marketing site

Free landing site for **studynexs.com** — deployed via Cloudflare Workers (`wrangler deploy`).

## Pages

| File | URL |
|------|-----|
| `index.html` | `/` |
| `product.html` | `/product.html` |
| `pricing.html` | `/pricing.html` |
| `contact.html` | `/contact.html` |

## Deploy (Cloudflare Workers + GitHub)

**Build command:** *(empty)*  
**Deploy command:** `npx wrangler deploy`  
**Root directory:** repo root (`wrangler.toml` must be at root)

After push, attach custom domains in Cloudflare: `studynexs.com`, `www.studynexs.com`.

## Email

Set up Cloudflare **Email Routing**: `hello@studynexs.com` → your Gmail.

## Later

Full Next.js marketing from `apps/admin-web` can replace this on Cloudflare Pages or Vercel. School app stays at `app.studynexs.com` (OCI).
