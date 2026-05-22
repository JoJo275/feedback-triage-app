# Email Framework

!!! danger "Operating Boundary"
    This document defines tool boundaries for transactional email authoring,
    runtime rendering, and delivery.
    It does not replace `../tooling.md` as the tool inventory or
    `background-processing-architecture.md` for task/workflow execution boundaries.

!!! note "Status (Migration Target)"
    This framework describes the target migration model.
    Existing implementation paths may still use simpler in-process email sending
    while migration work is staged.

## Purpose

Use this framework to keep HTML layout, runtime variable injection, and provider delivery separate.

## Core Ownership Model

- MJML owns the responsive HTML email layout.
- Jinja2 owns dynamic variable injection and plain-text rendering.
- The email provider owns delivery.
- Provider templates remain deferred.

So the split is:

- MJML = layout/design system for HTML email
- Jinja2 = variable injection + plain-text email

## Tool Boundaries

| Tool | Role | Use for | Adoption timing |
| --- | --- | --- | --- |
| Jinja2 | Runtime template rendering for dynamic values and plain-text output | Inject reset links, names, workspace names, expiration times, and render `.txt` fallback emails | Active/default |
| MJML | Responsive HTML email layout authoring | Branded HTML email structure: headers, buttons, sections, reports, onboarding, invites | Active/default |
| Provider templates | Provider-managed email templates | Non-code editing and provider-side template governance | Deferred |

Use MJML for source-controlled responsive HTML email layouts. Use Jinja2 to inject runtime values into compiled HTML templates and to render plain-text fallback templates. Provider templates remain deferred until there is an explicit governance process for editing templates outside the codebase.

## What Jinja2 Owns

Jinja2 handles runtime variables such as:

```jinja
{{ user_name }}
{{ reset_url }}
{{ expires_minutes }}
{{ workspace_name }}
{{ invite_url }}
{{ support_email }}
```

Jinja2 can also handle light conditional blocks:

```jinja
{% if workspace_name %}
You were invited to {{ workspace_name }}.
{% endif %}
```

If MJML is active, Jinja2 should not be the main responsive layout system.

## What MJML Owns

MJML owns the HTML layout/design system elements:

- Header
- Body sections
- Buttons
- Footer
- Spacing
- Mobile layout
- Responsive columns
- Brand styling

## Recommended Implementation Workflow

1. Author HTML email layout in MJML.
2. Compile MJML to HTML.
3. Keep Jinja2 placeholders in the compiled HTML template.
4. At runtime, FastAPI, Celery, or Temporal passes variables into Jinja2.
5. Jinja2 renders final HTML and plain text.
6. Email provider sends the email.

Recommended template layout:

```text
emails/
  src/
    mjml/
      password_reset.mjml
  templates/
    html/
      password_reset.html.j2
    text/
      password_reset.txt.j2
```

Keep MJML source files under `emails/src/mjml/` and compile into `emails/templates/html/` while preserving Jinja2 placeholders.

Example runtime variables:

```python
context = {
    "product_name": "SignalNest",
    "support_email": "support@signalnest.com",
    "user_name": user_name,
    "reset_url": reset_url,
    "invite_url": invite_url,
    "workspace_name": workspace_name,
    "expires_minutes": 30,
}
```

Runtime variable guidance:

- Keep a stable set of shared keys (`product_name`, `support_email`) across transactional emails.
- Precompute URLs in backend code and pass them as final values (`reset_url`, `invite_url`).
- Treat optional values as optional and guard with Jinja2 conditionals (for example, `workspace_name`).
- Keep context payloads flat and explicit to reduce template drift.

## Adoption Guidance

MJML + Jinja2 is the recommended default for new transactional emails. Provider templates remain deferred until there is a clear need and governance process for non-code template editing. Existing in-process email sending can be migrated to this framework incrementally, starting with new emails or major revisions.
