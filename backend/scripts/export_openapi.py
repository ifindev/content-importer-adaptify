import json
from pathlib import Path

from app.api.main import app


def main() -> None:
    schema = app.openapi()
    output_path = Path(__file__).resolve().parents[2] / "web/lib/api/openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
