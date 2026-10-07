from dataclasses import dataclass
from datetime import datetime
from typing import Literal

PostStatusValue = Literal["publish", "future", "draft", "private"]


@dataclass(frozen=True)
class PostStatus:
    id: int
    status: PostStatusValue
    link: str | None
    date_gmt: datetime | None
