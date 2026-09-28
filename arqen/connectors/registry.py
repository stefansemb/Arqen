from __future__ import annotations

from arqen.connectors.base import Connector
from arqen.tools.registry import ToolRegistry
from arqen.ui.strings import tr
from arqen.ui.tool_catalog import CATEGORIES, tool_info

# What each built-in group is for, in the words shown on its card.
# The badge letters stay as they were in Swedish, so the cards look the same.
_BUILTIN = {
    "System": ("system", "The computer's status, time, resources and processes.", "S"),
    "Windows & programs": ("windows", "See, focus, start and close programs and windows.", "F"),
    "Workspace files": ("files", "List, search, read and change files in the workspace.", "A"),
    "Documents": ("documents", "Read PDF, Word and Excel files.", "D"),
    "Web": ("web", "Search the web, fetch pages, tech news, release notes and weather.", "W"),
    "Browser": ("browser", "Control Arqen's own browser: go to, read, click.", "B"),
    "Voice & image": ("voice-image", "Read text aloud and create images.", "R"),
    "Memory": ("memory", "Propose things to remember; you approve them.", "M"),
}


def builtin_connectors(tools: ToolRegistry) -> list[Connector]:
    """The built-in tool groups as connectors, one per catalogue category."""
    grouped: dict[str, list[str]] = {}
    for entry in tools.describe():
        tool = tools.get(entry["name"])
        if tool is not None and tool.connector_id:
            continue  # belongs to its own connection card, not a built-in group
        grouped.setdefault(tool_info(entry["name"]).category, []).append(entry["name"])
    connectors = []
    for category in CATEGORIES:
        names = grouped.get(category)
        if not names:
            continue
        identifier, description, icon = _BUILTIN.get(
            category, (category.casefold(), "Tools without a group of their own.", category[:1])
        )
        connectors.append(Connector(
            id=f"builtin:{identifier}",
            name=tr(category),
            category="Built-in",
            description=tr(description),
            tools=tuple(names),
            icon=icon,
        ))
    return connectors


def all_connectors(tools: ToolRegistry) -> list[Connector]:
    """Every connector Arqen knows about, built-in first."""
    from arqen.connectors.external import EXTERNAL
    from arqen.connectors.mcp import mcp_connectors

    return builtin_connectors(tools) + list(EXTERNAL) + mcp_connectors()
