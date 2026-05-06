"""Service-layer helpers shared across API routers.

Each module here owns the multi-table writes for one bounded context
so the route handlers stay thin (read body → call service → return
response). The transaction boundary always lives in ``get_db``; nothing
in this package opens its own session.
"""
