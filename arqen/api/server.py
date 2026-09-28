import hmac
import ipaddress
import json
import glob
import os
import shutil
import subprocess
import uuid
from dataclasses import asdict, is_dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from arqen import __version__
from arqen.application.service import ArqenApplication
from arqen.config import paths
from arqen.config.settings import load_mission_runtime_config
from arqen.mission import Approval, Event, MissionRunner, MissionScheduler, MissionStore, Schedule, Task, Workflow, WorkflowRunner, WorkflowStep
from arqen.mission.scheduler_worker import SchedulerWorker
from arqen.mission.task_worker import TaskWorker
from arqen.api.mobile_page import manifest, mobile_page, ICON_SVG


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


class ArqenHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], application: ArqenApplication, token: str,
                 run_workers: bool = True) -> None:
        # Anything but this computer can reach a server on another address,
        # and without a token every chat, task and tool would be open to it.
        if not token and not _is_loopback(server_address[0]):
            raise ValueError("A token is required to listen on anything but this computer.")
        super().__init__(server_address, ArqenRequestHandler)
        self.application = application
        self.token = token
        self.mission_store = MissionStore(paths.data_dir() / "mission.sqlite3")
        runtimes = self._mission_runtimes()
        self.mission_runner = MissionRunner(self.mission_store, application._engine_factory, runtimes)
        self.workflow_runner = WorkflowRunner(self.mission_store, self.mission_runner)
        # Started here when the API runs on its own; the desktop app runs its own.
        self.scheduler_worker = None
        self.task_worker = None
        if run_workers:
            self.scheduler_worker = SchedulerWorker(MissionScheduler(self.mission_store, self.workflow_runner))
            self.scheduler_worker.start()
            self.task_worker = TaskWorker(self.mission_store, self.mission_runner)
            self.task_worker.start()

    def server_close(self) -> None:
        if self.task_worker is not None:
            self.task_worker.stop()
        if self.scheduler_worker is not None:
            self.scheduler_worker.stop()
        super().server_close()

    def _mission_runtimes(self) -> dict[str, Any]:
        config = load_mission_runtime_config()
        hermes = config.get("hermes", {})
        if not isinstance(hermes, dict) or not str(hermes.get("executable", "")).strip():
            return {}
        from arqen.mission import HermesRuntime
        runtime = HermesRuntime(str(hermes["executable"]), hermes.get("working_dir"), float(hermes.get("timeout", 300)))
        return {agent.id: runtime for agent in self.mission_store.list_agents() if agent.runtime == "hermes"}


class ArqenRequestHandler(BaseHTTPRequestHandler):
    server: ArqenHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        # One line per request is noise (the phone polls every 20 seconds),
        # and under pythonw there is no stderr to write it to: the base
        # class's write then broke every request.
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path == "/":
                self._send_html(mobile_page())
                return
            if path == "/manifest.webmanifest":
                self._send_bytes(json.dumps(manifest()).encode("utf-8"), "application/manifest+json")
                return
            if path == "/icon.svg":
                self._send_bytes(ICON_SVG.encode("utf-8"), "image/svg+xml")
                return
            if path == "/control":
                self._send_html(CONTROL_PAGE)
                return
            if path == "/api/v1/health":
                self._send_json(HTTPStatus.OK, {"data": {"status": "ok", "version": __version__}})
                return
            self._require_auth()
            if path == "/api/v1/status":
                self._send_json(HTTPStatus.OK, {"data": self._as_json(self.server.application.status())})
                return
            if path == "/api/v1/tools":
                self._send_json(HTTPStatus.OK, {"data": self.server.application.tool_catalog()})
                return
            if path == "/api/v1/tools/policies":
                self._send_json(HTTPStatus.OK, {"data": self.server.application.tool_policies()})
                return
            if path == "/api/v1/tools/audit":
                self._send_json(HTTPStatus.OK, {"data": self.server.application.tool_audit()})
                return
            if path == "/api/v1/control/status":
                self._send_json(HTTPStatus.OK, {"data": self._control_status()})
                return
            if path == "/api/v1/mission/tasks":
                tasks = self.server.mission_store.list_tasks()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in tasks]})
                return
            if path == "/api/v1/mission/activity":
                events = self.server.mission_store.list_all_events()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in events]})
                return
            if path == "/api/v1/mission/agents":
                agents = self.server.mission_store.list_agents()
                data = []
                for agent in agents:
                    item = self._as_json(agent)
                    item["runtime_status"] = self.server.mission_runner.runtime_status(agent.id)
                    data.append(item)
                self._send_json(HTTPStatus.OK, {"data": data})
                return
            if path == "/api/v1/mission/approvals":
                approvals = self.server.mission_store.list_approvals()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in approvals]})
                return
            if path == "/api/v1/mission/schedules":
                schedules = self.server.mission_store.list_schedules()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in schedules]})
                return
            if path == "/api/v1/mission/workflows":
                workflows = self.server.mission_store.list_workflows()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in workflows]})
                return
            if path.startswith("/api/v1/mission/workflows/") and path.endswith("/runs"):
                workflow_id = path.removeprefix("/api/v1/mission/workflows/").removesuffix("/runs").strip("/")
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in self.server.mission_store.list_workflow_runs(workflow_id)]})
                return
            if path.startswith("/api/v1/mission/runs/") and path.endswith("/resume"):
                # Resuming starts work, so it must not happen on a read: a
                # link, a prefetch or a crawler could otherwise trigger it.
                self._error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Use POST to resume a run.")
                return
            if path.startswith("/api/v1/mission/tasks/"):
                task_id = path.removeprefix("/api/v1/mission/tasks/").strip("/")
                if not task_id or "/" in task_id:
                    raise FileNotFoundError(task_id)
                task = self.server.mission_store.get_task(task_id)
                if task is None:
                    raise FileNotFoundError(task_id)
                self._send_json(HTTPStatus.OK, {"data": {"task": self._as_json(task), "events": self._as_json(self.server.mission_store.list_events(task_id))}})
                return
            if path == "/api/v1/sessions":
                sessions = self.server.application.list_sessions()
                self._send_json(HTTPStatus.OK, {"data": [self._as_json(item) for item in sessions]})
                return
            if path.startswith("/api/v1/sessions/"):
                session_id = self._session_id(path)
                session = self.server.application.get_session(session_id)
                data = self._as_json(session)
                data["confirmation"] = self.server.application.pending_confirmation(session_id)
                self._send_json(HTTPStatus.OK, {"data": data})
                return
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except PermissionError as exc:
            self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", str(exc))
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "An internal error occurred.")

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        try:
            self._require_auth()
            payload = self._read_json()
            if path == "/api/v1/sessions":
                result = self.server.application.create_session(str(payload.get("title", "New chat")))
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(result)})
                return
            if path == "/api/v1/mission/tasks":
                title = str(payload.get("title", "")).strip()
                prompt = str(payload.get("prompt", "")).strip()
                if not title or not prompt:
                    raise ValueError("title and prompt are required.")
                task = Task.create(title, prompt, payload.get("agent_id"))
                self.server.mission_store.save_task(task)
                self.server.mission_store.add_event(Event.create(task.id, "created", "Task created"))
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(task)})
                return
            if path == "/api/v1/mission/agents":
                agent_id = str(payload.get("id", "")).strip()
                name = str(payload.get("name", "")).strip()
                role = str(payload.get("role", "")).strip()
                if not agent_id or not name or not role:
                    raise ValueError("id, name and role are required.")
                from arqen.mission import Agent
                agent = Agent(agent_id, name, role, str(payload.get("runtime", "arqen")), bool(payload.get("enabled", True)))
                self.server.mission_store.save_agent(agent)
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(agent)})
                return
            if path == "/api/v1/mission/approvals":
                task_id = str(payload.get("task_id", "")).strip()
                action = str(payload.get("action", "")).strip()
                if not task_id or not action:
                    raise ValueError("task_id and action are required.")
                approval = Approval(__import__("uuid").uuid4().hex, task_id, action, dict(payload.get("payload", {})))
                self.server.mission_store.save_approval(approval)
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(approval)})
                return
            if path == "/api/v1/mission/schedules":
                name = str(payload.get("name", "")).strip()
                prompt = str(payload.get("prompt", "")).strip()
                if not name or not prompt or (not payload.get("cron") and not payload.get("run_at")):
                    raise ValueError("name, prompt and cron or run_at are required.")
                schedule = Schedule(uuid.uuid4().hex, name, prompt, payload.get("agent_id"), payload.get("cron"), payload.get("run_at"), True, workflow_id=payload.get("workflow_id"))
                self.server.mission_store.save_schedule(schedule)
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(schedule)})
                return
            if path == "/api/v1/mission/workflows":
                name = str(payload.get("name", "")).strip()
                raw_steps = payload.get("steps", [])
                if not name or not isinstance(raw_steps, list) or not raw_steps:
                    raise ValueError("name and at least one step are required.")
                steps = tuple(WorkflowStep(str(step.get("name", "")).strip(), str(step.get("prompt", "")).strip(), step.get("agent_id")) for step in raw_steps)
                if any(not step.name or not step.prompt for step in steps):
                    raise ValueError("Every step needs a name and a prompt.")
                workflow = Workflow(uuid.uuid4().hex, name, steps)
                self.server.mission_store.save_workflow(workflow)
                self._send_json(HTTPStatus.CREATED, {"data": self._as_json(workflow)})
                return
            if path.startswith("/api/v1/mission/workflows/") and path.endswith("/run"):
                workflow_id = path.removeprefix("/api/v1/mission/workflows/").removesuffix("/run").strip("/")
                workflow = next((item for item in self.server.mission_store.list_workflows() if item.id == workflow_id), None)
                if workflow is None:
                    raise FileNotFoundError(workflow_id)
                results = self.server.workflow_runner.run(workflow.name, list(workflow.steps), workflow.id)
                self._send_json(HTTPStatus.OK, {"data": {"workflow_id": workflow.id, "results": results}})
                return
            if path.startswith("/api/v1/mission/approvals/") and path.endswith("/decision"):
                approval_id = path.removeprefix("/api/v1/mission/approvals/").removesuffix("/decision").strip("/")
                store = self.server.mission_store
                store.decide_approval(approval_id, str(payload.get("status", "")))
                approval = store.get_approval(approval_id)
                if approval is None:
                    raise FileNotFoundError(approval_id)
                # Resume on both answers, as the desktop app does: a rejection
                # is what cancels the task, otherwise it waits forever.
                result = None
                task = store.get_task(approval.task_id)
                if task is not None and task.status == "waiting_approval":
                    result = self.server.mission_runner.resume(approval.task_id)
                task = store.get_task(approval.task_id)
                data = {**self._as_json(approval), "task_status": task.status if task else None, "result": result}
                self._send_json(HTTPStatus.OK, {"data": data})
                return
            if path.startswith("/api/v1/mission/runs/") and path.endswith("/resume"):
                run_id = path.removeprefix("/api/v1/mission/runs/").removesuffix("/resume").strip("/")
                results = self.server.workflow_runner.resume(run_id)
                self._send_json(HTTPStatus.OK, {"data": {"run_id": run_id, "results": results}})
                return
            if path.endswith("/run") and path.startswith("/api/v1/mission/tasks/"):
                task_id = path.removeprefix("/api/v1/mission/tasks/").removesuffix("/run").strip("/")
                result = self.server.mission_runner.run(task_id)
                self._send_json(HTTPStatus.OK, {"data": {"task_id": task_id, "result": result}})
                return
            if path.endswith("/resume") and path.startswith("/api/v1/mission/tasks/"):
                task_id = path.removeprefix("/api/v1/mission/tasks/").removesuffix("/resume").strip("/")
                result = self.server.mission_runner.resume(task_id)
                self._send_json(HTTPStatus.OK, {"data": {"task_id": task_id, "result": result}})
                return
            if path.endswith("/confirmation") and path.startswith("/api/v1/sessions/"):
                session_id = path.removeprefix("/api/v1/sessions/").removesuffix("/confirmation").strip("/")
                if not isinstance(payload.get("approve"), bool):
                    raise ValueError("approve (true or false) is required.")
                result = self.server.application.confirm(session_id, payload["approve"])
                self._send_json(HTTPStatus.OK, {"data": self._as_json(result)})
                return
            if path.endswith("/messages") and path.startswith("/api/v1/sessions/"):
                session_id = path.removeprefix("/api/v1/sessions/").removesuffix("/messages").strip("/")
                result = self.server.application.send_message(session_id, str(payload.get("content", "")))
                self._send_json(HTTPStatus.OK, {"data": self._as_json(result)})
                return
            if path == "/api/v1/voice/stop":
                # This used to answer without stopping anything.
                from arqen.tools.speech import stop_speech

                stop_speech()
                self._send_json(HTTPStatus.OK, {"data": {"status": "stopped"}})
                return
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except ValueError as exc:
            self._error(HTTPStatus.UNPROCESSABLE_ENTITY, "validation_error", str(exc))
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except PermissionError as exc:
            self._error(HTTPStatus.UNAUTHORIZED, "unauthorized", str(exc))
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "An internal error occurred.")

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        try:
            self._require_auth()
            if not path.startswith("/api/v1/sessions/"):
                self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
                return
            payload = self._read_json()
            result = self.server.application.rename_session(self._session_id(path), str(payload.get("title", "")))
            self._send_json(HTTPStatus.OK, {"data": self._as_json(result)})
        except ValueError as exc:
            self._error(HTTPStatus.UNPROCESSABLE_ENTITY, "validation_error", str(exc))
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "An internal error occurred.")

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        try:
            self._require_auth()
            self.server.application.delete_session(self._session_id(path))
            self._send_json(HTTPStatus.OK, {"data": {"status": "deleted"}})
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Not found.")
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "An internal error occurred.")

    def _require_auth(self) -> None:
        expected = self.server.token
        if not expected:
            return
        authorization = self.headers.get("Authorization", "")
        # Compared in constant time, so the answer's timing gives nothing away.
        if not hmac.compare_digest(authorization.encode("utf-8"), f"Bearer {expected}".encode("utf-8")):
            raise PermissionError("A valid Bearer token is required.")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 1_000_000:
            raise ValueError("The JSON body is missing or too large.")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("The JSON body must be an object.")
        return payload

    def _session_id(self, path: str) -> str:
        value = path.removeprefix("/api/v1/sessions/").strip("/")
        if not value or "/" in value:
            raise FileNotFoundError(value)
        return value

    def _control_status(self) -> dict[str, Any]:
        disk = shutil.disk_usage("/")
        memory = "unknown"
        try:
            memory = subprocess.check_output(["free", "-h"], text=True, timeout=2).splitlines()[1].split()[2]
        except (OSError, IndexError, subprocess.SubprocessError):
            pass
        try:
            ollama = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=3).stdout.strip()
            ollama_status = "online" if ollama else "idle"
        except (OSError, subprocess.SubprocessError):
            ollama_status = "offline"
        timer_status = "unknown"
        last_health = "unknown"
        try:
            timer_status = subprocess.run(
                ["systemctl", "is-active", "arqen-healthcheck.timer"],
                capture_output=True, text=True, timeout=2,
            ).stdout.strip() or "inactive"
            last_health = subprocess.run(
                ["journalctl", "-t", "arqen-health", "-n", "1", "--no-pager", "-o", "cat"],
                capture_output=True, text=True, timeout=2,
            ).stdout.strip() or "unknown"
        except (OSError, subprocess.SubprocessError):
            pass
        status = self._as_json(self.server.application.status())
        backups = sorted(glob.glob("/var/backups/arqen/arqen-*.tar.gz"), reverse=True)
        backup_age = "unknown"
        if backups:
            backup_age = f"{round((__import__('time').time() - os.path.getmtime(backups[0])) / 3600, 1)} h"
        return {"api": "online", "model": status.get("model", ""), "ollama": ollama_status,
                "memory_used": memory, "disk_used_percent": round(disk.used / disk.total * 100),
                "sessions": len(self.server.application.list_sessions()), "healthcheck": timer_status,
                "last_health": last_health, "telegram": "configured" if os.path.exists("/etc/arqen-telegram.env") else "not configured",
                "latest_backup": os.path.basename(backups[0]) if backups else "none", "backup_age": backup_age}

    def _send_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_html(self, html: str) -> None:
        self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8")

    def _send_bytes(self, encoded: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self, status: HTTPStatus, code: str, message: str) -> None:
        self._send_json(status, {"error": {"code": code, "message": message}})

    @staticmethod
    def _as_json(value: Any) -> Any:
        if is_dataclass(value):
            result = asdict(value)
            if "messages" in result:
                result["messages"] = [ArqenRequestHandler._as_json(item) for item in value.messages]
            return result
        if isinstance(value, list):
            return [ArqenRequestHandler._as_json(item) for item in value]
        if isinstance(value, dict):
            return {key: ArqenRequestHandler._as_json(item) for key, item in value.items()}
        return value


def create_server(application: ArqenApplication, host: str = "127.0.0.1", port: int = 8765, token: str = "",
                  run_workers: bool = True) -> ArqenHTTPServer:
    """Create an API server; call serve_forever() from the host process.

    ``run_workers`` starts the scheduler and task worker; the desktop app,
    which runs its own, passes False.
    """
    return ArqenHTTPServer((host, port), application, token, run_workers)


CONTROL_PAGE = r"""<!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Arqen Control</title>
<style>*{box-sizing:border-box}body{margin:0;background:#101214;color:#e9eee8;font:16px system-ui,sans-serif}main{max-width:980px;margin:auto;padding:28px 18px}h1{color:#b7ff18;letter-spacing:.1em}input,button{padding:12px;border:1px solid #343b37;border-radius:8px;background:#1d2220;color:#fff;font:inherit}input{width:70%}button{background:#b7ff18;color:#101214;font-weight:700;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-top:22px}.card{background:#191d1b;border:1px solid #303832;border-radius:12px;padding:18px}.label{color:#89958c;font-size:.85rem}.value{font-size:1.35rem;margin-top:7px;color:#b7ff18}#message{margin-top:18px;color:#aab5ad}</style></head>
<body><main><h1>ARQEN CONTROL</h1><p>Server status and operations</p><input id="token" type="password" placeholder="API token"><button onclick="loadStatus()">CONNECT</button><div id="message">Enter the token to read the status.</div><section class="grid" id="grid"></section></main>
<script>async function loadStatus(){const token=document.getElementById('token').value;try{const r=await fetch('/api/v1/control/status',{headers:{Authorization:'Bearer '+token}});const j=await r.json();if(!r.ok)throw Error(j.error?.message||'Error');const d=j.data;const rows=[['API',d.api],['Ollama',d.ollama],['Model',d.model],['RAM used',d.memory_used],['Disk',d.disk_used_percent+'%'],['Sessions',d.sessions],['Healthcheck',d.healthcheck],['Telegram',d.telegram],['Backup',d.latest_backup],['Backup age',d.backup_age],['Latest check',d.last_health]];document.getElementById('grid').innerHTML=rows.map(x=>'<div class="card"><div class="label">'+x[0]+'</div><div class="value">'+x[1]+'</div></div>').join('');document.getElementById('message').textContent='Last updated: '+new Date().toLocaleTimeString()}catch(e){document.getElementById('message').textContent=e.message}}setInterval(()=>{if(document.getElementById('token').value)loadStatus()},30000)</script></body></html>"""
