# Demo Data Policy

This policy defines what data is acceptable for demos, screenshots,
seed scripts, sample exports, and public documentation.

The goal is simple: all demo surfaces must use safe, non-sensitive,
non-identifying data.

## Policy summary

- Use synthetic or anonymized data for all public artifacts.
- Never include real customer, prospect, or partner identifiers.
- Keep public demo examples realistic enough for clarity, but fake.
- Treat uncertain cases as private and do not publish them.

## Allowed demo data

- Fully synthetic names, emails, company names, and feedback text.
- Placeholder channels and sources (for example: web, email, sales-call).
- Aggregated counts that cannot be traced to a person or account.
- Redacted examples where any identifying detail is removed.

## Prohibited demo data

- Real customer/prospect names, domains, emails, or account IDs.
- Interview transcripts or quotes tied to identifiable parties.
- Contract, pricing, legal, or negotiation details.
- Internal strategy notes, risk assessments, or launch tactics.

## Generation and sanitization rules

1. Prefer generated fixtures and seed data over copied production data.
2. If a real record is needed for structure, replace all identifying
   fields before saving or sharing.
3. Preserve business shape (statuses, pain levels, trends) while
   removing identity.
4. Re-check screenshots and exports for hidden metadata or visible
   personal information.

## Publication checklist

Before publishing docs, demos, screenshots, or recordings:

- [ ] No real names, emails, domains, IDs, or customer references.
- [ ] No private pricing, legal, or strategy content.
- [ ] Sample data is synthetic or safely anonymized.
- [ ] The artifact is safe for public repository viewers.

## Escalation rule

If there is any doubt that data is public-safe, keep it out of public
files and store it in private planning notes.

## Related docs

- [Business README](README.md)
- [Validation Plan](validation-plan.md)
- [v2 Risks](../project/spec/v2/risks.md)
