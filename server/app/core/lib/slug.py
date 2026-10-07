import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    slug = _NON_ALNUM.sub("-", title.lower()).strip("-")
    return slug or "untitled"
