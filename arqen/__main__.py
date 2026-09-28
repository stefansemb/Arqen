from .core.engine import ConversationEngine
from .core.chat_tools import apply_chat_tool_limits
from .config.settings import load_language, load_provider_config, load_workspace_root
from .providers.factory import create_provider
from .tools.builtins import create_builtin_registry
from .ui.strings import set_language, tr


def main() -> None:
    try:
        load_workspace_root()
        set_language(load_language())
        config = load_provider_config()
        provider = create_provider(config)
    except ValueError as exc:
        print(tr("Configuration error: {error}", error=exc))
        return
    engine = ConversationEngine(
        provider=provider,
        tools=create_builtin_registry(),
    )
    apply_chat_tool_limits(engine)
    print(f"Provider: {config.name} ({config.model})")
    print(tr("Arqen Desktop demo. Type 'quit' to exit."))
    while True:
        prompt = input(tr("You") + ": ").strip()
        if prompt.lower() in {"quit", "exit", "avsluta"}:
            break
        if prompt:
            try:
                print(f"Arqen: {engine.respond(prompt)}")
            except RuntimeError as exc:
                print(tr("Arqen could not answer: {error}", error=exc))


if __name__ == "__main__":
    main()
