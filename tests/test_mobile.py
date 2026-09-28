"""Reaching Arqen from a phone: tool approvals over the API, the token and the settings."""

import json
from pathlib import Path

import pytest

from arqen.api import mobile
from arqen.api.mobile_page import mobile_page
from arqen.api.server import create_server
from arqen.application.service import ArqenApplication
from arqen.core.engine import ConversationEngine
from arqen.core.session_store import SessionStore
from arqen.ui import strings
from tests.test_api_server import request
from tests.test_cloud_tool_calls import ConfirmThenAnswerProvider, _confirm_registry


def _application(tmp_path: Path) -> ArqenApplication:
    return ArqenApplication(
        lambda: ConversationEngine(ConfirmThenAnswerProvider(), tools=_confirm_registry()),
        SessionStore(tmp_path / "sessions"),
    )


def test_a_tool_that_needs_approval_waits_and_the_phone_can_approve_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = _application(tmp_path)
    session = app.create_session()
    asked = app.send_message(session.session_id, "write hej")
    assert asked.status == "needs_confirmation"
    assert asked.confirmation == {"tool": "confirm_me", "arguments": {"text": "hej"}}
    assert app.pending_confirmation(session.session_id) == asked.confirmation

    done = app.confirm(session.session_id, True)
    assert done.status == "ready" and done.confirmation is None
    assert done.assistant_message == "Klart, jag skrev hej."
    assert app.pending_confirmation(session.session_id) is None


def test_rejecting_cancels_the_tool(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = _application(tmp_path)
    session = app.create_session()
    app.send_message(session.session_id, "write hej")
    assert app.confirm(session.session_id, False).assistant_message == "Tool request cancelled"


def test_confirming_with_nothing_waiting_is_an_error(tmp_path):
    app = _application(tmp_path)
    session = app.create_session()
    with pytest.raises(ValueError):
        app.confirm(session.session_id, True)


def test_the_confirmation_round_trip_over_http(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    server = create_server(_application(tmp_path), port=0, token="t", run_workers=False)
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        _, created = request(server, "POST", "/api/v1/sessions", {}, token="t")
        session_id = created["data"]["session_id"]
        _, asked = request(server, "POST", f"/api/v1/sessions/{session_id}/messages", {"content": "write hej"}, token="t")
        assert asked["data"]["status"] == "needs_confirmation"
        _, session = request(server, "GET", f"/api/v1/sessions/{session_id}", token="t")
        assert session["data"]["confirmation"]["tool"] == "confirm_me"
        status, bad = request(server, "POST", f"/api/v1/sessions/{session_id}/confirmation", {"approve": "yes"}, token="t")
        assert status == 422
        status, done = request(server, "POST", f"/api/v1/sessions/{session_id}/confirmation", {"approve": True}, token="t")
        assert status == 200 and done["data"]["assistant_message"] == "Klart, jag skrev hej."
        assert server.task_worker is None, "the desktop app runs the workers itself"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_the_server_refuses_to_listen_beyond_this_computer_without_a_token(tmp_path):
    app = _application(tmp_path)
    with pytest.raises(ValueError):
        create_server(app, host="0.0.0.0", port=0, token="", run_workers=False)
    create_server(app, host="127.0.0.1", port=0, token="", run_workers=False).server_close()


def test_settings_and_token_are_kept_apart(tmp_path):
    assert mobile.load_settings() == mobile.MobileSettings()
    mobile.save_settings(mobile.MobileSettings(True, "lan", 9000))
    assert mobile.load_settings() == mobile.MobileSettings(True, "lan", 9000)
    token = mobile.api_token()
    assert len(token) >= 40 and mobile.api_token() == token
    config = json.loads((tmp_path / "config" / "arqen.json").read_text(encoding="utf-8"))
    assert token not in json.dumps(config)
    from arqen.config.secrets import scrub

    assert token not in scrub(f"the token is {token}")
    assert mobile.new_token() != token
    with pytest.raises(ValueError):
        mobile.save_settings(mobile.MobileSettings(True, "internet", 9000))


def test_the_phone_link_keeps_the_token_out_of_requests():
    url = mobile.phone_url("100.64.0.7", 8765, "abc")
    assert url == "http://100.64.0.7:8765/#token=abc"


def test_the_local_network_listens_everywhere_but_tailscale_only_on_its_address(monkeypatch):
    monkeypatch.setattr(mobile, "tailscale_address", lambda: "100.64.0.7")
    monkeypatch.setattr(mobile, "lan_address", lambda: "192.168.1.20")
    assert mobile.addresses("tailscale") == ("100.64.0.7", "100.64.0.7")
    assert mobile.addresses("lan") == ("0.0.0.0", "192.168.1.20")
    assert mobile.addresses("local") == ("127.0.0.1", "127.0.0.1")
    monkeypatch.setattr(mobile, "tailscale_address", lambda: "")
    with pytest.raises(RuntimeError):
        mobile.addresses("tailscale")


def test_the_mobile_server_starts_and_stops(tmp_path):
    server = mobile.MobileServer(lambda: _application(tmp_path))
    assert server.start(mobile.MobileSettings(True, "local", 18765))
    try:
        assert server.running and server.url().startswith("http://127.0.0.1:")
        assert "#token=" in server.url(with_token=True)
    finally:
        server.stop()
    assert not server.running and server.url() == ""


def test_the_phone_page_speaks_the_ui_language():
    page = mobile_page()
    assert '<html lang="sv">' in page and "Godkännanden" in page
    strings.set_language("en")
    try:
        page = mobile_page()
        assert '<html lang="en">' in page and '"approvals": "Approvals"' in page
    finally:
        strings.set_language("sv")


def test_health_reports_the_version(tmp_path):
    import threading

    from arqen import __version__

    server = create_server(_application(tmp_path), port=0, token="t", run_workers=False)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        _, health = request(server, "GET", "/api/v1/health", token="")
        assert health["data"] == {"status": "ok", "version": __version__}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
