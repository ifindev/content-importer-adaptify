from app.api.main import app
from app.api.tags import OPENAPI_TAGS

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

EXPECTED_OPERATIONS = {
    "Health": ["GET /health"],
    "Auth": ["POST /auth/session"],
    "Sites": [
        "GET /sites",
        "POST /sites",
        "POST /sites/test-connection",
        "POST /sites/{site_id}/test-connection",
    ],
    "Import": [
        "POST /sites/{site_id}/articles/upload",
        "POST /sites/{site_id}/articles/paste",
    ],
    "Articles": [
        "GET /sites/{site_id}/articles",
        "GET /sites/{site_id}/articles/{article_id}",
        "PATCH /sites/{site_id}/articles/{article_id}",
    ],
    "Publishing": [
        "POST /sites/{site_id}/articles/{article_id}/send-for-review",
        "POST /sites/{site_id}/articles/{article_id}/pull-back",
        "POST /sites/{site_id}/articles/{article_id}/schedule",
        "POST /sites/{site_id}/articles/{article_id}/retry",
    ],
    "Review link": [
        "GET /sites/{site_id}/review-link",
        "POST /sites/{site_id}/review-link/reset",
    ],
    "Report": ["GET /sites/{site_id}/report"],
    "Client review": [
        "GET /review/{token}",
        "GET /review/{token}/articles/{article_id}",
        "POST /review/{token}/articles/{article_id}/approve",
        "POST /review/{token}/articles/{article_id}/request-changes",
    ],
}


def test_openapi_sections_follow_the_workflow() -> None:
    schema = app.openapi()
    assert [tag["name"] for tag in schema["tags"]] == [tag["name"] for tag in OPENAPI_TAGS]

    grouped: dict[str, list[str]] = {tag["name"]: [] for tag in schema["tags"]}
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            assert operation["tags"], f"{method.upper()} {path} has no section"
            for tag in operation["tags"]:
                grouped[tag].append(f"{method.upper()} {path}")

    assert grouped == EXPECTED_OPERATIONS
