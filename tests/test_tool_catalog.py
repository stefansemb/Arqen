import pytest

from arqen.tools.builtins import create_builtin_registry
from arqen.ui import strings
from arqen.ui.tool_catalog import CATEGORIES, tool_info


@pytest.fixture
def language():
    yield strings.set_language
    strings.set_language("sv")


def test_every_builtin_tool_has_display_info():
    """A new tool should get a name and category, not land in "Other"."""
    missing = [
        item["name"]
        for item in create_builtin_registry().describe()
        if tool_info(item["name"]).category == "Other"
    ]
    assert missing == []


def test_every_category_has_a_swedish_name():
    assert [category for category in CATEGORIES if category not in {"System", "Google", "MCP"}
            and strings.tr(category) == category] == []


def test_tool_names_follow_the_ui_language(language):
    assert tool_info("read_pdf").title == "Läs PDF"
    language("en")
    assert (tool_info("read_pdf").category, tool_info("read_pdf").title) == ("Documents", "Read PDF")


def test_unknown_tool_falls_back_to_its_model_description():
    info = tool_info("brand_new_tool", "Does something new.")
    assert (info.category, info.title, info.summary) == ("Other", "brand_new_tool", "Does something new.")
    assert info.category in CATEGORIES
