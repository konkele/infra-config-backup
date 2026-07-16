from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BackupResult:
    """
    Immutable representation of a provider backup.

    Providers return a BackupResult to the execution engine after a
    successful backup. The engine is responsible for persisting the
    artifacts and committing them to Git.

    Attributes:
        provider:
            Provider type (for example: "pfsense" or "truenas").

        name:
            Provider instance name from the configuration.

        filename:
            Relative filename used to store the backup artifact.

        metadata_filename:
            Relative filename used to store the metadata document.

        data:
            Raw backup contents.

        metadata:
            Additional metadata describing the backup.

        content_hash:
            SHA-256 hash of the backup contents.
    """

    provider: str
    name: str

    filename: str
    metadata_filename: str

    data: bytes
    metadata: dict[str, Any]

    content_hash: str

    @property
    def size_bytes(self) -> int:
        """
        Size of the backup payload in bytes.

        This avoids repeatedly calling len(result.data) throughout the
        application and provides a single place for future enhancements
        (compressed size, streamed data, etc.).
        """
        return len(self.data)