"""Arqen in English: the model, the chat commands and the voice follow the language."""

import pytest

from arqen.core.contracts import ProviderResponse
from arqen.core.engine import ConversationEngine
from arqen.tools import speech
from arqen.ui import strings


class Recorder:
    def __init__(self):
        self.calls = []

    def respond(self, messages, tools=None):
        self.calls.append(messages)
        return ProviderResponse(content="ok")


@pytest.fixture
def english():
    strings.set_language("en")
    yield
    strings.set_language("sv")


def test_the_model_is_told_to_answer_in_the_ui_language(english):
    provider = Recorder()
    ConversationEngine(provider=provider).respond("hello")
    system = provider.calls[0][0].content
    assert "Answer in English by default" in system
    assert "under Memory" in system


def test_swedish_stays_the_answer_language_in_swedish():
    provider = Recorder()
    ConversationEngine(provider=provider).respond("hej")
    assert "Answer in Swedish by default" in provider.calls[0][0].content


def test_memory_commands_work_in_english(english):
    engine = ConversationEngine(provider=Recorder())
    assert engine.respond("remember that the cat is called Mio") == "Saved to memory: the cat is called Mio"
    assert "the cat is called Mio" in engine.respond("what do you remember?")
    assert engine.respond("forget that the cat is called Mio") == "I have forgotten: the cat is called Mio"


def test_swedish_commands_answer_in_english_when_the_ui_is_english(english):
    engine = ConversationEngine(provider=Recorder())
    assert engine.respond("kom ihåg att katten heter Mio") == "Saved to memory: katten heter Mio"


def test_summarise_only_takes_documents(english):
    # "summarize our plan" is a request for the model, not a missing file type.
    provider = Recorder()
    engine = ConversationEngine(provider=provider)
    assert engine._handle_document_command("summarize our plan") is None
    assert engine._handle_document_command("compare Python and Rust") is None


def test_a_document_can_be_summarised(tmp_path, monkeypatch):
    # This used to fail on every document: the read had ended up unreachable.
    from arqen.tools.builtins import create_builtin_registry

    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.md").write_text("Arqen notes", encoding="utf-8")
    provider = Recorder()
    engine = ConversationEngine(provider=provider, tools=create_builtin_registry())
    assert engine._handle_document_command("sammanfatta notes.md") == "ok"
    assert "Arqen notes" in provider.calls[0][1].content
    assert "in Swedish" in provider.calls[0][0].content


def test_new_chats_get_a_language_neutral_title(english):
    engine = ConversationEngine(provider=Recorder())
    assert engine.session.title == "New chat"
    engine.respond("Plan the week")
    assert engine.session.title == "Plan the week"


def test_degrees_are_read_in_the_ui_language(english):
    assert speech._speak_degrees("It is 13 °C") == "It is 13 degrees Celsius"
    assert speech._speak_degrees("1 °F") == "1 degree Fahrenheit"


def test_degrees_in_swedish():
    assert speech._speak_degrees("Det är 13 °C") == "Det är 13 grader"


def test_the_voice_follows_the_language():
    assert speech.EDGE_VOICES["sv"] == "sv-SE-MattiasNeural"
    assert speech.EDGE_VOICES["en"].startswith("en-")
    assert set(speech.EDGE_VOICES) == set(strings.LANGUAGES)
