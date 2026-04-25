# Bug Bounty Program

> **⚠️ THIS IS A TEMPLATE — NOT AN ACTIVE BUG BOUNTY PROGRAM**
>
> **This document is an example only. It is NOT active for this repository.**
> **Do not submit vulnerability reports expecting rewards for this template repo.**
>
> To use this template: copy it to your own repository, replace all
> placeholders (marked with `TODO`), and link it from your SECURITY.md.

<!-- TODO (template users): Before publishing this file:
     1. Replace ALL `[OWNER]/[REPO]` placeholders with your actual repo path
     2. Replace ALL email placeholders with your real security contact
     3. Set actual reward amounts or remove the monetary rewards section
     4. Replace `[PROJECT NAME]` and `[package-name]` with real values
     5. Review each section — remove anything that doesn't apply to your project
     6. Delete the template warning banner at the top
     7. Consider having legal counsel review before making bounty commitments -->

## Overview

We offer rewards for responsibly disclosed security vulnerabilities in
[PROJECT NAME]. This program encourages security researchers to help us
identify and fix vulnerabilities before they can be exploited.

> **Legal disclaimer:** Nothing in this document creates a legal obligation
> to pay. All rewards, if any, are offered at our sole discretion based on
> the severity, impact, and quality of the report.

## Scope

### In Scope

<!-- TODO (template users): Replace all placeholders below with your actual values.
     Remove lines that don't apply (e.g., Documentation site if you don't have one). -->

The following are eligible for rewards:

- **Primary repository:** `https://github.com/[OWNER]/[REPO]`
- **Official releases:** Packages published to PyPI under `[package-name]` (latest stable release and currently supported versions)
- **Documentation site:** `https://[your-docs-domain].com` (if applicable)
- **Only assets owned/operated by us** — We can only authorize testing on infrastructure we control
- **Only vulnerabilities that affect confidentiality, integrity, or availability in a meaningful way** — Theoretical issues or best-practice deviations without real-world impact are out of scope

### Version Coverage

<!-- TODO (template users): Specify which versions are in scope.
     Align with your release policy (see docs/release-policy.md if available).
     Keep this table in sync with SECURITY.md's Supported Versions table. -->

| Version                                 | In Scope                          |
| --------------------------------------- | --------------------------------- |
| Latest stable release                   | ✅ Yes                            |
| Supported versions (per release policy) | ✅ Yes                            |
| Unsupported / EOL versions              | ❌ No                             |
| Pre-release / beta                      | ❌ No (unless explicitly invited) |

### Vulnerability Types

<!-- TODO (template users): Replace $X values with your actual reward amounts,
     or remove monetary rewards entirely and offer recognition only.
     See the "Reward Payment" section below for payment method options. -->

| Severity     | Examples                                                           | Reward Range     |
| ------------ | ------------------------------------------------------------------ | ---------------- |
| **Critical** | Remote code execution, authentication bypass, data breach          | $[X] – $[Y]      |
| **High**     | Privilege escalation, significant data exposure, injection attacks | $[X] – $[Y]      |
| **Medium**   | Cross-site scripting (XSS), CSRF, information disclosure           | $[X] – $[Y]      |
| **Low**      | Minor information leaks, theoretical attacks                       | Recognition only |

> **⚠️ Template Note:** Rewards are discretionary. Projects using this template may offer recognition only, swag, or no rewards at all. Adjust or remove this table based on your actual budget and commitment.

> **Severity calibration:** We use [CVSS 3.1](https://www.first.org/cvss/calculator/3.1) or similar frameworks to help calibrate severity. Final severity is determined by the maintainers based on actual impact to this project.

> **Minimum for monetary rewards:** Only Medium severity and above are eligible for monetary rewards (if offered). Low severity issues receive recognition in our Hall of Fame.

### Out of Scope

The following are **not eligible** for rewards:

- Vulnerabilities in third-party dependencies (report to upstream)
- Issues requiring physical access to a user's device
- Social engineering attacks (phishing, etc.)
- Denial of service (DoS/DDoS) attacks
- Issues in non-production environments (staging, dev)
- Previously reported vulnerabilities
- Vulnerabilities disclosed publicly before we can address them
- Automated scanner output without proof of exploitability
- Best-practice findings with no demonstrable security impact (e.g., missing headers without exploit path)
- Rate-limit bypass claims without demonstrated security impact
- **User-hosted deployments / forks / self-hosted instances** — Unless explicitly included above, we cannot authorize testing on infrastructure we don't control

---

## Rules of Engagement

To qualify for a reward, you must:

1. **Report privately** — Do not disclose publicly until we've released a fix
2. **Provide details** — Include steps to reproduce, impact assessment, and PoC
3. **Act in good faith** — Do not access, modify, or delete user data
4. **Test responsibly** — Only test against your own instances or with explicit permission
5. **One report per issue** — Do not submit duplicates or variants of the same issue

### Duplicate Reports

If multiple researchers report the same vulnerability:

- The **first valid report** receives the full reward
- Subsequent reports may receive partial recognition (but no monetary reward)
- We determine duplicates based on the timestamp of the report submission
- If reports arrive within the same 24-hour period with substantially different details, we may split the reward at our discretion

### Safe Harbor

We will not pursue legal action against researchers who:

- Follow the rules outlined in this policy
- Act in good faith to avoid privacy violations and service disruption
- Report vulnerabilities promptly and work with us on remediation

> **⚠️ Important:** Safe harbor applies only to authorized testing within the scope of this policy and does not permit unlawful access to systems, data exfiltration, or any activity that violates applicable laws. When in doubt, ask before testing.

---

## How to Report

<!-- TODO (template users): Replace [OWNER]/[REPO] and security email with your
     actual values. Ensure GitHub Security Advisories are enabled in your repo
     settings (Settings → Security → Private vulnerability reporting);
     otherwise the advisory link below will 404. -->

**If you are using this as a template:** Replace the link, email, and all
placeholders below before publishing. Do not ship this file with example values.

1. **Preferred:** [GitHub Security Advisory](https://github.com/[OWNER]/[REPO]/security/advisories/new)
 <!-- TODO (template users): Replace `[OWNER]/[REPO]` with your actual repo path -->
2. **Email:** `[security-email]@[your-domain].com`
 <!-- TODO (template users): Replace with your actual security email -->
3. **PGP Encrypted:** See key details below (if available)

<!-- TODO (template users): Add your PGP key fingerprint (full 40-character format),
     or remove this option entirely if you don't use PGP:
     Key fingerprint: `XXXX XXXX XXXX XXXX XXXX  XXXX XXXX XXXX XXXX XXXX`
     Public key: https://keys.openpgp.org/search?q=security@example.com
-->

For general security information, see our [Security Policy](../../SECURITY.md).

### What to Include

- **Summary:** Brief description of the vulnerability
- **Severity:** Your assessment (Critical/High/Medium/Low)
- **Steps to Reproduce:** Detailed instructions or proof-of-concept
- **Impact:** What could an attacker achieve?
- **Affected Versions:** Which versions are vulnerable?
- **Suggested Fix:** Optional but appreciated

---

## Response Timeline

| Action                        | Timeframe                                 |
| ----------------------------- | ----------------------------------------- |
| Acknowledgment                | Target: within 72 hours                   |
| Initial triage                | Target: within 7 days                     |
| Status update                 | Target: every 7 days during investigation |
| Fix deployed                  | Varies by severity (target: 30–90 days)   |
| Reward issued (if applicable) | Target: within 30 days of fix deployment  |

> **Note:** These are targets, not guarantees. Small teams or volunteer maintainers may need more time. We will communicate delays proactively.

---

## Reward Payment

<!-- TODO (template users): Remove this entire section if you're offering
     recognition only. If you keep it, review payment methods and legal
     requirements for your jurisdiction. Consider consulting legal counsel
     before committing to monetary rewards. -->

If monetary rewards are offered, payment methods may include:

- **PayPal** (most common)
- **GitHub Sponsors** (one-time sponsorship)
- **Bank transfer** (for larger amounts, where feasible)
- **Cryptocurrency** (BTC, ETH — optional, if available; may have compliance limitations)
- **Donation to charity** (in your name)

> **Note:** Not all payment methods may be available. We will work with you to find a suitable option.

### Requirements

- You must have a valid payment method available in your region
- You must not be on any applicable sanctions list (varies by jurisdiction)
- You must be at least 18 years old (or have guardian consent, where permitted)
- Rewards may be subject to applicable tax laws in your jurisdiction
- **Tax responsibility:** Researchers are responsible for reporting any bounty income as required by their local laws. We may request tax documentation where legally required.

<!-- TODO (template users): Adjust or remove these requirements based on
     your jurisdiction and legal advice. These are examples, not legal guidance. -->

---

## Recognition

With your permission, we will:

- Credit you in the security advisory
- Add your name to our [Security Hall of Fame](#hall-of-fame)
- Provide a letter of acknowledgment (upon request)

If you prefer to remain anonymous, we will respect that.

---

## Hall of Fame

We thank the following researchers for their contributions:

<!-- Add researchers here as vulnerabilities are reported and fixed -->

| Researcher      | Vulnerability | Date |
| --------------- | ------------- | ---- |
| _Be the first!_ | —             | —    |

---

## Changes to This Policy

We may modify this bug bounty policy at any time. Changes will be posted to this document with an updated revision date.

**Last updated:** January 2026

<!-- TODO (template users): Update this date whenever you modify the policy. -->

---

## Questions?

Contact us at `[security-email]@[your-domain].com` for any questions about
this program.

<!-- TODO (template users): Replace with your actual security contact email -->

---

## Related Documents

- [SECURITY.md](../../SECURITY.md) — Main security policy for this repository
- [SECURITY_with_bounty.md](SECURITY_with_bounty.md) — Security policy template with integrated bounty section
- [SECURITY_no_bounty.md](SECURITY_no_bounty.md) — Security policy template without bounty program
- [Templates README](README.md) — Overview of all available templates
