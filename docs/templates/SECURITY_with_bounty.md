# Security Policy

> **⚠️ THIS IS A TEMPLATE — NOT AN ACTIVE SECURITY POLICY**
>
> **This document is an example only. It is NOT active for this repository.**
> **Do not submit vulnerability reports expecting rewards for this template repo.**
>
> To use this template: copy it to the root of your repository as
> `SECURITY.md`, replace all placeholders (marked with `TODO`), and remove
> this notice.

<!-- TODO (template users): Before publishing this file:
     1. Copy this file to the root of your repository as SECURITY.md
     2. Replace ALL `[OWNER]/[REPO]` placeholders with your actual repo path
     3. Replace ALL email placeholders with your real security contact
     4. Replace `[package-name]` and domain placeholders with real values
     5. Set actual reward amounts in the bounty table (or switch to recognition only)
     6. Copy BUG_BOUNTY.md alongside this file and update it too
     7. Enable GitHub Security Advisories in repo settings
        (Settings → Security → Private vulnerability reporting)
     8. Delete the template warning banner at the top
     9. Consider having legal counsel review before committing to bounty payments -->

**Status:** Not active for this repository. For demonstration purposes only.

---

## Supported Versions

<!-- TODO (template users): Update this table as you release new versions.
     Keep it in sync with BUG_BOUNTY.md's Version Coverage table.
     If you only support the latest version, simplify to a single row. -->

> **Note:** Update this table per release; otherwise assume only the latest
> version is supported.

| Version | Supported                                |
| ------- | ---------------------------------------- |
| 2.x.x   | :white_check_mark:                       |
| 1.x.x   | :white_check_mark: (security fixes only) |
| < 1.0   | :x:                                      |

---

## Bug Bounty Program

**This template includes an example bug bounty program. If you adopt it, you may offer rewards for responsibly disclosed vulnerabilities; amounts are guidelines and depend on impact, exploitability, and available funding.**

> **Severity Classification:** Severity is determined by maintainers using [CVSS](https://www.first.org/cvss/) or [OWASP guidance](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology).

| Severity | Examples                                        | Reward Range     |
| -------- | ----------------------------------------------- | ---------------- |
| Critical | Remote code execution, auth bypass, data breach | $100 – $500+     |
| High     | Privilege escalation, significant data exposure | $50 – $200       |
| Medium   | XSS, CSRF, information disclosure               | $25 – $100       |
| Low      | Minor information leaks, theoretical attacks    | Recognition only |

> **Note:** Reward amounts are guidelines and may vary based on project funding. Some projects may offer recognition only.

> **Payout Caveat:** Rewards are discretionary and depend on exploitability, impact, report quality, and available funding.

> **Minimum for monetary rewards:** Only Medium severity and above are eligible for monetary rewards.

**For full details, including scope, payment methods, eligibility rules, and tax requirements, see our [Bug Bounty Policy](BUG_BOUNTY.md).**

---

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Do NOT open a public issue for security vulnerabilities.**

Instead, please report security vulnerabilities via one of the following methods:

<!-- TODO (template users): Replace [OWNER]/[REPO] and security@example.com
     with your actual values. -->
<!-- TODO (template users): Ensure Security Advisories are enabled in repo
     settings (Settings → Security → Private vulnerability reporting);
     otherwise the advisory link below will 404. -->

1. **GitHub Security Advisories (Preferred)**
   Use [GitHub's private vulnerability reporting](https://github.com/[OWNER]/[REPO]/security/advisories/new) to submit a report directly.

2. **Email**
   Contact the maintainers directly at: `security@example.com`

3. **PGP Encrypted Email** (Optional)
   For sensitive communications, you may encrypt your report using our PGP key.

     <!-- TODO (template users): Add your PGP key fingerprint (full 40-character
          format), or remove this entire option if you don't use PGP:
     Key fingerprint: `XXXX XXXX XXXX XXXX XXXX  XXXX XXXX XXXX XXXX XXXX`
     Public key: https://keys.openpgp.org/search?q=security@example.com
     -->

### What to Include

Please provide as much information as possible:

- **Summary** — Brief description of the vulnerability
- **Severity** — Your assessment (Critical/High/Medium/Low)
- **Steps to reproduce** — Detailed instructions or proof-of-concept
- **Affected versions** — Which versions are vulnerable?
- **Potential impact** — What could an attacker achieve?
- **Suggested fix** — Optional but appreciated
- **Bounty eligibility** — Confirm you've read the [Bug Bounty Policy](BUG_BOUNTY.md)

---

## Response Timeline

> **Note:** These are targets, not guarantees. Small teams or volunteer
> maintainers may need more time. We will communicate delays proactively.

| Action                         | Timeframe                                 |
| ------------------------------ | ----------------------------------------- |
| Acknowledgment of report       | Target: within 72 hours                   |
| Initial assessment             | Target: within 7 days                     |
| Status updates                 | Target: every 7 days during investigation |
| Resolution or mitigation       | Varies by severity (target: 30–90 days)   |
| Reward payment (if applicable) | Target: within 30 days of fix deployment  |
| Public disclosure              | After fix is released                     |

---

## Disclosure Policy

- We will work with you to understand and resolve the issue quickly.
- We request that you give us reasonable time to address the vulnerability before public disclosure (typically 90 days).
- We will credit reporters in the security advisory (unless you prefer to remain anonymous).
- Coordinated disclosure will not affect your bounty eligibility.

---

## Rules of Engagement

To qualify for a reward, you must:

1. **Report privately** — Do not disclose publicly until we've released a fix
2. **Provide details** — Include steps to reproduce, impact assessment, and PoC
3. **Act in good faith** — Do not access, modify, or delete user data
4. **Test responsibly** — Only test against your own instances or with explicit permission
5. **One report per issue** — Do not submit duplicates or variants of the same issue
6. **No disruptive testing** — Do not perform DoS attacks, brute force attacks, or aggressive automated scanning

For full eligibility rules, duplicate handling, and safe harbor provisions, see our [Bug Bounty Policy](BUG_BOUNTY.md).

### Duplicate Reports

If multiple researchers report the same vulnerability:

- The **first valid report** receives the full reward
- Subsequent reports may receive partial recognition at our sole discretion (but no monetary reward)
- We determine duplicates based on the timestamp of the report submission
- If reports arrive within 24 hours with substantially different details, we may split the reward at our sole discretion

---

## Safe Harbor

We support responsible security research. To the extent permitted by law, we will not initiate legal action against researchers who:

- Follow this security policy
- Act in good faith to avoid privacy violations and service disruption
- Do not access, modify, or delete data belonging to others
- Report vulnerabilities promptly

> **⚠️ Important:** Safe harbor applies only to authorized testing within the scope of this policy. The following activities are explicitly excluded from safe harbor:
>
> - Unauthorized access to systems or data exfiltration
> - Service disruption, including DoS/DDoS attacks
> - Aggressive or repeated automated scanning
> - Any activity that violates applicable laws
>
> When in doubt, ask before testing.

---

## Scope

### In Scope

<!-- TODO (template users): Replace placeholders with your actual values.
     Remove lines that don't apply (e.g., Documentation site if you don't host one). -->

This security policy applies to:

- **Primary repository:** `https://github.com/[OWNER]/[REPO]`
- **Official releases:** Packages published to PyPI under `[package-name]`
- **Documentation site:** `https://docs.[your-domain].com` (if applicable)

> **Note:** Only the default branch and the latest supported release line are eligible for bounty rewards.

### Out of Scope

The following are generally **not eligible** for rewards:

- Vulnerabilities in third-party dependencies (report to upstream project), unless the exploitability is caused by this project's code or configuration
- Issues requiring physical access to a user's device
- Social engineering attacks (phishing, etc.)
- Denial of service (DoS/DDoS) attacks
- Issues in staging/development environments
- Previously reported vulnerabilities
- Vulnerabilities disclosed publicly before we can address them
- Automated scanner output without proof of exploitability
- Theoretical vulnerabilities without demonstrable security impact
- User-hosted deployments, forks, or self-hosted instances

For complete scope details, see our [Bug Bounty Policy](BUG_BOUNTY.md).

---

## Security Best Practices

When using this project:

1. **Keep dependencies updated** — Run `pip list --outdated` or
   `task deps:outdated` regularly
2. **Use virtual environments** — Isolate project dependencies (`hatch shell`
   or `python -m venv .venv`)
3. **Review code before running** — Especially from untrusted sources
4. **Enable Dependabot** — For automated security updates on your fork
5. **Pin dependencies** — Use `pip freeze` or lock files for reproducible builds
6. **Avoid `shell=True`** — Use `subprocess` with argument lists instead
7. **Use safe YAML loading** — Always use `yaml.safe_load()`, never `yaml.load()`
8. **Never log secrets** — Ensure tokens and credentials are not logged

---

## Acknowledgments

We thank the following individuals for responsibly disclosing security issues:

<!-- Add names/handles here as vulnerabilities are reported and fixed -->

| Researcher      | Vulnerability | Severity | Date |
| --------------- | ------------- | -------- | ---- |
| _Be the first!_ | —             | —        | —    |

---

## Contact

<!-- TODO (template users): Replace placeholders with your actual values.
     Consider adding a dedicated security email alias rather than a personal address. -->

- **Security issues:** `security@example.com`
- **General questions:** Open a [Discussion](https://github.com/[OWNER]/[REPO]/discussions)
- **Bug bounty questions:** `security@example.com` with subject "Bug Bounty Question"

---

## Related Documents

- [Bug Bounty Policy](BUG_BOUNTY.md) — Full bounty program details, payment methods, and eligibility
- [SECURITY.md](../../SECURITY.md) — Main security policy for this repository
- [SECURITY_no_bounty.md](SECURITY_no_bounty.md) — Security policy template without bounty program
- [Templates README](README.md) — Overview of all available templates

---

**Last updated:** February 2026

<!-- TODO (template users): Update this date whenever you modify the policy. -->
