# Buying a Domain — Personal Playbook

Notes on how to actually purchase a domain name for a small project,
which services are worth using, and the verification steps that catch
problems before money changes hands. Pairs with
[`domain-and-cloudflare.md`](domain-and-cloudflare.md), which covers
**what to do after** you own one.

> Status (May 2026): bought `signalnest.app` through Cloudflare
> Registrar. The notes below match that path, with detours noted for
> when Cloudflare can't sell the name (premium domains, certain TLDs).

---

## 1. Vocabulary you need before clicking "buy"

| Term | What it actually means |
| --- | --- |
| **Registrar** | The company that sells you the domain and records you as the registrant in the registry. Examples: Cloudflare, Namecheap, Porkbun, GoDaddy. |
| **Registry** | The wholesale operator of a TLD (e.g. Verisign for `.com`, Google for `.app`). Registrars buy from registries; you buy from registrars. |
| **TLD** | Top-level domain — the last segment (`.com`, `.app`, `.dev`, `.io`, `.co.uk`). Different TLDs have different prices and rules. |
| **Premium domain** | A name the registry has flagged as "high value" and listed at a multiple of the standard wholesale price (often $1,000–$1,000,000). The registrar can only sell it at that price; they aren't allowed to discount it. Common on short, dictionary-word, or trend-aligned names. |
| **Aftermarket / secondary market** | Domains owned by a previous registrant who is reselling. Sold via marketplaces (Sedo, Afternic, Dan, GoDaddy Auctions). Prices are negotiable; transfer is a separate step from buying a fresh name. |
| **WHOIS / RDAP** | Public records identifying the registrant, registrar, and key dates for a domain. Most registrars now offer free privacy/redaction so your real address isn't published. |
| **DNSSEC** | Cryptographic signing of DNS records. Protects against DNS spoofing. Free at most modern registrars. |
| **Auto-renew** | Automatic yearly renewal at the registry list price. Default-on at Cloudflare; default-off at some registrars — check this. Letting a domain expire and getting it back is painful and sometimes impossible. |

---

## 2. Where to look up a domain *before* buying it

Always check at least one source other than the registrar's search box —
the registrar's box can lie (or rate-limit) and may show "available"
prices that exclude premium markup until you click into checkout.

| Tool | What it tells you |
| --- | --- |
| <https://lookup.icann.org/en> | Authoritative WHOIS / RDAP lookup. Use this to confirm which registrar holds an existing domain, who the registrant is (if not redacted), and key dates. ICANN's own tool, no upsell. |
| <https://who.is/> | Mirror of the same data with a friendlier UI. Faster than ICANN for casual checks. |
| <https://rdap.org/> | Direct RDAP gateway. Useful when WHOIS is being rate-limited or returning truncated output. |
| <https://www.dnschecker.org/> | Resolves a name from many global DNS resolvers. Good for "is this domain *actually* dead, or just dead from my ISP?" |
| Registrar search (Cloudflare, Porkbun, Namecheap) | Use for price comparison, not as the final word on availability. |

**Rule of thumb:** if the registrar shows "available" but ICANN
lookup shows an active registration, refresh — you're seeing a stale
cache, not a deal.

---

## 3. Where to actually buy

The shortlist for a small portfolio/side-project domain.

### Cloudflare Registrar — default choice

- **Sells at registry cost.** No retail markup, no gotcha "second-year"
  pricing. (<https://www.cloudflare.com/products/registrar/>)
- Free WHOIS privacy (registrant contact details redacted by default).
- Free DNSSEC, one-click activation.
- Auto-renew on by default.
- Tightly integrated with Cloudflare DNS (which you'll want anyway).
- **Limits:** can only register names you don't already own elsewhere
  *and* aren't flagged premium. They will not sell premium domains
  even if the TLD supports it.
- **Verify before buying:** use Cloudflare's own search at
  <https://dash.cloudflare.com/?to=/:account/domains/register> while
  signed in. Confirm the price you see is "registry fee" — not "first
  year promo."

### Porkbun, Namecheap — alternates

- Slightly higher than registry cost but still cheap, and they sell
  some TLDs Cloudflare doesn't carry.
- Sometimes have promotional first-year pricing — read the renewal
  price before buying.
- WHOIS privacy is free at both.
- Use these when Cloudflare doesn't offer the TLD you want.

### GoDaddy — for premium / aftermarket only

- Sells **premium domains** (registry-flagged high-value names).
  Cloudflare won't carry these; if you must have one, GoDaddy or the
  marketplace platforms (Sedo, Dan, Afternic) are where they live.
- Treat their search results as a sales funnel — premium domains will
  be heavily upsold and bundled with hosting/email you don't need.
- Renewals are full retail, not registry cost. **Move the domain to
  Cloudflare after the first year** by transferring it (most TLDs
  allow transfer-out 60 days after registration).

### Other paths worth knowing

- **Aftermarket (Sedo, Dan, Afternic):** for negotiating with a
  current owner. Use escrow (Escrow.com or the marketplace's built-in
  escrow). Never wire money outside escrow.
- **Direct WHOIS contact:** the registrant of an unused domain is
  sometimes willing to sell at a sane price. Polite, low-effort email;
  expect 90% silence. Only works if WHOIS isn't redacted.

---

## 4. Pre-purchase verification checklist

Run through this *before* clicking buy — five minutes here saves real
money.

- [ ] **Spell the name out loud.** "S-I-G-N-A-L-N-E-S-T-dot-app." If
      it's ambiguous over the phone, you'll regret it. Avoid hyphens,
      avoid numbers that look like letters (`0`/`O`, `1`/`l`/`I`).
- [ ] **ICANN WHOIS lookup**: <https://lookup.icann.org/en>. Confirm
      the name is genuinely unregistered, or that the existing
      registration is expiring soon (within 30 days) if you intend to
      drop-catch.
- [ ] **Trademark check.** The USPTO's TESS search at
      <https://www.uspto.gov/trademarks/search>, plus a plain Google
      search of the brand name. Picking a name that's already a live
      trademark in your industry is asking for a UDRP dispute.
- [ ] **Search the name on GitHub, npm, PyPI, the App Store.** Even
      if it's not trademarked, a clash with an existing software
      product is a long-term headache.
- [ ] **Pricing sanity check.** Compare the registrar's price against
      the registry list price. For `.app`, registry fee is set by
      Google; if Cloudflare quotes ~$14/year and another registrar
      quotes $40, the difference is markup.
- [ ] **Confirm renewal price, not just first-year price.** A $1
      first-year promo that renews at $20 is fine; a $1 first-year
      that renews at $80 is a trap.
- [ ] **Check the TLD's restrictions.** `.app` and `.dev` are
      [HSTS preloaded](https://hstspreload.org/) — they only work
      over HTTPS, ever. That's a feature for a real app and a problem
      for a static demo on `http://`. Some TLDs require a local
      presence (`.us`, `.de`, `.ca`).
- [ ] **Decide on the registrar before searching at multiple
      registrars.** Some registrars run "premium availability"
      searches that flag a name as recently-searched, which can drive
      price increases on the secondary market. (Conspiracy-tier but
      it's been documented enough to warrant caution.)

---

## 5. The actual purchase (Cloudflare path)

1. Sign in at <https://dash.cloudflare.com/>.
2. Account home → **Domain Registration** → **Register Domains**.
3. Search for the name. Confirm:
   - Price line says "Registration fee" not "Premium."
   - Renewal price matches.
   - WHOIS privacy is checked (it should be by default).
4. Add to cart, pay. Cloudflare sets auto-renew on by default and the
   nameservers point at Cloudflare's resolvers automatically.
5. **Immediately** verify two things:
   - Account → Profile → **Authentication** → 2FA is enabled.
     (Domain control == account control. Lose the account, lose the
     domain.)
   - Domain → DNS → **DNSSEC** is on (one click).
6. Open <https://lookup.icann.org/en>, paste the domain, confirm:
   - Registrar is "Cloudflare, Inc."
   - Registrant is redacted (privacy active).
   - Status includes `clientTransferProhibited` (default lock).

That's the whole purchase. Configuration after this lives in
[`domain-and-cloudflare.md`](domain-and-cloudflare.md).

---

## 6. Post-purchase: red flags that mean *act now*

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Receive a paper or PDF "domain renewal invoice" by mail or email from a company you didn't buy from | Slamming scam — they want you to transfer the domain to them. | Ignore. Verify by signing in at your real registrar. |
| ICANN WHOIS shows a different registrar than where you bought | Registrar account compromise *or* an unauthorized transfer. | Disable transfers, change password, contact registrar support. |
| Domain stops resolving a year in | Auto-renew failed (expired card, declined payment). | Renew immediately. Most TLDs have a 30-day grace + 30-day redemption window before the name drops. |
| Browser shows certificate error on first deploy | TLD is HSTS-preloaded (e.g. `.app`) and you don't have HTTPS configured yet. | Configure HTTPS / let the platform (Railway, Cloudflare) provision a cert before pointing DNS. |

---

## 7. What "done" looks like

The buy is finished — and the domain is *yours* — when:

1. ICANN WHOIS confirms registrar = where-you-bought, registrant
   redacted, status locked.
2. Auto-renew is on with a payment method that won't expire next month.
3. 2FA is on at the registrar account.
4. DNSSEC is enabled.
5. You haven't created any DNS records yet — that comes when you have
   something to point at.

Anything beyond this is configuration, not purchase. See
[`domain-and-cloudflare.md`](domain-and-cloudflare.md).
