# Zero-to-Revenue Infrastructure Plan
## Run at ₹0 Until 5 Paying Schools

> **Goal:** Spend as close to ₹0 as possible during pilot and early stages.
> Use free tiers strategically until revenue arrives to replace them.

---

## Important Clarification: Google AI Pro ≠ Free API

| What You Have | What It Gives You | For Our App? |
|---|---|---|
| **Google One AI Premium** (₹1,950/month) | Gemini chatbot, 2TB Google Drive, Workspace | ❌ CANNOT use for API calls |
| **Google AI Studio API (FREE tier)** | 1,500 API calls/day, Gemini Flash | ✅ YES — use this |

> Your Google One subscription and the API are completely separate products.
> The good news: **Google AI Studio's FREE API tier is generous enough for 1–3 schools.**
> Cancel Google One if you don't personally need it — it doesn't help the app.

---

## Free Tier Stack (What Each Service Gives You Free)

### Databases

| Service | Free Plan | Storage | Duration | Enough For |
|---|---|---|---|---|
| **Azure Database for PostgreSQL** | Flexible Server free tier | 32GB, 1 vCore, 4GB RAM | **12 months** ← countdown starts when you create it | 10+ schools |
| **MongoDB Atlas M0** | Shared cluster | 512MB | **Forever free** | 3–5 schools of AI session data |
| **Upstash Redis** | Serverless free | 256MB, 10,000 commands/day | **Forever free** | OTP + JWT blacklist for 3 schools |
| **Qdrant Cloud** | Free cluster | 1GB vectors | **Forever free** | RAG knowledge base for 3–5 schools |

### Compute (Running Your Services)

| Service | Free Plan | What Runs Free | Enough For |
|---|---|---|---|
| **Google Cloud Run** | 2M requests/month, 360,000 GB-seconds | Your FastAPI services | 5+ schools easily |
| **Vercel** | Hobby plan | Next.js frontend | Unlimited (hobby) |
| **Azure Container Apps** | 180,000 vCPU-seconds/month | Partial — borderline for 8 services | 1–2 schools |

> ✅ **Recommendation: Use Google Cloud Run** for backend services — most generous free compute tier.
> Your laptop Docker stays for development. Cloud Run for production.

### AI / LLM

| Service | Free Tier | Daily Limit | Enough For |
|---|---|---|---|
| **Gemini 1.5 Flash API** | Google AI Studio | **1,500 requests/day** | 1–2 schools with 65% cache |
| **Gemini 1.5 Pro API** | Google AI Studio | **50 requests/day** | Complex queries only — limited |
| **Ollama gemma3:4b local** | Your laptop | Unlimited | Emergency dev fallback |
| **edge-tts** | Free, no API key | Unlimited | TTS always free |

**Does 1,500 free API calls/day cover a school?**
```
Calculation (School with 500 students, 400 active/day):
  Raw queries: 400 students × 5 questions/day = 2,000 calls
  After 65% semantic cache: 2,000 × 0.35 = 700 actual API calls/day

700 calls/day < 1,500 free limit ✅ → 1 school is fully free!

For 2 schools: 1,400 calls/day → Still within free limit ✅
For 3 schools: 2,100 calls/day → Exceeds by 600 calls → ~$0.36/day extra
For 5 schools: 3,500 calls/day → ~$1.50/day over free limit = ₹3,780/month
```

### Storage, Auth, Notifications

| Service | Free Plan | Enough For |
|---|---|---|
| **Azure Blob Storage** | 5GB (12 months) | Profile photos for 10 schools |
| **Firebase FCM** | Free forever | Push notifications for any number |
| **SendGrid** | 100 emails/day free | Alerts for 5 schools easily |
| **MSG91** | Trial credits (~500 OTPs) | Pilot only |

---

## The Real Cost by Phase

### Phase 0: Building (Apr–Sep 2026) — ₹0/month
*Everything runs on your laptop via Docker Compose*

```
PostgreSQL    → Docker on laptop      ₹0
MongoDB       → Docker on laptop      ₹0
Redis         → Docker on laptop      ₹0
Qdrant        → Docker on laptop      ₹0
Gemini API    → Free tier (dev use)   ₹0
Frontend      → localhost:3000        ₹0
OTP           → Dev mode (console)    ₹0 ← OTP prints to screen, no SMS sent
─────────────────────────────────────────
TOTAL MONTHLY COST:                   ₹0
```

### Phase 1: Pilot (Sep 2026 – Mar 2027) — ₹500–₹2,000/month
*1 free school. Switch to cloud free tiers.*

| Service | Plan | Cost |
|---|---|---|
| Azure PostgreSQL | Free (12-month timer starts) | ₹0 |
| MongoDB Atlas | M0 forever free | ₹0 |
| Upstash Redis | Free tier | ₹0 |
| Qdrant Cloud | Free tier | ₹0 |
| Azure Blob | Free (12-month timer) | ₹0 |
| Google Cloud Run | Free tier (2M req/month) | ₹0 |
| Vercel (Next.js) | Hobby free | ₹0 |
| Gemini Flash API | Free 1,500/day | ₹0 |
| MSG91 OTP | Trial + low usage (500 users) | ₹500–₹1,000 |
| Firebase FCM | Free | ₹0 |
| SendGrid | Free 100/day | ₹0 |
| **TOTAL** | | **₹500–₹1,000/month** |

### Phase 2: Schools 2–5 Launch (Apr 2027 – Mar 2028) — ₹3,000–₹8,000/month
*3 paying schools. Some free tiers get saturated.*

| Service | Plan | Cost |
|---|---|---|
| Azure PostgreSQL | Free tier (months 7–12) | ₹0 (still free) |
| MongoDB Atlas | M0 free | ₹0 |
| Upstash Redis | May need paid (~$10) | ₹840 |
| Qdrant Cloud | Free (1GB still ok) | ₹0 |
| Azure Blob | Free (still in 12 months) | ₹0 |
| Google Cloud Run | Free (still covered) | ₹0 |
| Vercel | Hobby free | ₹0 |
| Gemini Flash API | Slightly over free = ~$1/day | ₹2,520 |
| MSG91 OTP | 3–5 schools = ~2,000 OTPs/month | ₹1,680 |
| Firebase FCM | Free | ₹0 |
| **TOTAL** | | **₹5,040–₹8,000/month** |

> **BUT:** By April 2027, you collect ₹11,25,000 from 3 schools.
> ₹8,000/month infra = just 0.7% of your monthly revenue. **Negligible!**

### When Azure 12-Month Free Tier Expires (Apr 2027 onwards)
*Switch to Google Cloud — it has its own free tier!*

| Azure Service Expires | Switch To | New Cost |
|---|---|---|
| Azure PostgreSQL | **Google Cloud SQL** free trial ($300 credit for 90 days) → then $15/month | ₹1,260 |
| Azure Blob Storage | **Google Cloud Storage** free tier (5GB/month) | ₹0 |
| Azure Redis | Already using Upstash paid | ₹840/month |
| **Total after switch** | | **~₹4,000–₹6,000/month** |

---

## The ₹0 Setup Guide (Step by Step)

### Step 1: Create These FREE Accounts Now

```
✅ Google AI Studio (FREE API key)
   → https://aistudio.google.com
   → Create API key → Free: 1,500 Flash calls/day

✅ MongoDB Atlas (FREE cluster)
   → https://www.mongodb.com/cloud/atlas
   → Create M0 cluster → Free forever, 512MB

✅ Upstash (FREE Redis)
   → https://upstash.com
   → Create Redis database → Free: 256MB, 10K commands/day

✅ Qdrant Cloud (FREE vector store)
   → https://cloud.qdrant.io
   → Create free cluster → 1GB forever free

✅ Google Cloud (FREE compute)
   → https://console.cloud.google.com
   → Enable Cloud Run → Free: 2M requests/month

✅ Vercel (FREE Next.js hosting)
   → https://vercel.com
   → Connect GitHub repo → Free hobby tier

✅ Firebase (FREE push notifications)
   → https://console.firebase.google.com
   → Enable FCM → Free forever

✅ Azure (FREE databases for 12 months)
   → https://azure.microsoft.com/free
   → Only activate when going live with pilot school
   → 12-month clock starts when you CREATE the resource
```

### Step 2: Update Your .env for Free Stack

```env
# ─── LLM (Google AI Studio FREE tier) ────────────────────────────────────────
GOOGLE_AI_API_KEY=AIza...from-aistudio.google.com
GEMINI_MODEL=gemini-1.5-flash      ← Use Flash (1,500/day free, not Pro's 50/day)
GEMINI_FALLBACK_MODEL=gemini-1.5-flash

# ─── PostgreSQL (Azure FREE 12 months) ───────────────────────────────────────
POSTGRES_URL=postgresql+asyncpg://sms_user:pass@<azure-free-server>.postgres.database.azure.com:5432/school_management

# ─── MongoDB (Atlas M0 FREE forever) ─────────────────────────────────────────
MONGODB_URL=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net

# ─── Redis (Upstash FREE forever) ────────────────────────────────────────────
REDIS_URL=rediss://default:pass@global-xxxx.upstash.io:6379

# ─── Qdrant (Cloud FREE forever) ─────────────────────────────────────────────
QDRANT_URL=https://xxxx.us-east-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# ─── OTP (MSG91 — only real cost) ────────────────────────────────────────────
MSG91_AUTH_KEY=your-key
MSG91_TEMPLATE_ID=your-template
```

---

## The Honest ₹0 Timeline

```
Month 1–5  (Apr–Aug 2026):  ₹0/month     Everything on laptop Docker
Month 6–12 (Sep 26–Mar 27): ₹500–1,000   Azure free tiers + MSG91 for pilot
Month 13   (Apr 2027):      ₹11,25,000 REVENUE IN ← 3 schools pay
Month 14+  (May 2027+):     ₹5,000–8,000  Some costs, tiny vs revenue
Month 25   (Apr 2028):      ₹43,09,500 REVENUE IN ← 7 schools pay
```

---

## What You Actually Need to Buy

### The ONLY unavoidable costs (not covered by any free tier):

| Item | Cost | Why Unavoidable |
|---|---|---|
| **MSG91 OTP SMS** | ₹0.15–₹0.25 per SMS | No free OTP tier. Real users need real SMS |
| **Domain name** | ₹800/year (~₹67/month) | yourschool.com for professional image |

**That's it.** Everything else has a free tier.

For 1 pilot school (500 students, 300 logins/month):
```
MSG91: 300 OTPs × ₹0.20 = ₹60/month
Domain: ₹67/month
───────────────────────────────
TOTAL REAL COST: ₹127/month ← This is your "break-even" number during pilot
```

---

## Revised 5-Year Cost With Free Tiers

| Year | Schools | Monthly Infra Cost | Monthly Revenue | Net Monthly |
|---|---|---|---|---|
| Year 1 | 0→1 (free) | **₹500–₹1,000** | ₹0 | -₹1,000 |
| Year 2 | 2–3 paying | **₹5,000–₹8,000** | ₹93,750 | +₹85,750 |
| Year 3 | 4–7 paying | **₹25,000–₹40,000** | ₹3,59,125 | +₹3,19,125 |
| Year 4 | 8–10 paying | **₹45,000–₹55,000** | ₹6,24,583 | +₹5,69,583 |
| Year 5 | 10 schools | **₹55,000–₹65,000** | ₹6,24,583 | +₹5,59,583 |

*(Monthly revenue = annual collection ÷ 12 smoothed)*

---

## Revised Bootstrap Capital Needed

```
Original plan:  ₹10,00,000 needed
With free tiers: ₹3,00,000–₹4,00,000 needed

Why only ₹3–4 lakh?
  → Laptop already exists (you have it)
  → No cloud bills during building phase
  → Pilot school costs only ₹1,000/month
  → You just need to cover your personal living expenses
    for 12–18 months until the first revenue cheque

Personal living: ₹25,000/month × 12 months = ₹3,00,000
SMS + Domain:    ₹5,000
Buffer:          ₹45,000
─────────────────────────────────
Required: ₹3,50,000 (₹3.5 lakh)
```

---

## Free Tier Expiry Calendar — Plan Ahead

| Free Tier | Expires | Action Before Expiry |
|---|---|---|
| Azure PostgreSQL | 12 months after you create it | Switch to Google Cloud SQL OR pay ($50/month) |
| Azure Blob Storage | 12 months | Switch to Cloudflare R2 (FREE 10GB forever!) |
| Azure Cache for Redis | 12 months | Upstash paid ($10/month) or Azure Basic ($16/month) |
| Gemini Flash API free | No expiry — usage limit | Add billing when 5 schools → $20/month max |
| MongoDB Atlas M0 | Never expires | Upgrade to M10 when storage hits 400MB |
| Qdrant Cloud | Never expires | Upgrade to paid when vectors > 900MB |
| Google Cloud Run | Never expires | Add billing only if > 2M req/month |
| Vercel Hobby | Never expires | Upgrade to Pro ($20/month) if team needed |

> 💡 **Pro Tip:** Create your Azure account fresh when you're ready to go live with the pilot school.
> That starts the 12-month free clock exactly when you need it.
> Don't create Azure resources during development — you'll waste free tier months.

---

## Summary

```
❓ Can you run at ₹0 until 5 schools?

✅ Building phase (6 months):    ₹0/month — laptop only
✅ Pilot (1 free school):        ₹127/month — just SMS + domain
✅ 2–3 paying schools:           ₹5,000–8,000/month infra
                                 Revenue: ₹93,750+/month
                                 Net profit: ₹85,000+/month ✅

You need ₹3.5 lakh bootstrap capital (personal savings)
to cover your living expenses for 12–18 months.

After April 2027 (first revenue):
You become self-sustaining. Infra costs are < 10% of revenue.
```

---

*Update FIVE_YEAR_PLAN.md Bootstrap Capital: ₹10L → ₹3.5L using free tiers*
