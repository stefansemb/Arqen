"""How the Tools view presents each tool: category, name and summary.

The tool's own description is written for the model and stays in English;
this table is only for people reading the catalogue, in English and Swedish
side by side.  Categories are English keys, shown through ``tr``.  A tool
that is missing here still shows up, under "Other" with its model description.
"""

from __future__ import annotations

from dataclasses import dataclass

from arqen.ui import strings

# Display order of the catalogue sections.  Show them with ``tr(category)``.
CATEGORIES = (
    "System",
    "Windows & programs",
    "Workspace files",
    "Documents",
    "Web",
    "Browser",
    "Voice & image",
    "Memory",
    "Development",
    "Google",
    "Messages",
    "MCP",
    "Other",
)


@dataclass(frozen=True)
class ToolInfo:
    category: str
    title: str
    summary: str


# name: (category, (English title, summary), (Swedish title, summary))
_TOOLS: dict[str, tuple[str, tuple[str, str], tuple[str, str]]] = {
    "system_status": ("System", ("System status", "Operating system and Python environment."), ("Systemstatus", "Operativsystem och Python-miljö.")),
    "current_time": ("System", ("Current time", "Today's date and time."), ("Aktuell tid", "Dagens datum och klockslag.")),
    "system_resources": ("System", ("Resources", "Processor and memory use right now."), ("Resurser", "Processor- och minnesanvändning just nu.")),
    "running_processes": ("System", ("Processes", "The processes using the most processor."), ("Processer", "De processer som använder mest processor.")),
    "active_window": ("Windows & programs", ("Active window", "Title and process of the window in focus."), ("Aktivt fönster", "Titel och process för fönstret i fokus.")),
    "open_windows": ("Windows & programs", ("Open windows", "Lists visible windows."), ("Öppna fönster", "Listar synliga fönster.")),
    "focus_window": ("Windows & programs", ("Focus window", "Brings a window forward by title."), ("Fokusera fönster", "Tar fram ett fönster efter titel.")),
    "launch_path": ("Windows & programs", ("Open file or folder", "Opens with the Windows default program."), ("Öppna fil eller mapp", "Öppnar med Windows standardprogram.")),
    "launch_program": ("Windows & programs", ("Start program", "Starts an installed program."), ("Starta program", "Startar ett installerat program.")),
    "installed_programs": ("Windows & programs", ("Installed programs", "Lists programs from the registry."), ("Installerade program", "Listar program från registret.")),
    "close_program": ("Windows & programs", ("Close program", "Ends a process by PID or name."), ("Stäng program", "Avslutar en process via PID eller namn.")),
    "workspace_files": ("Workspace files", ("List files", "Files and sizes in the workspace root."), ("Lista filer", "Filer och storlekar i arbetsytans rot.")),
    "search_workspace_files": ("Workspace files", ("Search file names", "Searches file names in the whole workspace."), ("Sök filnamn", "Söker filnamn i hela arbetsytan.")),
    "search_workspace_content": ("Workspace files", ("Search contents", "Searches text in the files."), ("Sök i innehåll", "Söker text i filerna.")),
    "read_workspace_file": ("Workspace files", ("Read file", "Reads a text file."), ("Läs fil", "Läser en textfil.")),
    "write_workspace_file": ("Workspace files", ("Write file", "Creates or overwrites a text file."), ("Skriv fil", "Skapar eller skriver över en textfil.")),
    "delete_workspace_file": ("Workspace files", ("Delete file", "Deletes a file."), ("Ta bort fil", "Tar bort en fil.")),
    "move_workspace_file": ("Workspace files", ("Move file", "Moves or renames a file."), ("Flytta fil", "Flyttar eller byter namn på en fil.")),
    "undo_workspace_file_change": ("Workspace files", ("Undo file change", "Restores the latest change."), ("Ångra filändring", "Återställer den senaste ändringen.")),
    "read_pdf": ("Documents", ("Read PDF", "Extracts the text from a PDF."), ("Läs PDF", "Hämtar texten ur en PDF.")),
    "read_docx": ("Documents", ("Read Word", "Extracts the text from a DOCX file."), ("Läs Word", "Hämtar texten ur en DOCX-fil.")),
    "read_xlsx": ("Documents", ("Read Excel", "Sheets and cells from an XLSX file."), ("Läs Excel", "Blad och celler ur en XLSX-fil.")),
    "search_web": ("Web", ("Search the web", "Short list of search results."), ("Sök på webben", "Kort lista med sökträffar.")),
    "fetch_webpage": ("Web", ("Fetch web page", "Title and readable text from a page."), ("Hämta webbsida", "Titel och läsbar text från en sida.")),
    "open_webpage": ("Web", ("Open in browser", "Opens an address in your browser."), ("Öppna i webbläsare", "Öppnar en adress i din webbläsare.")),
    "search_tech_news": ("Web", ("Search tech news", "Hacker News, Reddit and GitHub in one call."), ("Sök tekniknyheter", "Hacker News, Reddit och GitHub i ett anrop.")),
    "github_release_notes": ("Web", ("Release notes", "Official release news for a GitHub project."), ("Release notes", "Officiella versionsnyheter för ett GitHub-projekt.")),
    "weather_forecast": ("Web", ("Weather forecast", "Evening forecast for Gothenburg."), ("Väderprognos", "Kvällsprognos för Göteborg.")),
    "browser_navigate": ("Browser", ("Go to address", "Arqen's browser opens an address."), ("Gå till adress", "Arqens webbläsare öppnar en adress.")),
    "browser_read_page": ("Browser", ("Read page", "Title and visible text on the page."), ("Läs sida", "Titel och synlig text på sidan.")),
    "browser_list_links": ("Browser", ("List links", "The links on the page."), ("Lista länkar", "Länkarna på sidan.")),
    "browser_click_link": ("Browser", ("Click link", "Clicks a link by its text."), ("Klicka länk", "Klickar på en länk efter text.")),
    "browser_back": ("Browser", ("Back", "Goes back one page."), ("Bakåt", "Går tillbaka en sida.")),
    "browser_forward": ("Browser", ("Forward", "Goes forward one page."), ("Framåt", "Går fram en sida.")),
    "speak_text": ("Voice & image", ("Read aloud", "Reads text aloud with the voice."), ("Läs upp", "Läser upp text med rösten.")),
    "stop_speech": ("Voice & image", ("Stop reading", "Stops the current reading."), ("Stoppa uppläsning", "Avbryter pågående uppläsning.")),
    "generate_image": ("Voice & image", ("Create image", "Generates an image via OpenRouter. Costs money."), ("Skapa bild", "Genererar en bild via OpenRouter. Kostar pengar.")),
    "propose_memory": ("Memory", ("Propose memory", "Suggests something to remember. You approve it under Memory."), ("Föreslå minne", "Föreslår något att minnas. Du godkänner det under Minne.")),
    "github_list_repos": ("Development", ("GitHub: list repos", "Your repos, most recently changed first."), ("GitHub: lista repon", "Dina repon, senast ändrade först.")),
    "github_list_issues": ("Development", ("GitHub: list issues", "Open issues in a repo."), ("GitHub: lista issues", "Öppna issues i ett repo.")),
    "github_read_issue": ("Development", ("GitHub: read issue", "Title, state, labels and text."), ("GitHub: läs issue", "Titel, status, etiketter och text.")),
    "github_list_pull_requests": ("Development", ("GitHub: list pull requests", "Open pull requests in a repo."), ("GitHub: lista pull requests", "Öppna pull requests i ett repo.")),
    "github_create_issue": ("Development", ("GitHub: create issue", "Creates a new issue in a repo."), ("GitHub: skapa issue", "Skapar en ny issue i ett repo.")),
    "gmail_search_messages": ("Google", ("Gmail: search mail", "Searches your Gmail and lists the hits."), ("Gmail: sök mejl", "Söker i din Gmail och listar träffar.")),
    "gmail_read_message": ("Google", ("Gmail: read mail", "Sender, subject, text and attachments."), ("Gmail: läs mejl", "Avsändare, ämne, text och bilagor.")),
    "gmail_create_draft": ("Google", ("Gmail: create draft", "Saves a mail draft. Nothing is sent."), ("Gmail: skapa utkast", "Sparar ett mejlutkast. Inget skickas.")),
    "calendar_list_events": ("Google", ("Calendar: upcoming", "Events in your calendar over the next few days."), ("Kalender: kommande", "Händelser i din kalender de närmaste dagarna.")),
    "calendar_create_event": ("Google", ("Calendar: create event", "Adds an event to your calendar."), ("Kalender: skapa händelse", "Lägger in en händelse i din kalender.")),
    "drive_search_files": ("Google", ("Drive: search files", "Searches files by name and content."), ("Drive: sök filer", "Söker filer på namn och innehåll.")),
    "drive_read_file": ("Google", ("Drive: read file", "The text of Docs, Sheets, Slides and text files."), ("Drive: läs fil", "Texten ur Docs, Kalkylark, Presentationer och textfiler.")),
    "discord_send_message": ("Messages", ("Discord: send", "Sends a message to your channel."), ("Discord: skicka", "Skickar ett meddelande till din kanal.")),
    "telegram_send_message": ("Messages", ("Telegram: send", "Sends a message through your bot."), ("Telegram: skicka", "Skickar ett meddelande via din bot.")),
}


def tool_info(name: str, model_description: str = "") -> ToolInfo:
    """The display info for ``name`` in the UI language, falling back to its model description."""
    if name in _TOOLS:
        category, english, swedish = _TOOLS[name]
        title, summary = swedish if strings.LANGUAGE == "sv" else english
        return ToolInfo(category, title, summary)
    if name.startswith("mcp_"):
        # MCP tools come from the user's servers; show the server's own name.
        from arqen.connectors.mcp import display_title

        return ToolInfo("MCP", display_title(name) or name, model_description)
    return ToolInfo("Other", name, model_description)
