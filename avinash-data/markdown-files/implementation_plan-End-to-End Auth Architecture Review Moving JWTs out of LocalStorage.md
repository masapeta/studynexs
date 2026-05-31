# End-to-End Auth Architecture Review: Moving JWTs out of LocalStorage

Currently, Academix handles authentication via the `staff-web` client making direct `axios` calls to the FastAPI monolith. The `/auth/login-password` and `/auth/verify-otp` endpoints return an `access_token` (15m) and `refresh_token` (30d) in the JSON body. The frontend stores both in `localStorage`, exposing the long-lived refresh token to any potential Cross-Site Scripting (XSS) vulnerability. 

To mitigate this, we have three primary architectural paths. Here is a comparison of each based on Security, Scalability, Robustness, and Efficiency.

---

## 1. Hybrid: HttpOnly Refresh Cookie + In-Memory Access Token

In this pattern, the backend API issues the long-lived `refresh_token` as an `HttpOnly`, `Secure` cookie mapped to the `/api/v1/auth/refresh` path. The `access_token` is still returned in the JSON body, but the frontend keeps it purely in JavaScript memory (React state/variables) instead of `localStorage`.

* **How it works:** On page load, the frontend makes a silent call to `/auth/refresh`. The browser automatically sends the `HttpOnly` refresh cookie, and the backend returns a fresh `access_token` in JSON. 
* **Security:** **Very High.** XSS cannot steal the refresh token (it's HttpOnly). XSS *could* theoretically steal the access token, but it expires in 15 minutes. It completely avoids CSRF vulnerabilities on standard API routes because they still require the `Authorization: Bearer <token>` header.
* **Scalability & Efficiency:** **Highest.** The frontend still talks directly to the backend API without any proxy layers, maintaining peak performance and minimal network hops.
* **Robustness:** High, but requires handling "silent refresh" logic in the frontend on initial page load, which you mostly already do in `AuthContext`.

## 2. Backend-for-Frontend (BFF) via Next.js

Since `staff-web` is a Next.js application, we can introduce a Next.js API layer (`/api/login`, `/api/proxy/*`). The browser only talks to the Next.js BFF, never directly to the Python backend.

* **How it works:** The Next.js BFF calls the Python backend for login, receives both tokens, and encrypts them into a single `HttpOnly` session cookie (e.g., using `iron-session`) stored on the browser. All subsequent API calls go to `/api/proxy/...` where the Next.js server decrypts the cookie and forwards the request to Python with the Bearer token.
* **Security:** **Extremely High.** Tokens never reach the browser at all. 
* **Scalability & Efficiency:** **Lower.** Every API request doubles in network hops (Browser -> Next.js -> Python). Proxying file downloads (like the printable fee receipts) or heavy analytics payloads can bottleneck the Node.js server.
* **Robustness:** Very high. This is the standard pattern for Next.js (e.g., Auth.js/NextAuth), making future transitions to Server-Side Rendering (SSR) seamless.

## 3. Pure Cookie Auth (Same-Domain API)

The backend API issues *both* the `access_token` and `refresh_token` as `HttpOnly` cookies. The frontend removes the `Authorization: Bearer` header entirely.

* **How it works:** The browser automatically attaches the cookies to every API request.
* **Security:** High against XSS, but introduces **Critical CSRF Risk**. Because cookies are sent automatically, any malicious site could trigger an API action if the user is logged in. 
* **Scalability & Efficiency:** Highest, direct API calls.
* **Robustness:** **Lowest.** Requires strict SameSite cookie policies, configuring CORS specifically for credentials, ensuring API and frontend share a root domain, and adding Anti-CSRF tokens to all POST/PUT/DELETE endpoints in the FastAPI monolith.

---

> [!IMPORTANT]
> ## My Recommendation: The Hybrid Approach (Option 1)
> 
> For Academix's current architecture (a heavily client-side Next.js SPA talking directly to a FastAPI monolith), **Option 1 (HttpOnly Refresh Cookie + In-Memory Access) is the most efficient and scalable solution.** 
> 
> It provides the exact security benefit you need—protecting the 30-day refresh session from XSS—without introducing the proxy overhead of a BFF or the CSRF complexities of pure cookie auth. 
> 
> **Implementation Steps for Hybrid:**
> 1. Update FastAPI `/login` and `/verify-otp` to set `refresh_token` as an `HttpOnly`, `Secure`, `SameSite=Strict` cookie on the path `/api/v1/auth/refresh`.
> 2. Update FastAPI `/refresh` to read the cookie instead of the JSON body.
> 3. Update FastAPI `/logout` to clear the cookie.
> 4. Update Next.js `AuthContext` and `api.ts` to stop storing/reading from `localStorage`. Instead, rely on Axios interceptors and memory.

> [!NOTE]
> If you plan to heavily adopt Next.js **App Router Server Components (RSC)** in the near future (where the server fetches data before sending HTML), **Option 2 (BFF)** is the better long-term investment, despite the proxy overhead.

## User Review Required

Please review the architectural options above. 

**Question:** Which path would you prefer to take? 
- If you prioritize **Efficiency and avoiding proxy overhead**, we should build the **Hybrid** approach.
- If you prioritize **Next.js ecosystem alignment and future SSR**, we should build the **BFF**. 

Let me know your decision, and I will execute the changes across the `api` and `staff-web` codebases!
