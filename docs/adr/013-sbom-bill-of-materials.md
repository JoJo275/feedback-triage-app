# ADR 013: SBOM generation and distribution strategy

## Status

Accepted

## Context

Software supply-chain transparency is increasingly expected by consumers, auditors, and regulators (e.g., US Executive Order 14028, EU Cyber Resilience Act). A Software Bill of Materials (SBOM) provides a machine-readable inventory of every component in a software artifact, enabling vulnerability tracking, license compliance, and procurement decisions.

Two dominant SBOM standards exist:

| Standard                     | Governing body                        | Strengths                                                           |
| ---------------------------- | ------------------------------------- | ------------------------------------------------------------------- |
| **SPDX** (ISO/IEC 5962:2021) | Linux Foundation                      | ISO standard; strong license metadata; GitHub-native support        |
| **CycloneDX**                | OWASP / Ecma International (ECMA-424) | Purpose-built for security; rich vulnerability and service metadata |

Neither standard is a strict superset of the other. Producing both maximises interoperability with downstream tooling.

### Distribution channels considered

GitHub offers several complementary ways to surface SBOM data:

| Channel                               | What it provides                                       | Who controls it       |
| ------------------------------------- | ------------------------------------------------------ | --------------------- |
| 1. **Dependency Graph "Export SBOM"** | SPDX JSON computed by GitHub from the dependency graph | GitHub (repo setting) |
| 2. **Actions artifact**               | SBOM files downloadable from a workflow run            | Our workflow          |
| 3. **Release asset**                  | SBOM files attached to a GitHub Release                | Our workflow          |
| 4. **Dependency Submission API**      | Dependency data pushed into GitHub's graph and alerts  | Our workflow          |

Channels 1 and 4 populate the same Dependency Graph UI but may differ because (1) uses GitHub's own resolver while (4) uses whatever our generator (Syft) detects.

### Generator tool considered

| Tool               | Formats            | Maintained | Notes                                                   |
| ------------------ | ------------------ | ---------- | ------------------------------------------------------- |
| **Syft** (Anchore) | SPDX, CycloneDX    | Active     | Multi-ecosystem scanner; used via `anchore/sbom-action` |
| **CycloneDX CLI**  | CycloneDX only     | Active     | Python-specific; would need a separate tool for SPDX    |
| **pip-licenses**   | Custom / CycloneDX | Active     | License-focused; not a full SBOM generator              |

## Decision

1. **Primary format: SPDX JSON** — aligns with GitHub's native support and ISO standardisation.
2. **Secondary format: CycloneDX JSON** — produced simultaneously for OWASP-ecosystem consumers.
3. **Generator: Syft** (via `anchore/sbom-action`) — single tool produces both formats; actively maintained; first-party GitHub Action available.
4. **Enable all four distribution channels simultaneously:**

    | Channel                      | Workflow                      | Authoritative?                                  |
    | ---------------------------- | ----------------------------- | ----------------------------------------------- |
    | 1. Dependency Graph export   | Built-in (no workflow needed) | No — GitHub-computed, may differ                |
    | 2. Actions artifact          | `sbom.yml`                    | No — per-commit snapshot                        |
    | 3. Release asset             | `release.yml`                 | **Yes — authoritative for each tagged version** |
    | 4. Dependency Submission API | `sbom.yml` (push to main)     | No — enriches GitHub UI/alerts                  |

5. **Authoritative SBOM:** The release-asset SBOM (channel 3) attached to a tagged release is the authoritative SBOM for that version. It is generated from the same commit that produced the release artifacts.

## Consequences

### Positive

- Full supply-chain transparency in both major SBOM standards
- Consumers can download the authoritative SBOM from the Release page
- GitHub's Dependency Graph and Dependabot alerts are enriched via the Submission API
- Single tool (Syft) for both formats reduces maintenance burden
- Weekly scheduled runs catch newly disclosed vulnerabilities in existing dependency snapshots
- Aligns with industry direction (EO 14028, CRA, NTIA minimum elements)

### Negative

- Adds ~2–3 minutes of CI time per push/PR (SBOM generation)
- Release workflow gains an additional job (sbom), adding ~2 minutes to release time
- Four channels may confuse consumers about which SBOM to trust (mitigated by documenting channel 3 as authoritative)
- Syft's output may differ from GitHub's built-in Dependency Graph export (channel 1) — this is inherent and documented

### Neutral

- `anchore/sbom-action` is pinned to a commit SHA per ADR-004
- The `sbom.yml` workflow uses the same repository-guard pattern as other optional workflows (ADR-011)
- CycloneDX VEX (Vulnerability Exploitability eXchange) support could be added later as a follow-up
