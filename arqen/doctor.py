import json
from urllib.error import URLError
from urllib.request import urlopen

from arqen.config.settings import load_provider_config


def check_local_provider(base_url: str) -> tuple[bool, str]:
    try:
        with urlopen(f"{base_url.rstrip('/')}/models", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [item.get("id", "unknown") for item in payload.get("data", [])]
        model_text = ", ".join(models) if models else "no models reported"
        return True, f"Provider responds. Models: {model_text}"
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return False, f"Provider does not respond: {exc}"


def main() -> None:
    config = load_provider_config()
    print(f"Provider: {config.name}")
    if config.name != "local":
        print("The check is for a local provider (Ollama or LM Studio); skipped.")
        return
    ok, message = check_local_provider(config.base_url)
    print(message)
    if not ok:
        print(f"Expected model: {config.model}")


if __name__ == "__main__":
    main()

