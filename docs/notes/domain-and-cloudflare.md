# Domains, DNS, and Cloudflare Configuration

What a domain *is* at a technical level, the things you should
configure once you own one, and the specific Cloudflare settings that
matter for this project (`signalnest.app`). Pairs with
[`buying-a-domain.md`](buying-a-domain.md), which covers the purchase
itself.

---

## 1. What a domain actually is

A **domain name** is a human-friendly label that maps to one or more
machine addresses (and other records) through the **Domain Name System
(DNS)**. The mapping is published and authoritative, not stored on your
laptop.

The pieces, working from the user's URL inward:

```
https://app.signalnest.app/feedback?id=42
        └─┬─┘ └────┬────┘ └─┬┘
          │        │        └─ TLD (top-level domain) — sold by a registry
          │        └──────────  Apex / second-level — what you bought
          └───────────────────  Subdomain (label under apex)
```

- **Apex (or root)** — `signalnest.app`. The thing on your invoice.
- **Subdomains** — `app.signalnest.app`, `www.signalnest.app`,
  `api.signalnest.app`. You can create as many as you want without
  paying extra; they're just DNS records.
- **TLD** — `.app`. Owned by a registry (Google, in this case). Some
  TLDs have technical features (`.app` and `.dev` are HSTS-preloaded,
  meaning every browser refuses to talk to them over plain HTTP).
- **Registrar** — where you bought the domain (Cloudflare, here).
- **Authoritative nameservers** — the DNS servers that hold the
  *truth* about your domain's records. With Cloudflare Registrar these
  are Cloudflare's nameservers (`*.ns.cloudflare.com`).
- **Resolvers** — what the browser/OS asks. They cache results from
  the authoritative nameservers, which is why DNS changes take time
  to propagate (caches expire by **TTL**).

### Records you'll actually use

| Type | What it does | When to use |
| --- | --- | --- |
| `A` | Maps a name to an IPv4 address. | When the target is a fixed IPv4. |
| `AAAA` | Same, but IPv6. | Modern equivalent of `A`. |
| `CNAME` | Alias one name to another name. | Pointing a subdomain at a platform-provided host (Railway, Vercel, GitHub Pages). **Cannot exist at the apex** by spec — Cloudflare uses "CNAME flattening" to fake it. |
| `MX` | Mail servers for email at this domain. | If you're using domain email (Fastmail, Google Workspace). |
| `TXT` | Arbitrary text. | SPF, DKIM, DMARC, domain-verification challenges. |
| `CAA` | Restricts which CAs can issue certs for this domain. | Defense-in-depth. Optional. |

### Things that are *not* the domain

- **The website.** A domain without a server it points to is just an
  empty record. You configure the *server* (Railway, in our case) and
  then create a DNS record that points the domain at it.
- **Email.** Owning `signalnest.app` does not give you
  `you@signalnest.app` until you connect a mail provider via `MX` and
  TXT records.
- **HTTPS certificates.** Issued by a Certificate Authority (Let's
  Encrypt, Google Trust Services, Cloudflare's edge cert) based on
  your DNS records, not the domain registration. Most platforms
  (Railway, Cloudflare) provision these automatically once DNS is
  pointing at them.

---

## 2. Cloudflare configuration for `signalnest.app`

The settings below are what's recommended for this project and why.
Most are Cloudflare's defaults; the ones that need explicit action are
flagged.

### 2.1 Account and registration hygiene

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| Account security | Two-factor authentication | **Enable now.** Use TOTP (authenticator app) plus at least one hardware key if you have one. Save backup codes offline. | Your Cloudflare account controls the domain, the DNS, and the proxy in front of the app. Losing the account is worse than losing the app. |
| Billing / registration | Auto-renew | **Leave enabled.** Cloudflare enrolls Registrar domains in auto-renew by default; renewals run at registry list price. ([docs](https://developers.cloudflare.com/registrar/account-options/auto-renew/)) | A lapsed domain is far more painful to recover than the cost of a year of renewal — sometimes you just lose it. |
| Domain privacy | WHOIS / RDAP redaction | **Confirm it is active.** Cloudflare advertises free WHOIS redaction for registrant contact details. ([source](https://www.cloudflare.com/products/registrar/)) | Plain WHOIS publishes your real name/address/email otherwise. Spam follows. |
| DNSSEC | Enable DNSSEC | **Recommended; not urgent before launch.** Cloudflare supports free one-click DNSSEC activation. ([docs](https://developers.cloudflare.com/dns/dnssec/)) | Protects against DNS spoofing/cache poisoning. Free, low-risk; flip it on. |
| Account access | Audit log | Skim it monthly. | Catches "logged in from a country I've never been to" early. |

### 2.2 DNS

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| DNS records | Don't add records yet beyond what Railway/email require | **Hold.** Add only when there's something live to point at. | Random `A`/`CNAME` records are how you end up with a stale record pointing at a 2-year-old test deploy. Keep the zone tidy. |
| Proxy / orange cloud | Records pointing at Railway | **DNS-only (grey cloud)** until the Railway custom domain works end-to-end, then revisit. | Railway terminates TLS itself. Putting Cloudflare's proxy in front means two layers of TLS and CDN — debug-able, but not what you want during initial setup. |
| TTL | Defaults | **Auto.** | Cloudflare picks sensible TTLs (1 minute behind the proxy, longer for grey-cloud). |
| CAA | Optional `0 issue "letsencrypt.org"` (or whichever CA Railway uses) | **Skip for v1.0.** | CAA misconfig blocks cert issuance. Add later only if you understand which CA actually issues your cert. |

### 2.3 SSL/TLS — the part most projects misconfigure

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| SSL/TLS encryption mode | **Full** until the Railway custom domain is verified, then **Full (strict)** | When proxied, Cloudflare needs to know *how* to talk to the origin. **Full** = TLS to origin without verifying its cert. **Full (strict)** = TLS to origin *and* verify the cert chain. ([docs](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)) | Anything below Full ("Flexible") is a trap — Cloudflare↔origin is plain HTTP, the user sees a padlock, the connection is *not* end-to-end encrypted. Don't ever pick Flexible. |
| Always Use HTTPS | **Enable after the Railway custom domain works.** | Forces HTTP → HTTPS redirect at the Cloudflare edge. | `.app` is HSTS-preloaded already, so browsers refuse plain HTTP regardless. Redundant but harmless. Defer until the domain is wired up so debug requests aren't auto-redirected mid-investigation. |
| Minimum TLS version | **TLS 1.2** (default). Move to 1.3-only later. | TLS 1.0/1.1 are dead. | A small portfolio app has no reason to support old TLS. |
| Automatic HTTPS Rewrites | **On.** | Rewrites `http://` → `https://` in HTML returned through the proxy. | Defense-in-depth for any hardcoded `http://` link in templates. |
| HSTS | **Skip.** | Adding HSTS via Cloudflare overrides what the origin sets. | `.app` is preloaded; browsers already enforce HTTPS. Adding another HSTS layer makes it harder to undo if something breaks. |

### 2.4 Security & WAF

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| WAF managed rules | **Defaults.** | Cloudflare's free tier ships sane defaults (Cloudflare Managed Ruleset on a quota of evaluations). | Bespoke rules early are how you start blocking your own API requests during dev. |
| Bot Fight Mode | **Off until launch, then On.** | It will challenge `curl` and CI smoke tests. Turn on once you stop scripting against the live URL constantly. | Trade-off between aggressive bot blocking and developer ergonomics. |
| Rate limiting | **None for v1.0.** | Free plan caps you to 10k req/mo of rate-limit evaluations anyway. | Add only when you have a specific abuse pattern to defend against. |
| Page Rules / Configuration Rules | **None.** | One default cache behavior is plenty for a backend API + static HTML app. | Page Rules are where over-configuration starts. |

### 2.5 Analytics

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| Cloudflare Analytics | **On (default).** | Aggregate traffic counts, bandwidth, threats blocked. No client-side script, no PII. | Useful and privacy-respecting. |
| Web Analytics (cf-beacon JS) | **Off until you have a privacy page.** | Adds a small JS beacon to capture page-view metrics. | First-party-ish but still client-side. Don't ship analytics until you've documented them somewhere visible. |

### 2.6 Email (deferred)

| Area | Setting | Recommendation | Why |
| --- | --- | --- | --- |
| Email Routing | **Don't enable until you actually want email at the domain.** | Forwards `you@signalnest.app` to your real inbox for free. | Once enabled, it adds `MX` records you'll have to remember when debugging DNS later. Defer. |
| SPF / DKIM / DMARC | **Add only after enabling email.** | Authentication records that prevent spoofing. | Adding these without active email leaves dangling records. |

---

## 3. Things this project will need (later)

Concrete records to plan for once Phase 8 is done and the Railway
custom domain step starts:

- **One `CNAME`** — `signalnest.app` (or `app.signalnest.app`)
  pointing at the Railway-provided host (e.g.
  `<service>.up.railway.app`). DNS-only (grey cloud) initially.
- **No `A`/`AAAA` at apex** — let Cloudflare's CNAME flattening
  handle the apex. Don't paste IPs manually; Railway can rotate them.
- **TXT verification** — Railway requires a one-off TXT record to
  verify domain ownership before issuing a cert. Add, wait for
  verification, leave it in place.
- **Status check after wiring:** `dig +short signalnest.app CNAME`
  and `curl -sI https://signalnest.app/health` should both succeed
  before flipping the proxy on.

---

## 4. Pushback on the original config table

The original recommendations I was given lined up with Cloudflare's
own guidance, with two small caveats:

- **"SSL/TLS mode → Full / Full strict when connected."** Agreed, but
  the order matters: start at **Full** during the Railway hand-off,
  flip to **Full (strict)** *after* Cloudflare has verified the
  origin cert. Going straight to Full (strict) before the cert chain
  is verifiable produces 525/526 errors that look like Cloudflare
  outages and aren't.
- **"WAF / security rules — leave defaults mostly alone."** Agreed.
  I'd add: explicitly *disable* Bot Fight Mode during initial
  development, because it will block `curl` smoke tests and CI
  probes. Re-enable after launch.

Everything else (2FA, auto-renew, WHOIS redaction, DNSSEC, restrained
DNS, deferred Always-Use-HTTPS, conservative analytics) matches what I
would recommend independently. Adopted as-is.

---

## 5. Things I'd add

- **Account recovery is configured before anything is built on the
  domain.** Verify the recovery email at the Cloudflare account level,
  print backup 2FA codes, store them offline.
- **`audit log` reviewed monthly** for the first six months. Catches
  surprises early.
- **No third-party "DNS managers" or domain "boosters."** If a
  service asks for your Cloudflare API token to "optimize" DNS,
  decline. The native dashboard is enough for v1.0.
- **Document the zone in this repo.** Once records exist, add a brief
  table to [`how-deployment-works.md`](how-deployment-works.md) listing
  what each record is for. Future-you will not remember.
