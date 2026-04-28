# ADR 049: Offset Pagination with Documented Keyset Upgrade Path

## Status

Proposed

## Context

The list endpoint (`GET /api/v1/feedback`) needs paging. The two
candidates:

- **Offset pagination** (`skip`, `limit`) — simple, matches a "Page N of
  M" UI, fine up to ~10k rows.
- **Keyset pagination** (cursor on `(created_at DESC, id DESC)`) —
  scales without `OFFSET` cost, stable under concurrent inserts, but
  needs the UI to either render "Older / Newer" controls or hide the
  page count.

Offset has two known weaknesses: deep-page cost (`OFFSET 100000` scans
100k rows) and result drift when rows are inserted between page loads.

## Decision

v1.0 uses **offset pagination**. Response shape is the documented
envelope: `{items, total, skip, limit}`. The frontend uses `total` to
render "Page N of M".

The list endpoint also supports `sort_by` from a closed allow-list
(`created_at`, `pain_level`, `status`, `source`, optionally prefixed
with `-` for descending).

Switch to keyset pagination when **either** of the following is true:

1. P95 latency on `GET /api/v1/feedback?skip=…` exceeds 200ms with
   `skip > 1000` against a realistic dataset.
2. The list view shows result drift complaints from real users.

The migration is mechanical: keep the route, change the query plan,
add `cursor_after` query param, remove `total` from the envelope (or
make it best-effort).

## Alternatives Considered

### Keyset from day one

**Rejected because:** the UI calls for "Page N of M", which keyset
makes awkward. v1.0 datasets are small; the cost is not real yet.

### Bare-array response

**Rejected because:** the UI always needs `total` to render pager
controls. Forcing a second request or a header is friction the spec
already pushed back against.

## Consequences

### Positive

- Trivial to implement.
- Matches the UI's expectations.
- Easy to test.

### Negative

- Known scaling cliff. Documented as Future Improvement.
