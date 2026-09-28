import argparse
import os

from arqen.application.service import ArqenApplication
from arqen.config.settings import load_language, load_provider_config
from arqen.core.chat_tools import apply_chat_tool_limits
from arqen.core.engine import ConversationEngine
from arqen.providers.factory import create_provider
from arqen.tools.builtins import create_builtin_registry
from arqen.api.server import create_server
from arqen.ui.strings import set_language


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Arqen's local API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default=os.environ.get("ARQEN_API_TOKEN", ""))
    args = parser.parse_args()

    set_language(load_language())
    config = load_provider_config()

    def engine_factory() -> ConversationEngine:
        # API conversations are chats: they follow the chat's tool selection.
        engine = ConversationEngine(
            provider=create_provider(config),
            tools=create_builtin_registry(),
        )
        apply_chat_tool_limits(engine)
        return engine

    application = ArqenApplication(engine_factory)
    server = create_server(application, host=args.host, port=args.port, token=args.token)
    print(f"Arqen API running at http://{args.host}:{server.server_port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
