from dataclasses import dataclass

from app.adapters.clock import SystemClock
from app.core.ports.clock import Clock
from app.settings import Settings


@dataclass
class Container:
    clock: Clock


def build_container(settings: Settings) -> Container:
    return Container(clock=SystemClock())
