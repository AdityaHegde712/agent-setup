import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_MODELS_URL: str = "https://opencode.ai/zen/v1/models"


def extract_free_model_ids(raw_data: Any) -> list[str]:
    entries: list[dict[str, Any]] = []

    if isinstance(raw_data, dict):
        entries = raw_data.get("data", []) or raw_data.get("models", [])

    if isinstance(raw_data, list):
        entries = raw_data

    free_model_ids: list[str] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        model_id: str = str(entry.get("id", ""))
        is_free_model: bool = "free" in model_id.lower()

        if is_free_model:
            free_model_ids.append(model_id)

    return free_model_ids


def fetch_free_models(url: str = DEFAULT_MODELS_URL) -> list[str]:
    request: urllib.request.Request = urllib.request.Request(
        url,
        headers={"User-Agent": "OpenCode-Client/1.0", "Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_bytes: bytes = response.read()
            parsed_json: Any = json.loads(response_bytes.decode("utf-8"))
            return extract_free_model_ids(parsed_json)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as error:
        print(f"Error fetching models from {url}: {error}")
        return []


def main() -> None:
    free_models: list[str] = fetch_free_models()

    if not free_models:
        print("No free models available or request failed.")
        return

    print("Available Free Models:")
    for model_id in free_models:
        print(f"  - {model_id}")


if __name__ == "__main__":
    main()
