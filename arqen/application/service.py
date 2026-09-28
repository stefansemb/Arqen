import threading
from dataclasses import dataclass
from typing import Any, Callable

from arqen.core.engine import ConversationEngine
from arqen.core.session_store import DEFAULT_TITLE, ChatSession, SessionStore
from arqen.ui.strings import tr


@dataclass(frozen=True)
class MessageResult:
    session_id: str
    user_message: str
    assistant_message: str
    speakable: bool
    # "ready", or "needs_confirmation" when a tool waits for the user; then
    # ``confirmation`` names the tool and its arguments.
    status: str = "ready"
    confirmation: dict[str, Any] | None = None


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ArqenStatus:
    provider: str
    model: str
    voice_enabled: bool
    session_id: str
    status: str = "ready"


class ArqenApplication:
    """Application boundary shared by desktop, API and future mobile clients."""

    def __init__(
        self,
        engine_factory: Callable[[], ConversationEngine],
        session_store: SessionStore | None = None,
    ) -> None:
        self.session_store = session_store or SessionStore()
        self._engine_factory = engine_factory
        self._engines: dict[str, ConversationEngine] = {}
        # One turn at a time per chat: two requests on the same engine would
        # interleave their messages and tool calls.
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def create_session(self, title: str = DEFAULT_TITLE) -> SessionSummary:
        session = self.session_store.create(title)
        self.session_store.save(session)
        self._engines[session.session_id] = self._new_engine(session)
        return self._summary(session)

    def list_sessions(self) -> list[SessionSummary]:
        return [self._summary(session) for session in self.session_store.list_sessions()]

    def get_session(self, session_id: str) -> ChatSession:
        return self.session_store.load(session_id)

    def rename_session(self, session_id: str, title: str) -> SessionSummary:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError(tr("The title cannot be empty."))
        session = self.session_store.load(session_id)
        session.title = cleaned_title
        self.session_store.save(session)
        return self._summary(session)

    def delete_session(self, session_id: str) -> None:
        self.session_store.delete(session_id)
        self._engines.pop(session_id, None)

    def send_message(self, session_id: str, content: str) -> MessageResult:
        prompt = content.strip()
        if not prompt:
            raise ValueError(tr("The message cannot be empty."))
        with self._lock(session_id):
            engine = self._engine_for(session_id)
            response = engine.respond(prompt)
            return self._result(session_id, prompt, response, engine)

    def pending_confirmation(self, session_id: str) -> dict[str, Any] | None:
        """The tool waiting for the user in this chat, if any."""
        engine = self._engines.get(session_id)
        pending = engine.executor.pending if engine is not None else None
        return None if pending is None else {"tool": pending[0], "arguments": dict(pending[1])}

    def confirm(self, session_id: str, approve: bool) -> MessageResult:
        """Run or cancel the tool this chat is waiting on, and let Arqen finish the turn."""
        with self._lock(session_id):
            engine = self._engines.get(session_id)
            if engine is None or engine.executor.pending is None:
                raise ValueError(tr("Nothing is waiting for confirmation."))
            response = engine.confirm_pending_tool(approve)
            return self._result(session_id, "", response, engine)

    def status(self, session_id: str | None = None) -> ArqenStatus:
        engine = self._engine_for(session_id) if session_id else self._default_engine()
        provider = getattr(engine.provider, "provider_name", "unknown")
        model = getattr(engine.provider, "model", "")
        return ArqenStatus(
            provider=provider,
            model=model,
            voice_enabled=engine.voice_enabled,
            session_id=engine.session.session_id,
        )

    def tool_catalog(self) -> list[dict]:
        return self._default_engine().gateway.catalog()

    def tool_audit(self, limit: int = 100) -> list[dict]:
        return self._default_engine().gateway.audit_entries(limit)

    def tool_policies(self) -> list[dict]:
        return self._default_engine().gateway.policy_view()

    def _result(self, session_id: str, prompt: str, response: str, engine: ConversationEngine) -> MessageResult:
        confirmation = self.pending_confirmation(session_id)
        return MessageResult(
            session_id=session_id,
            user_message=prompt,
            assistant_message=response,
            speakable=engine.last_response_speakable,
            status="needs_confirmation" if confirmation else "ready",
            confirmation=confirmation,
        )

    def _lock(self, session_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(session_id, threading.Lock())

    def _default_engine(self) -> ConversationEngine:
        if self._engines:
            return next(iter(self._engines.values()))
        session = self.session_store.create()
        self._engines[session.session_id] = self._new_engine(session)
        return self._engines[session.session_id]

    def _engine_for(self, session_id: str) -> ConversationEngine:
        if session_id not in self._engines:
            session = self.session_store.load(session_id)
            self._engines[session_id] = self._new_engine(session)
        return self._engines[session_id]

    def _new_engine(self, session: ChatSession) -> ConversationEngine:
        engine = self._engine_factory()
        engine.session_store = self.session_store
        engine.session = session
        engine.messages = list(session.messages)
        return engine

    @staticmethod
    def _summary(session: ChatSession) -> SessionSummary:
        return SessionSummary(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
