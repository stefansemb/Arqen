"""Reach Arqen from a phone: the local API, started and stopped by the desktop app.

Mobile access is off until it is turned on under Settings → Mobile.  The
settings (on/off, network, port) live in ``arqen.json`` under ``"mobile"``;
the token lives in ``arqen-secrets.json`` under ``"mobile"``, so the tool
gateway scrubs it from tool output like any other key.

The network decides which address the server listens on:

- ``tailscale``: only the computer's Tailscale address, so only devices in
  the person's own tailnet can connect.  The recommended choice.
- ``lan``: every interface, so anything on the local network can connect
  (with the token).
- ``local``: this computer only, for trying the mobile page in a browser.
"""

from __future__ import annotations

import ipaddress
import json
import secrets as token_source
import socket
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from arqen.config import paths

NETWORKS = ("tailscale", "lan", "local")
DEFAULT_PORT = 8765
# Tailscale hands out addresses from the carrier-grade NAT range.
_TAILSCALE_RANGE = ipaddress.ip_network("100.64.0.0/10")


@dataclass
class MobileSettings:
    enabled: bool = False
    network: str = "tailscale"
    port: int = DEFAULT_PORT


def _read(name: str) -> dict:
    path = paths.config_dir() / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_section(name: str, section: dict) -> None:
    # Both files are shared with the rest of Arqen: keep every other key.
    data = _read(name)
    data["mobile"] = section
    path = paths.config_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_settings() -> MobileSettings:
    section = _read("arqen.json").get("mobile")
    if not isinstance(section, dict):
        return MobileSettings()
    network = str(section.get("network", "tailscale"))
    try:
        port = int(section.get("port", DEFAULT_PORT))
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    return MobileSettings(
        enabled=bool(section.get("enabled", False)),
        network=network if network in NETWORKS else "tailscale",
        port=port if 1024 <= port <= 65535 else DEFAULT_PORT,
    )


def save_settings(settings: MobileSettings) -> None:
    if settings.network not in NETWORKS:
        raise ValueError(f"Unknown network: {settings.network}")
    if not 1024 <= settings.port <= 65535:
        raise ValueError("The port must be between 1024 and 65535.")
    _write_section("arqen.json", {"enabled": settings.enabled, "network": settings.network, "port": settings.port})


def api_token() -> str:
    """The phone's token, created the first time it is needed."""
    section = _read("arqen-secrets.json").get("mobile")
    token = str(section.get("token", "")) if isinstance(section, dict) else ""
    return token or new_token()


def new_token() -> str:
    """Replace the token; phones signed in with the old one must scan again."""
    token = token_source.token_urlsafe(32)
    _write_section("arqen-secrets.json", {"token": token})
    return token


def tailscale_address() -> str:
    """This computer's Tailscale IPv4 address, or "" without Tailscale."""
    try:
        completed = subprocess.run(
            ["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in completed.stdout.splitlines():
            if _is_tailscale(line.strip()):
                return line.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    # The CLI can be missing from PATH while Tailscale runs; look at the interfaces.
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            if _is_tailscale(info[4][0]):
                return info[4][0]
    except OSError:
        pass
    return ""


def _is_tailscale(address: str) -> bool:
    try:
        return ipaddress.ip_address(address) in _TAILSCALE_RANGE
    except ValueError:
        return False


def lan_address() -> str:
    """The address other devices on the local network reach this computer at."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connecting a UDP socket sends nothing; it only picks the outgoing interface.
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return ""
    finally:
        probe.close()


def addresses(network: str) -> tuple[str, str]:
    """Where the server listens and the address the phone opens, for ``network``.

    Raises ``RuntimeError`` when the network is not available, e.g. Tailscale
    is not running.
    """
    if network == "local":
        return "127.0.0.1", "127.0.0.1"
    if network == "tailscale":
        address = tailscale_address()
        if not address:
            raise RuntimeError("Tailscale is not running on this computer.")
        return address, address
    address = lan_address()
    if not address:
        raise RuntimeError("This computer is not on a local network.")
    return "0.0.0.0", address


def phone_url(address: str, port: int, token: str = "") -> str:
    """The address to open on the phone; the token rides in the fragment.

    A fragment never leaves the phone's browser, so the token is not sent in
    requests or kept in server logs; the page reads it and stores it.
    """
    url = f"http://{address}:{port}/"
    return f"{url}#token={token}" if token else url


class MobileServer:
    """The API server in a background thread of the desktop app."""

    def __init__(self, application_factory: Callable[[], object]) -> None:
        self._application_factory = application_factory
        self._server = None
        self._thread: threading.Thread | None = None
        self.address = ""
        self.port = 0
        self.error = ""

    @property
    def running(self) -> bool:
        return self._server is not None

    def start(self, settings: MobileSettings) -> bool:
        """Start (or restart) with ``settings``; on failure ``error`` says why."""
        from arqen.api.server import create_server

        self.stop()
        self.error = ""
        try:
            host, self.address = addresses(settings.network)
            # The desktop app already runs the scheduler and task worker.
            self._server = create_server(
                self._application_factory(), host=host, port=settings.port,
                token=api_token(), run_workers=False,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self._server = None
            self.error = str(exc)
            return False
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="arqen-mobile-api")
        self._thread.start()
        return True

    def stop(self) -> None:
        server, self._server = self._server, None
        if server is None:
            return
        server.shutdown()
        server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._thread = None

    def url(self, with_token: bool = False) -> str:
        if not self.running:
            return ""
        return phone_url(self.address, self.port, api_token() if with_token else "")
