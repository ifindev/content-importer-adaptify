from dataclasses import dataclass

from app.adapters.clock import SystemClock
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher
from app.settings import Settings


@dataclass
class Container:
    clock: Clock
    publisher: Publisher


def build_container(settings: Settings) -> Container:
    return Container(
        clock=SystemClock(),
        publisher=WordPressPublisher(
            base_url=settings.wp_base_url,
            username=settings.wp_username,
            app_password=settings.wp_app_password,
        ),
    )
