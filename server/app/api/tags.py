HEALTH = "Health"
AUTH = "Auth"
SITES = "Sites"
IMPORT = "Import"
ARTICLES = "Articles"
PUBLISHING = "Publishing"
REVIEW_LINK = "Review link"
CLIENT_REVIEW = "Client review"
REPORT = "Report"

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": HEALTH, "description": "Liveness check."},
    {"name": AUTH, "description": "Exchange a Firebase ID token for a session cookie."},
    {"name": SITES, "description": "Create and list the agency's client sites."},
    {"name": IMPORT, "description": "Create drafts from a .docx upload or pasted HTML."},
    {"name": ARTICLES, "description": "List, read, and edit articles."},
    {"name": PUBLISHING, "description": "Send for review, pull back, schedule, and retry."},
    {"name": REVIEW_LINK, "description": "The agency's client review URL."},
    {"name": REPORT, "description": "Status counts, approval speed, and change rounds."},
    {
        "name": CLIENT_REVIEW,
        "description": (
            "The client's review page. These routes use the review token, not the session cookie."
        ),
    },
]
