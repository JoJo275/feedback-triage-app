# Email Implementation: Vertical and Horizontal

This note explains how to stage email-framework rollout without blurring tool boundaries.

## Definitions

- Vertical implementation means shipping one user-visible email flow end to end.
- Horizontal implementation means building shared platform capabilities used by multiple email flows.

## Vertical Implementation

Use vertical slices to deliver value quickly and validate architecture in production-like paths.

Example vertical slice: password reset.

1. Add/update backend endpoint behavior and token persistence.
2. Build `password_reset.mjml` plus `password_reset.html.j2` and `password_reset.txt.j2`.
3. Compile MJML to HTML template and keep Jinja2 placeholders.
4. Build the runtime context payload and render with Jinja2.
5. Send through provider and capture delivery/failure logs.
6. Add tests for API behavior, rendering, and send-path success/failure handling.

Vertical slice success criteria:

- The flow is fully usable by end users.
- HTML and plain-text outputs both render correctly.
- Runtime context keys are explicit and validated.
- Delivery errors are observable and actionable.

## Horizontal Implementation

Use horizontal work to reduce repetition after one or more vertical slices prove the path.

Horizontal building blocks:

- Directory conventions for MJML source and compiled Jinja2 templates.
- Shared context key conventions and required/optional key policy.
- Compile workflow automation (command snippets, optional task wiring, CI checks).
- Reusable rendering helpers and provider send adapters.
- Shared logging/metrics/error taxonomy for delivery outcomes.
- Regression tests for common template and rendering invariants.

Horizontal success criteria:

- New email flows can be added with minimal boilerplate.
- Context payload shape is predictable across templates.
- Compile and render steps are consistent in local and CI runs.
- Operational telemetry is consistent across all transactional emails.

## Recommended Rollout Pattern

1. Start with one high-impact vertical slice (password reset or invite).
2. Extract only the shared pieces proven by that slice.
3. Ship a second vertical slice using extracted horizontal primitives.
4. Harden horizontal automation and conventions after the second slice.
5. Repeat per new email type with the same boundaries: MJML layout, Jinja2 injection/text, provider delivery.

## Avoid These Failure Modes

- Building broad horizontal abstraction before any real email flow ships.
- Letting each flow invent different context key naming conventions.
- Using provider templates early and losing source-controlled reviewability.
- Mixing ownership so Jinja2 becomes a responsive layout system.
- Skipping plain-text templates and relying only on HTML output.
