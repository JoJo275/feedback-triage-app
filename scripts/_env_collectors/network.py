"""Network collector — DNS, proxy, outbound summary."""

from __future__ import annotations

import os
import socket
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class NetworkCollector(BaseCollector):
    """Collect DNS, proxy, and basic outbound connectivity info."""

    name = "network"
    timeout = 10.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        env = os.environ
        proxy = {
            "http_proxy": env.get("HTTP_PROXY") or env.get("http_proxy", ""),
            "https_proxy": env.get("HTTPS_PROXY") or env.get("https_proxy", ""),
            "no_proxy": env.get("NO_PROXY") or env.get("no_proxy", ""),
        }

        dns_ok = False
        try:
            socket.getaddrinfo("pypi.org", 443, socket.AF_INET, socket.SOCK_STREAM)
            dns_ok = True
        except (socket.gaierror, OSError):
            pass

        outbound_ok = False
        try:
            sock = socket.create_connection(("pypi.org", 443), timeout=5)
            sock.close()
            outbound_ok = True
        except (OSError, TimeoutError):
            pass

        return {
            "proxy": proxy,
            "dns_resolves": dns_ok,
            "outbound_https": outbound_ok,
            "hostname": socket.gethostname(),
        }
