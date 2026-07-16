from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra_config_backup.models import BackupResult


class BaseProvider(ABC):
    def __init__(self, config: dict):
        self.config = config

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()

    def connect(self) -> None:
        pass

    @abstractmethod
    def backup(self) -> "BackupResult":
        pass

    def disconnect(self) -> None:
        pass