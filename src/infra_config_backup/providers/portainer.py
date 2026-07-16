import hashlib
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import BackupResult
from .base import BaseProvider
from .registry import provider


@provider("portainer")
class PortainerProvider(BaseProvider):
    """
    Backup Portainer via API snapshot endpoint.
    Requires an API key (recommended) or admin login token.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        self.name = config.get("name", "portainer")
        self.url = config["url"].rstrip("/")

        self.api_key = config.get("api_key")
        self.username = config.get("username")
        self.password = config.get("password")

        self.verify_ssl = config.get("tls", True)
        self.timeout = config.get("timeout", 30)

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._jwt = None

    # -------------------------
    # lifecycle
    # -------------------------
    def connect(self):
        if self.api_key:
            return

        if not self.username or not self.password:
            raise RuntimeError("Portainer requires api_key or username/password")

        # login if using credentials
        r = self.session.post(
            f"{self.url}/api/auth",
            json={
                "Username": self.username,
                "Password": self.password,
            },
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        r.raise_for_status()
        self._jwt = r.json().get("jwt")

        if not self._jwt:
            raise RuntimeError("Failed to obtain Portainer JWT")

    def disconnect(self):
        self.session.close()

    # -------------------------
    # backup
    # -------------------------
    def backup(self) -> BackupResult:
        headers = {}

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self._jwt:
            headers["Authorization"] = f"Bearer {self._jwt}"

        # Portainer backup endpoint (available in CE/BE depending version)
        url = f"{self.url}/api/backup"

        resp = self.session.post(
            url,
            json={
                "includeCredentials": True,
                "excludeStacks": False,
                "excludePlugins": False,
            },
            headers=headers,
            timeout=self.timeout,
            verify=self.verify_ssl,
            stream=True,
        )

        resp.raise_for_status()

        sha256 = hashlib.sha256()
        chunks = []
        total = 0

        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if not chunk:
                continue
            sha256.update(chunk)
            chunks.append(chunk)
            total += len(chunk)

        data = b"".join(chunks)
        content_hash = sha256.hexdigest()

        return BackupResult(
            provider="portainer",
            name=self.name,
            filename=f"{self.name}-backup.tar.gz",
            metadata_filename=f"{self.name}-metadata.json",
            data=data,
            content_hash=content_hash,
            metadata={
                "provider": "portainer",
                "name": self.name,
                "url": self.url,
                "size_bytes": total,
                "content_hash": content_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )