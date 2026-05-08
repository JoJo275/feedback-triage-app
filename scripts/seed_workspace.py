#!/usr/bin/env python3
"""Seed a target workspace with realistic demo data.

Unlike :mod:`scripts.seed`, which writes ~20 rows into the legacy
v1 workspace, this script populates a v2 workspace identified by
``--slug`` with a much richer dataset so the dashboard, inbox,
roadmap, changelog, insights, and submitters pages all have
something interesting to show.

Generated per run (deterministic via ``--seed``):

* ~10 tags spread across the palette
* ~30 named submitters + a handful of anonymous (email-null) ones
* ~150 feedback items spread across every status, type, source,
  priority, and pain level, with timestamps spread across the
  last 90 days, ~half attached to submitters, ~30 % carrying tags,
  ~20 % carrying notes, plus a few items already published to the
  public roadmap or changelog so those pages render content.

Idempotent by default: bails out if the workspace already has any
feedback. ``--reset`` deletes the workspace's tags, submitters,
and feedback items first; ``--force`` adds on top.

Usage:

    python scripts/seed_workspace.py --slug husky5084
    python scripts/seed_workspace.py --slug husky5084 --reset
    python scripts/seed_workspace.py --slug husky5084 --count 200
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from feedback_triage.database import SessionLocal
from feedback_triage.enums import (
    FeedbackType,
    Priority,
    Source,
    Status,
    UserRole,
    WorkspaceRole,
)
from feedback_triage.models import (
    FeedbackItem,
    FeedbackNote,
    FeedbackTag,
    Submitter,
    Tag,
    User,
    Workspace,
    WorkspaceMembership,
)

logger = logging.getLogger(__name__)

SCRIPT_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Demo content libraries
# ---------------------------------------------------------------------------

TAG_PALETTE = (
    ("Onboarding", "onboarding", "teal"),
    ("Performance", "performance", "amber"),
    ("Mobile", "mobile", "indigo"),
    ("Reporting", "reporting", "sky"),
    ("Billing", "billing", "rose"),
    ("Integrations", "integrations", "violet"),
    ("Accessibility", "accessibility", "green"),
    ("UI", "ui", "slate"),
    ("Permissions", "permissions", "rose"),
    ("Export", "export", "amber"),
    ("Search", "search", "sky"),
    ("Notifications", "notifications", "indigo"),
)

SUBMITTER_NAMES = (
    "Sarah Mitchell",
    "James Chen",
    "Olivia Garcia",
    "Aiden Patel",
    "Michael Brown",
    "Priya Shah",
    "Leah Thompson",
    "Daniel Kim",
    "Emma Wilson",
    "Noah Davis",
    "Ava Rodriguez",
    "Liam O'Connor",
    "Sophia Nguyen",
    "Lucas Müller",
    "Mia Hernandez",
    "Ethan Walker",
    "Isabella Rossi",
    "Mason Cohen",
    "Charlotte Bauer",
    "Logan Foster",
    "Amelia Yamamoto",
    "Benjamin Singh",
    "Harper Andersson",
    "Elijah Khan",
    "Evelyn Schmidt",
    "Henry Park",
    "Abigail Lopez",
    "Sebastian Reilly",
    "Madeline Cole",
    "Jackson Reed",
)

# (title, type, source, pain_level, status, priority, has_description)
ITEM_TEMPLATES: tuple[
    tuple[str, FeedbackType, Source, int, Status, Priority | None, bool], ...
] = (
    (
        "Login button hidden on mobile Safari",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.NEW,
        Priority.HIGH,
        True,
    ),
    (
        "CSV export silently truncates at 1000 rows",
        FeedbackType.BUG,
        Source.EMAIL,
        5,
        Status.REVIEWING,
        Priority.CRITICAL,
        True,
    ),
    (
        "Dark mode would be lovely",
        FeedbackType.FEATURE_REQUEST,
        Source.TWITTER,
        2,
        Status.PLANNED,
        Priority.MEDIUM,
        False,
    ),
    (
        "Onboarding tour is too long",
        FeedbackType.COMPLAINT,
        Source.INTERVIEW,
        3,
        Status.REVIEWING,
        Priority.MEDIUM,
        True,
    ),
    (
        "Add Slack integration",
        FeedbackType.FEATURE_REQUEST,
        Source.REDDIT,
        3,
        Status.PLANNED,
        Priority.HIGH,
        False,
    ),
    (
        "App crashes when offline for >10 minutes",
        FeedbackType.BUG,
        Source.APP_STORE,
        5,
        Status.IN_PROGRESS,
        Priority.CRITICAL,
        True,
    ),
    (
        "Settings page typo: 'colour' should be 'color'",
        FeedbackType.BUG,
        Source.OTHER,
        1,
        Status.SHIPPED,
        Priority.LOW,
        False,
    ),
    (
        "Keyboard shortcut for new item",
        FeedbackType.FEATURE_REQUEST,
        Source.SUPPORT,
        2,
        Status.PLANNED,
        Priority.LOW,
        False,
    ),
    (
        "Email notifications arrive 30 min late",
        FeedbackType.BUG,
        Source.EMAIL,
        4,
        Status.REVIEWING,
        Priority.HIGH,
        True,
    ),
    (
        "Bring back the old icon",
        FeedbackType.COMPLAINT,
        Source.TWITTER,
        1,
        Status.CLOSED,
        None,
        False,
    ),
    (
        "Bulk archive button on list page",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        3,
        Status.NEW,
        Priority.MEDIUM,
        False,
    ),
    (
        "Search returns deleted items",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.ACCEPTED,
        Priority.HIGH,
        True,
    ),
    (
        "Native Windows app",
        FeedbackType.FEATURE_REQUEST,
        Source.REDDIT,
        2,
        Status.CLOSED,
        None,
        True,
    ),
    (
        "Two-factor auth via TOTP",
        FeedbackType.FEATURE_REQUEST,
        Source.EMAIL,
        4,
        Status.PLANNED,
        Priority.HIGH,
        False,
    ),
    (
        "Charts render slowly with >5k items",
        FeedbackType.BUG,
        Source.APP_STORE,
        3,
        Status.NEW,
        Priority.MEDIUM,
        True,
    ),
    (
        "Allow markdown in descriptions",
        FeedbackType.FEATURE_REQUEST,
        Source.OTHER,
        2,
        Status.SHIPPED,
        Priority.MEDIUM,
        False,
    ),
    (
        "Timezone displayed in UTC, not local",
        FeedbackType.COMPLAINT,
        Source.SUPPORT,
        2,
        Status.NEW,
        None,
        False,
    ),
    (
        "Accessibility: focus ring missing on tabs",
        FeedbackType.BUG,
        Source.INTERVIEW,
        3,
        Status.REVIEWING,
        Priority.HIGH,
        True,
    ),
    (
        "Export to JSON, not just CSV",
        FeedbackType.FEATURE_REQUEST,
        Source.REDDIT,
        2,
        Status.PLANNED,
        Priority.LOW,
        False,
    ),
    (
        "Make pain_level optional",
        FeedbackType.FEATURE_REQUEST,
        Source.OTHER,
        1,
        Status.CLOSED,
        None,
        True,
    ),
    (
        "Support SSO with Okta",
        FeedbackType.FEATURE_REQUEST,
        Source.EMAIL,
        4,
        Status.PLANNED,
        Priority.HIGH,
        True,
    ),
    (
        "Reports page loads very slowly",
        FeedbackType.BUG,
        Source.SUPPORT,
        5,
        Status.IN_PROGRESS,
        Priority.CRITICAL,
        True,
    ),
    (
        "Can't invite new team members",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.IN_PROGRESS,
        Priority.HIGH,
        True,
    ),
    (
        "Errors when connecting Slack",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.IN_PROGRESS,
        Priority.HIGH,
        True,
    ),
    (
        "Add filter by date range",
        FeedbackType.FEATURE_REQUEST,
        Source.APP_STORE,
        3,
        Status.NEW,
        Priority.MEDIUM,
        False,
    ),
    (
        "How to add custom domain?",
        FeedbackType.QUESTION,
        Source.SUPPORT,
        2,
        Status.NEEDS_INFO,
        None,
        False,
    ),
    (
        "Bulk edit for custom fields",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        4,
        Status.PLANNED,
        Priority.HIGH,
        True,
    ),
    (
        "Praise: love the new triage view",
        FeedbackType.PRAISE,
        Source.TWITTER,
        1,
        Status.CLOSED,
        None,
        False,
    ),
    (
        "Webhook URL keeps resetting after save",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.NEW,
        Priority.HIGH,
        True,
    ),
    (
        "Improve empty-state copy on Inbox",
        FeedbackType.FEATURE_REQUEST,
        Source.OTHER,
        2,
        Status.ACCEPTED,
        Priority.LOW,
        False,
    ),
    (
        "API rate-limit headers missing",
        FeedbackType.BUG,
        Source.EMAIL,
        3,
        Status.REVIEWING,
        Priority.MEDIUM,
        True,
    ),
    (
        "Add Jira sync (one-way)",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        4,
        Status.PLANNED,
        Priority.HIGH,
        False,
    ),
    (
        "Notifications email goes to spam (Outlook)",
        FeedbackType.BUG,
        Source.SUPPORT,
        4,
        Status.NEEDS_INFO,
        Priority.HIGH,
        True,
    ),
    (
        "Tag colors not accessible (low contrast)",
        FeedbackType.BUG,
        Source.INTERVIEW,
        3,
        Status.ACCEPTED,
        Priority.MEDIUM,
        True,
    ),
    (
        "Saved views per user",
        FeedbackType.FEATURE_REQUEST,
        Source.REDDIT,
        3,
        Status.PLANNED,
        Priority.MEDIUM,
        False,
    ),
    (
        "Multi-select bulk actions",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        3,
        Status.IN_PROGRESS,
        Priority.MEDIUM,
        False,
    ),
    (
        "Page jitter when filter chips wrap",
        FeedbackType.BUG,
        Source.OTHER,
        2,
        Status.NEW,
        Priority.LOW,
        False,
    ),
    (
        "Question: do you support GDPR data export?",
        FeedbackType.QUESTION,
        Source.EMAIL,
        2,
        Status.NEEDS_INFO,
        None,
        True,
    ),
    (
        "Default sort should be newest first",
        FeedbackType.FEATURE_REQUEST,
        Source.SUPPORT,
        2,
        Status.SHIPPED,
        Priority.LOW,
        False,
    ),
    (
        "Sidebar collapse forgets state on reload",
        FeedbackType.BUG,
        Source.OTHER,
        2,
        Status.NEW,
        Priority.LOW,
        False,
    ),
    (
        "Praise: keyboard shortcuts feel great",
        FeedbackType.PRAISE,
        Source.TWITTER,
        1,
        Status.CLOSED,
        None,
        False,
    ),
    (
        "Spam: please buy our SEO services",
        FeedbackType.OTHER,
        Source.WEB_FORM,
        1,
        Status.SPAM,
        None,
        False,
    ),
    (
        "Public submit form needs honeypot",
        FeedbackType.FEATURE_REQUEST,
        Source.OTHER,
        3,
        Status.SHIPPED,
        Priority.HIGH,
        False,
    ),
    (
        "Add Zendesk source mapping",
        FeedbackType.FEATURE_REQUEST,
        Source.EMAIL,
        3,
        Status.PLANNED,
        Priority.MEDIUM,
        False,
    ),
    (
        "Dashboard chart legends overflow on iPad",
        FeedbackType.BUG,
        Source.APP_STORE,
        2,
        Status.NEW,
        Priority.LOW,
        False,
    ),
    (
        "Public roadmap should hide internal tags",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        3,
        Status.ACCEPTED,
        Priority.MEDIUM,
        False,
    ),
    (
        "CSV import for bulk feedback",
        FeedbackType.FEATURE_REQUEST,
        Source.SUPPORT,
        4,
        Status.PLANNED,
        Priority.HIGH,
        True,
    ),
    (
        "Login email is case-sensitive (shouldn't be)",
        FeedbackType.BUG,
        Source.SUPPORT,
        3,
        Status.SHIPPED,
        Priority.MEDIUM,
        True,
    ),
    (
        "Roadmap kanban: drag-and-drop",
        FeedbackType.FEATURE_REQUEST,
        Source.INTERVIEW,
        3,
        Status.IN_PROGRESS,
        Priority.MEDIUM,
        False,
    ),
    (
        "Changelog RSS feed",
        FeedbackType.FEATURE_REQUEST,
        Source.REDDIT,
        2,
        Status.PLANNED,
        Priority.LOW,
        False,
    ),
)

DESCRIPTION_SNIPPETS = (
    "Reproduces consistently in latest stable browsers; no console errors visible.",
    "Multiple users in support thread #{n} report this; happens after 5-10 minutes of idle time.",
    "Originally reported in interview round 3; users expect this to behave like the rest of the product.",
    "Discovered during the WCAG audit. Fails 2.4.7 (Focus Visible) on Firefox 124+.",
    "Power user hit this exporting a quarterly report. No warning is shown to the user.",
    "Mentioned by {count} reviewers in the latest App Store dump.",
    "Customer is on the Pro plan and has integrated with two third-party tools.",
    "Filed via the public submit form; submitter has been emailed an acknowledgement.",
    "Cross-referenced with #{n} — likely the same root cause.",
    "Affects ~12 % of sessions per the analytics dashboard; not a top-five issue but recurring.",
)

NOTE_SNIPPETS = (
    "Reproduced locally — repro steps in the description.",
    "Pinged engineering on Slack; will assign once triaged.",
    "Linked to internal ticket FT-{n}.",
    "Customer was offered a workaround; awaiting their reply.",
    "Pulled the relevant logs; root cause looks like a stale cache.",
    "Marked as duplicate candidate of #{n}, leaving open until confirmed.",
    "Spoke to the submitter; they confirmed the workaround works for now.",
)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedStats:
    workspace_slug: str
    tags: int
    submitters: int
    feedback: int
    notes: int
    feedback_tags: int


def _resolve_workspace(
    session: Session,
    slug: str,
    *,
    create_if_missing: bool = False,
    owner_email: str | None = None,
    owner_password: str | None = None,
) -> Workspace:
    ws = session.execute(
        select(Workspace).where(Workspace.slug == slug),  # type: ignore[arg-type]
    ).scalar_one_or_none()
    if ws is not None:
        return ws
    if not create_if_missing:
        raise SystemExit(f"workspace with slug '{slug}' not found")
    if not owner_email or not owner_password:
        raise SystemExit(
            "--create-if-missing requires --owner-email and --owner-password",
        )

    # Imported lazily so the module's top-level import graph stays small
    # for the common case where the workspace already exists.
    from feedback_triage.auth.hashing import hash_password

    user = session.execute(
        select(User).where(User.email == owner_email),  # type: ignore[arg-type]
    ).scalar_one_or_none()
    if user is None:
        user = User(
            email=owner_email,
            password_hash=hash_password(owner_password),
            is_verified=True,
            role=UserRole.TEAM_MEMBER,
        )
        session.add(user)
        session.flush()
        assert user.id is not None
        logger.info("created user %s", owner_email)

    ws = Workspace(
        slug=slug,
        name=f"{slug}'s workspace",
        owner_id=user.id,
        is_demo=False,
    )
    session.add(ws)
    session.flush()
    assert ws.id is not None

    membership = WorkspaceMembership(
        workspace_id=ws.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    session.add(membership)
    session.flush()
    logger.info("created workspace %s owned by %s", slug, owner_email)
    return ws
    return ws


def _existing_count(session: Session, workspace_id: uuid.UUID) -> int:
    return int(
        session.execute(
            text("SELECT count(*) FROM feedback_item WHERE workspace_id = :w"),
            {"w": str(workspace_id)},
        ).scalar_one(),
    )


def _purge(session: Session, workspace_id: uuid.UUID) -> None:
    """Delete tags, submitters, and feedback for the workspace.

    Cascades take care of feedback_tags, feedback_notes, and the
    submitter FK on feedback_item.
    """
    # Order matters because feedback_item.submitter_id is ON DELETE SET NULL
    # but feedback_tags/notes cascade off feedback_item. Delete feedback
    # first (cascading its child rows), then submitters, then tags.
    session.execute(
        text("DELETE FROM feedback_item WHERE workspace_id = :w"),
        {"w": str(workspace_id)},
    )
    session.execute(
        text("DELETE FROM submitters WHERE workspace_id = :w"),
        {"w": str(workspace_id)},
    )
    session.execute(
        text("DELETE FROM tags WHERE workspace_id = :w"),
        {"w": str(workspace_id)},
    )


def _ensure_tags(session: Session, workspace_id: uuid.UUID) -> list[Tag]:
    existing = list(
        session.execute(
            select(Tag).where(Tag.workspace_id == workspace_id),  # type: ignore[arg-type]
        ).scalars(),
    )
    by_slug = {t.slug: t for t in existing}
    out: list[Tag] = list(existing)
    for name, slug, color in TAG_PALETTE:
        if slug in by_slug:
            continue
        tag = Tag(workspace_id=workspace_id, name=name, slug=slug, color=color)
        session.add(tag)
        out.append(tag)
    session.flush()
    return out


def _ensure_submitters(
    session: Session,
    workspace_id: uuid.UUID,
    rng: random.Random,
) -> list[Submitter]:
    out: list[Submitter] = []
    now = datetime.now(UTC)
    for full_name in SUBMITTER_NAMES:
        first, _, last = full_name.partition(" ")
        local = f"{first.lower()}.{last.lower()}".replace("'", "")
        domain = rng.choice(
            ("acme.test", "globex.test", "initech.test", "umbrella.test", "stark.test")
        )
        email = f"{local}@{domain}"
        seen = now - timedelta(days=rng.randint(0, 90), hours=rng.randint(0, 23))
        sub = Submitter(
            workspace_id=workspace_id,
            email=email,
            name=full_name,
            first_seen_at=seen,
            last_seen_at=seen + timedelta(days=rng.randint(0, 5)),
            submission_count=0,  # bumped as items are inserted
        )
        session.add(sub)
        out.append(sub)
    # A few anonymous (NULL email) submitters
    for _ in range(3):
        seen = now - timedelta(days=rng.randint(0, 90))
        sub = Submitter(
            workspace_id=workspace_id,
            email=None,
            name=None,
            first_seen_at=seen,
            last_seen_at=seen,
            submission_count=0,
        )
        session.add(sub)
        out.append(sub)
    session.flush()
    return out


def _make_description(idx: int, rng: random.Random) -> str:
    parts = rng.sample(DESCRIPTION_SNIPPETS, k=rng.randint(1, 2))
    text_ = " ".join(parts).format(n=rng.randint(100, 999), count=rng.randint(2, 30))
    return text_


def _seed_feedback(
    session: Session,
    workspace: Workspace,
    tags: list[Tag],
    submitters: list[Submitter],
    *,
    count: int,
    rng: random.Random,
    author_user_id: uuid.UUID,
) -> tuple[int, int, int]:
    now = datetime.now(UTC)
    items_inserted = 0
    notes_inserted = 0
    feedback_tags_inserted = 0

    # Build a bag of (template_index) so we cycle through templates and
    # then add small variations on top.
    n_templates = len(ITEM_TEMPLATES)
    for i in range(count):
        title, ftype, source, pain, status, priority, has_desc = ITEM_TEMPLATES[
            i % n_templates
        ]
        # Add a suffix when we wrap so titles stay unique-ish.
        suffix = ""
        if i >= n_templates:
            suffix = f" (#{i // n_templates + 1})"

        created_at = now - timedelta(
            days=rng.randint(0, 89),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        # updated_at is created_at plus some drift, capped at "now".
        updated_at = min(
            now,
            created_at + timedelta(days=rng.randint(0, 5), hours=rng.randint(0, 23)),
        )

        # 60 % of items have a submitter.
        submitter = rng.choice(submitters) if rng.random() < 0.6 else None

        description = (
            _make_description(i, rng) if (has_desc or rng.random() < 0.4) else None
        )

        published_to_roadmap = (
            status
            in {
                Status.PLANNED,
                Status.ACCEPTED,
                Status.IN_PROGRESS,
            }
            and rng.random() < 0.5
        )
        published_to_changelog = status == Status.SHIPPED and rng.random() < 0.7
        release_note = None
        if published_to_changelog:
            release_note = (
                f"Released {(title + suffix).lower()}. Available to all "
                "workspaces immediately."
            )[:280]

        item = FeedbackItem(
            title=(title + suffix)[:200],
            description=description,
            source=source,
            pain_level=pain,
            status=status,
            workspace_id=workspace.id,  # type: ignore[arg-type]
            submitter_id=submitter.id if submitter else None,
            type=ftype,
            priority=priority,
            published_to_roadmap=published_to_roadmap,
            published_to_changelog=published_to_changelog,
            release_note=release_note,
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(item)
        session.flush()
        items_inserted += 1

        if submitter is not None:
            submitter.submission_count = (submitter.submission_count or 0) + 1

        # Attach 0-3 tags, biased toward 1.
        n_tags = rng.choices([0, 1, 2, 3], weights=[3, 5, 3, 1])[0]
        for tag in rng.sample(tags, k=min(n_tags, len(tags))):
            session.add(FeedbackTag(feedback_id=item.id, tag_id=tag.id))  # type: ignore[arg-type]
            feedback_tags_inserted += 1

        # 25 % of items have 1-2 internal notes.
        if rng.random() < 0.25:
            for _ in range(rng.randint(1, 2)):
                note_body = rng.choice(NOTE_SNIPPETS).format(n=rng.randint(100, 999))
                note_at = updated_at - timedelta(hours=rng.randint(0, 12))
                session.add(
                    FeedbackNote(
                        feedback_id=item.id,  # type: ignore[arg-type]
                        author_user_id=author_user_id,
                        body=note_body,
                        created_at=note_at,
                    ),
                )
                notes_inserted += 1

    return items_inserted, notes_inserted, feedback_tags_inserted


def _resolve_owner_user_id(session: Session, workspace: Workspace) -> uuid.UUID:
    user = session.get(User, workspace.owner_id)
    if user is None:
        raise SystemExit(
            f"workspace owner {workspace.owner_id} not found in users table",
        )
    return user.id  # type: ignore[return-value]


def seed(
    *,
    slug: str,
    count: int,
    reset: bool,
    force: bool,
    seed_value: int,
    create_if_missing: bool = False,
    owner_email: str | None = None,
    owner_password: str | None = None,
) -> SeedStats:
    rng = random.Random(seed_value)  # nosec B311  # demo seed data, not cryptographic
    with SessionLocal() as session:
        workspace = _resolve_workspace(
            session,
            slug,
            create_if_missing=create_if_missing,
            owner_email=owner_email,
            owner_password=owner_password,
        )

        existing = _existing_count(session, workspace.id)  # type: ignore[arg-type]
        if existing and not (reset or force):
            print(
                f"workspace '{slug}' already has {existing} feedback rows; "
                "pass --reset to wipe or --force to add on top.",
                file=sys.stderr,
            )
            return SeedStats(slug, 0, 0, 0, 0, 0)

        if reset:
            _purge(session, workspace.id)  # type: ignore[arg-type]
            session.flush()

        author_user_id = _resolve_owner_user_id(session, workspace)
        tags = _ensure_tags(session, workspace.id)  # type: ignore[arg-type]
        submitters = _ensure_submitters(session, workspace.id, rng)  # type: ignore[arg-type]
        items, notes, ft_links = _seed_feedback(
            session,
            workspace,
            tags,
            submitters,
            count=count,
            rng=rng,
            author_user_id=author_user_id,
        )
        session.commit()

        return SeedStats(
            workspace_slug=slug,
            tags=len(tags),
            submitters=len(submitters),
            feedback=items,
            notes=notes,
            feedback_tags=ft_links,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Populate a workspace with realistic demo data.",
        epilog=(
            "Examples:\n"
            "  python scripts/seed_workspace.py --slug husky5084\n"
            "  python scripts/seed_workspace.py --slug husky5084 --reset\n"
            "  python scripts/seed_workspace.py --slug husky5084 --count 200\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--slug",
        required=False,
        default="husky5084",
        help="Target workspace slug (default: husky5084).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=150,
        help="Number of feedback items to insert (default: 150).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the workspace's existing tags, submitters, and feedback first.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Insert even if the workspace already has feedback.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for deterministic output (default: 42).",
    )
    parser.add_argument(
        "--smoke", action="store_true", help="Run a self-check (no DB access) and exit."
    )
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create the workspace (and owner user) if no row matches --slug.",
    )
    parser.add_argument(
        "--owner-email",
        default=None,
        help="Email for the owner user when --create-if-missing creates it.",
    )
    parser.add_argument(
        "--owner-password",
        default=None,
        help="Initial password for the owner user when --create-if-missing creates it.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    args = parser.parse_args(argv)

    if args.reset and args.force:
        parser.error("--reset and --force are mutually exclusive")

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    if args.smoke:
        # Validate templates and palette without touching the DB.
        assert len(ITEM_TEMPLATES) >= 30
        assert len(TAG_PALETTE) >= 5
        used_statuses = {tpl[4] for tpl in ITEM_TEMPLATES}
        assert Status.NEW in used_statuses
        assert Status.SHIPPED in used_statuses
        print(
            f"seed_workspace {SCRIPT_VERSION}: smoke ok ({len(ITEM_TEMPLATES)} templates)"
        )
        return 0

    stats = seed(
        slug=args.slug,
        count=args.count,
        reset=args.reset,
        force=args.force,
        seed_value=args.seed,
        create_if_missing=args.create_if_missing,
        owner_email=args.owner_email,
        owner_password=args.owner_password,
    )
    print(
        f"workspace={stats.workspace_slug} tags={stats.tags} "
        f"submitters={stats.submitters} feedback={stats.feedback} "
        f"notes={stats.notes} feedback_tags={stats.feedback_tags}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
