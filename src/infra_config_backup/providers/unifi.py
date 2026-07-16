import hashlib
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import BackupResult
from .base import BaseProvider
from .registry import provider


@provider("unifi")
class UnifiProvider(BaseProvider):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        self.name = config.get("name", "unifi")
        self.url = config["url"].rstrip("/")

        self.verify_ssl = config.get("tls", True)
        self.timeout = config.get("timeout", 30)

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry)

        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # -------------------------
    # Lifecycle
    # -------------------------
    def connect(self):
        try:
            r = self.session.get(
                f"{self.url}/readyz",
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Unifi exporter not ready at {self.url}: {e}")

    def disconnect(self):
        self.session.close()

    # -------------------------
    # Backup
    # -------------------------
    def backup(self) -> BackupResult:
        # 1. Metadata (authoritative)
        meta_resp = self.session.get(
            f"{self.url}/metadata",
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        meta_resp.raise_for_status()
        metadata = meta_resp.json()

        # 2. Stream download (DO NOT load into memory blindly)
        resp = self.session.get(
            f"{self.url}/latest",
            timeout=self.timeout,
            verify=self.verify_ssl,
            stream=True,
        )
        resp.raise_for_status()

        sha256 = hashlib.sha256()
        chunks = []

        total_bytes = 0

        for chunk in resp.iter_content(chunk_size=1024 * 512):
            if not chunk:
                continue

            sha256.update(chunk)
            chunks.append(chunk)
            total_bytes += len(chunk)

            # safety guard (prevents runaway memory if exporter misbehaves)
            if total_bytes > 2 * 1024 * 1024 * 1024:  # 2GB guard
                raise RuntimeError("Unifi backup exceeded 2GB limit")

        data = b"".join(chunks)
        content_hash = sha256.hexdigest()

        # 3. Verify integrity (optional)
        expected = metadata.get("sha256")
        if expected and expected != content_hash:
            raise RuntimeError(
                f"Checksum mismatch: expected={expected}, got={content_hash}"
            )

        # FORCE deterministic filename
        filename = f"{self.name}-backup.unf"

        return BackupResult(
            provider="unifi",
            name=self.name,
            filename=filename,
            metadata_filename=f"{self.name}-metadata.json",
            data=data,
            content_hash=content_hash,
            metadata={
                "provider": "unifi",
                "name": self.name,
                "url": self.url,
                "filename": filename,
                "size_bytes": total_bytes,
                "modified": metadata.get("modified"),
                "content_hash": content_hash,
                "exporter_mode": "sidecar",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )