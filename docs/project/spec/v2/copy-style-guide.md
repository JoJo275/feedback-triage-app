# v2.0 — Copy style guide

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`core-idea.md`](core-idea.md),
> [`error-catalog.md`](error-catalog.md),
> [`information-architecture.md`](information-architecture.md), [`email.md`](email.md).

This file is **how SignalNest sounds** in product UI, error
messages, marketing copy, and email. It promotes the brand voice
from [`core-idea.md`](core-idea.md) and lists every locked
string in one place.

---

## Voice

SignalNest's voice is **calm, direct, and operational** — like
a good incident channel, not a chirpy SaaS marketing site.

| Do                                              | Don't                                       |
| ----------------------------------------------- | ------------------------------------------- |
| "Capture the noise. Find the signal."           | "Crush your feedback workflow!"             |
| "We couldn't sign you in. Check your password." | "Whoops! Something went wrong. 😬"          |
| "Demo workspaces are read-only."                | "Sorry, you can't do that here."            |
| "Note edits close after 15 minutes."            | "You can no longer edit this note."         |
| "Sign in"                                       | "Login"                                     |
| "Log out"                                       | "Sign out" / "Logout"                       |
| "Workspace"                                     | "Team" / "Org" / "Account"                  |
| "Team member"                                   | "User" / "Member"                           |
| "Owner"                                         | "Admin" / "Manager"                         |
| "Inbox"                                         | "Feedback queue" / "Triage list"            |

The key trade-off: **clarity over cleverness**. If a sentence
makes the user think for an extra beat, rewrite it.

---

## Mechanical rules

- **Sentence case** for buttons, labels, and headings —
  *"Create workspace"*, not *"Create Workspace"*. Proper nouns
  (`SignalNest`, `Resend`) keep their case.
- **Oxford comma** in lists.
- **Em dash** ( `—` ) for parentheticals; no spaced hyphens.
- **No exclamation marks** in product copy. The only exceptions
  are `core-idea.md` taglines if they're locked there.
- **No emoji** in product copy. (Markdown notes/issues are fine.)
- **Numbers**: spell out one through nine; numerals for 10+.
  Always numerals for time (`5 minutes`), money (`$5`), and
  versions (`v2.0`).
- **Time**: relative ("3 minutes ago") in lists; absolute UTC
  ISO 8601 in tooltips and detail pages. Never local time
  without an explicit "(your time)" suffix.
- **Capitalization of feature names**: lowercase unless it's
  the start of a sentence. *"Use roadmap to plan ahead."*
  Exception: locked strings in the table below.

---

## Action verbs

| Action                                  | Button text         |
| --------------------------------------- | ------------------- |
| Create a feedback item                  | *Add feedback*      |
| Create a workspace                      | *Create workspace*  |
| Save form changes                       | *Save changes*      |
| Discard form changes                    | *Cancel*            |
| Permanently remove                      | *Delete*            |
| Soft-archive                            | *Archive*           |
| Send an invitation email                | *Send invite*       |
| Sign in                                 | *Sign in*           |
| Sign out                                | *Log out*           |
| Confirm a destructive action            | *Yes, delete it*    |
| Acknowledge a non-destructive notice    | *Got it*            |

Destructive confirmations always restate the noun
("Yes, delete it" — not "Yes, confirm").

---

## Error messages

Sourced from [`error-catalog.md`](error-catalog.md). The tone:
**state what happened, then what to do**. No blame.

| Code                          | Message                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| `auth_required`               | *Please sign in to continue.*                                                        |
| `invalid_credentials`         | *We couldn't sign you in. Check your email and password.*                            |
| `email_not_verified`          | *Verify your email before signing in. We sent a link — check your inbox.*            |
| `account_locked`              | *Too many sign-in attempts. Try again in 15 minutes.*                                |
| `password_too_weak`           | *Use at least 12 characters with a mix of letters, numbers, and symbols.*            |
| `feature_disabled`            | *This isn't available yet. Check back soon.*                                         |
| `workspace_not_found`         | *We can't find that workspace.*                                                      |
| `workspace_slug_taken`        | *That URL is already taken. Try another.*                                            |
| `workspace_slug_immutable`    | *Workspace URLs can't be changed after creation.*                                    |
| `role_insufficient`           | *Only workspace owners can do that.*                                                 |
| `demo_read_only`              | *Demo workspaces are read-only. Sign up to make changes.*                            |
| `feedback_not_found`          | *We can't find that feedback item.*                                                  |
| `type_other_required`         | *Please describe the type when choosing 'Other.'*                                    |
| `source_other_required`       | *Please describe the source when choosing 'Other.'*                                  |
| `pain_level_out_of_range`     | *Pick a pain level from 1 to 5.*                                                     |
| `status_transition_invalid`   | *That status change isn't allowed from here.*                                        |
| `note_edit_window_expired`    | *Note edits close after 15 minutes.*                                                 |
| `note_not_owner`              | *You can only edit your own notes.*                                                  |
| `tag_name_taken`              | *A tag with that name already exists.*                                               |
| `rate_limited`                | *You're going a bit fast. Try again in a moment.*                                    |
| `payload_too_large`           | *That submission is too large. Keep it under 64 KB.*                                 |
| `internal_error`              | *Something went wrong on our end. Please try again.*                                 |

Messages exceed one sentence only when the user genuinely needs
more context (e.g. `account_locked` mentions the wait time).

---

## Empty states

Every list page has an empty state with three slots: **icon,
heading, body, primary action**. Voice is encouraging without
being chirpy.

| Page              | Heading                          | Body                                                                  | Primary action     |
| ----------------- | -------------------------------- | --------------------------------------------------------------------- | ------------------ |
| Inbox             | *Inbox zero.*                    | *Nothing waiting. New feedback shows up here.*                        | *Add feedback*     |
| Feedback list     | *No feedback yet.*               | *Start collecting signals from your users.*                           | *Add feedback*     |
| Roadmap           | *Roadmap is empty.*              | *Mark feedback as planned to put it on the roadmap.*                  | *Open inbox*       |
| Changelog         | *Nothing shipped yet.*           | *When you mark feedback as shipped, it'll show up here.*              | *Open feedback*    |
| Submitters        | *No submitters yet.*             | *Submitters appear when feedback is linked to a person.*              | (none)             |
| Tags (settings)   | *No tags yet.*                   | *Tags help group related feedback. Make a few to get started.*        | *New tag*          |
| Insights          | *Not enough data yet.*           | *Insights need at least 20 feedback items.*                           | *Open inbox*       |

---

## Locked strings (master list)

These never change without an ADR. They live in many places —
this is the canonical list. Cross-checked with
[`core-idea.md`](core-idea.md).

| Key                                         | Value                                                                                                |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `brand.name`                                | `SignalNest`                                                                                         |
| `brand.domain`                              | `signalnest.app`                                                                                     |
| `brand.tagline`                             | *Capture the noise. Find the signal.*                                                                |
| `brand.description`                         | *A feedback triage app for turning user requests, bugs, and product ideas into clear next steps.*    |
| `landing.hero.cta_primary`                  | *Get started*                                                                                        |
| `landing.hero.cta_secondary`                | *See it in action*                                                                                   |
| `auth.signin.heading`                       | *Sign in to SignalNest*                                                                              |
| `auth.signup.heading`                       | *Create your SignalNest account*                                                                     |
| `auth.verify.heading`                       | *Check your inbox*                                                                                   |
| `auth.verify.body`                          | *We sent a verification link. Click it to finish signing up.*                                        |
| `public_submit.thank_you.heading`           | *Thanks — we got it.*                                                                                |
| `public_submit.thank_you.body`              | *We read every signal. If you left an email, we'll let you know if your feedback ships.*             |
| `demo.write_blocked.toast`                  | *Demo workspaces are read-only. Sign up to make changes.*                                            |
| `email.verification.subject`                | *Verify your SignalNest email*                                                                       |
| `email.verification_already.subject`        | *You already have a SignalNest account*                                                              |
| `email.password_reset.subject`              | *Reset your SignalNest password*                                                                     |
| `email.invitation.subject`                  | *You've been invited to a SignalNest workspace*                                                      |
| `email.status_change.subject`               | *Update on your feedback*                                                                            |
| `footer.copyright`                          | *© SignalNest. Calm signal intelligence.*                                                            |

Forbidden spellings: `Signal Nest`, `Signalnest`, `signalnest`
(in prose; the domain `signalnest.app` is the only lowercase use).

---

## Microcopy patterns

- **Confirmation toasts** are short and past-tense:
  *"Workspace created."* / *"Note saved."* / *"Invite sent."*
- **Loading states** are present-tense, ≤ 3 words:
  *"Loading…"* / *"Saving…"* / *"Sending invite…"*
- **Destructive confirmations** restate the noun and the verb:
  *"Delete this feedback?"* with body *"This can't be undone."*
- **Form help text** is one short sentence under the field;
  no validation hints in placeholders.

---

## Out of scope (v2.0)

- Localization. v2.0 ships in English only. Logical CSS
  properties used where free ([`css.md`](css.md)) so v2.1
  can add translations without re-layouts.
- Long-form marketing copy beyond the landing hero. Documentation
  for product features lives in `docs/`, not in-app.
