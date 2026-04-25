# Security Policy

> **⚠️ THIS IS A TEMPLATE — NOT AN ACTIVE SECURITY POLICY**
>
> **This document is an example only. It is NOT active for this repository.**
>
> To use this template: copy it to the root of your repository as
> `SECURITY.md`, replace all placeholders (marked with `TODO`), and remove
> this notice.

<!-- TODO (template users): Before publishing this file:
     1. Copy this file to the root of your repository as SECURITY.md
     2. Replace ALL `[OWNER]/[REPO]` placeholders with your actual repo path
     3. Replace ALL email placeholders with your real security contact
     4. Replace `[package-name]` and domain placeholders with real values
     5. Update the Supported Versions table for your release schedule
     6. Enable GitHub Security Advisories in repo settings
        (Settings → Security → Private vulnerability reporting)
     7. Delete the template warning banner at the top
     8. Review each section — remove anything that doesn't apply -->

**Status:** Not active for this repository. For demonstration purposes only.

---

## Supported Versions

<!-- TODO (template users): Update this table as you release new versions.
     Keep it in sync with BUG_BOUNTY.md's Version Coverage table (if applicable).
     If you only support the latest version, simplify to a single row. -->

> **Note:** Update this table per release; otherwise assume only the latest
> version is supported.

| Version | Supported                                |
| ------- | ---------------------------------------- |
| 2.x.x   | :white_check_mark:                       |
| 1.x.x   | :white_check_mark: (security fixes only) |
| < 1.0   | :x:                                      |

---

## Bug Bounty

We do not currently offer a bug bounty program. However, we deeply
appreciate responsible disclosure and will acknowledge contributors in
our [Acknowledgments](#acknowledgments) section.

If you're interested in sponsoring a bug bounty program for this project,
please [contact us](mailto:security@example.com).

<!-- TODO (template users): Replace security@example.com with your actual
     security contact. If you decide to add a bounty program later,
     switch to the SECURITY_with_bounty.md template instead. -->

> **Looking for a bounty template?** See
> [SECURITY_with_bounty.md](SECURITY_with_bounty.md) and
> [BUG_BOUNTY.md](BUG_BOUNTY.md) for examples.

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

---

## Response Timeline

> **Note:** These are targets, not guarantees. Small teams or volunteer
> maintainers may need more time. We will communicate delays proactively.

| Action                   | Timeframe                                 |
| ------------------------ | ----------------------------------------- |
| Acknowledgment of report | Target: within 72 hours                   |
| Initial assessment       | Target: within 7 days                     |
| Status updates           | Target: every 7 days during investigation |
| Resolution or mitigation | Varies by severity (target: 30–90 days)   |
| Public disclosure        | After fix is released                     |

---

## Disclosure Policy

- We will work with you to understand and resolve the issue quickly.
- We request that you give us reasonable time to address the vulnerability before public disclosure (typically 90 days).
- We will credit reporters in the security advisory (unless you prefer to remain anonymous).

---

## Rules of Engagement

To be eligible for recognition, you must:

1. **Report privately** — Do not disclose publicly until we've released a fix
2. **Provide details** — Include steps to reproduce, impact assessment, and PoC
3. **Act in good faith** — Do not access, modify, or delete user data
4. **Test responsibly** — Only test against your own instances or with explicit permission
5. **One report per issue** — Do not submit duplicates or variants of the same issue
6. **No disruptive testing** — Do not perform DoS attacks, brute force attacks, or aggressive automated scanning

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

> **Note:** Only the default branch and the latest supported release line are eligible.

### Out of Scope

The following are generally **not considered** security vulnerabilities:

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

---

## Related Documents

- [SECURITY_with_bounty.md](SECURITY_with_bounty.md) — Example security policy with bug bounty program
- [BUG_BOUNTY.md](BUG_BOUNTY.md) — Example standalone bug bounty policy
- [SECURITY.md](../../SECURITY.md) — Main security policy for this repository
- [Templates README](README.md) — Overview of all available templates

---

**Last updated:** February 2026

<!-- TODO (template users): Update this date whenever you modify the policy. -->
