---
description: >-
  Use when working on environment data collectors: adding new collectors,
  modifying collection logic, changing the Tier system, or updating
  the insights/warnings engine in scripts/_env_collectors/.
applyTo: "scripts/_env_collectors/**"
---

# Environment Collectors — Copilot Instructions

## Architecture

Plugin-based collector system. Each collector extends `BaseCollector` and
is registered in `__init__.py._discover_collectors()`.

## Collector Structure

```python
class MyCollector(BaseCollector):
    name = "my_section"      # Section key in output dict
    timeout = 5.0            # Per-collector timeout (seconds)

    @property
    def tier(self):
        return Tier.STANDARD  # MINIMAL, STANDARD, or FULL

    def collect(self) -> dict[str, Any]:
        return {"key": "value"}
```

## Tiers

| Tier | Speed | Use Case |
|------|-------|----------|
| MINIMAL | Fast (<1s) | Essential project info only |
| STANDARD | Moderate (1-5s) | Default dashboard view |
| FULL | Slow (5s+) | Complete diagnostics |

## Insights Collector (Warnings)

`InsightsCollector` runs AFTER all other collectors. It receives
`self._sections` (all collected data) and derives warnings:

```python
{"severity": "warn|fail|info", "message": "...", "section": "..."}
```

When adding warnings, also add `hint` and `action` fields for UI display.

## Adding a New Collector

1. Create `scripts/_env_collectors/<name>.py`
2. Import and add to `_discover_collectors()` in `__init__.py`
3. Create matching template `tools/dev_tools/env_dashboard/templates/partials/<name>.html`
4. Add tests in `tests/unit/`

## Conventions

- Use `from __future__ import annotations` in every file
- Type hints on all public functions
- Timeout must be set — prevents one slow collector from blocking all
- Use `shutil.which()` for tool detection, not `subprocess` calls
