import asyncio
import json
import ssl
import hashlib
import urllib.request
from datetime import datetime, timezone
from typing import Any, Tuple

import websockets

from ..models import BackupResult
from .base import BaseProvider
from .registry import provider


@provider("truenas")
class TrueNASProvider(BaseProvider):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        self.host = config["host"]
        self.api_key = config["api_key"]
        self.name = config.get("name", "default")
        self.use_tls = config.get("tls", True)

        self._ws = None
        self._req_id = 0

    def connect(self):
        return

    def disconnect(self):
        return

    def backup(self) -> BackupResult:
        return asyncio.run(self._run())

    async def _run(self) -> BackupResult:

        url = f"{'wss' if self.use_tls else 'ws'}://{self.host}/api/current"
        ssl_ctx = ssl._create_unverified_context() if self.use_tls else None

        async with websockets.connect(url, ssl=ssl_ctx) as ws:
            self._ws = ws

            await self._auth()

            job_id, download_url = await self._create_backup()

            download_url = self._normalize(download_url)
            data = await self._download(download_url)

            h = hashlib.sha256(data).hexdigest()

            return BackupResult(
                provider="truenas",
                name=self.name,
                filename=f"{self.name}-backup.tar",
                metadata_filename=f"{self.name}-metadata.json",
                data=data,
                content_hash=h,
                metadata={
                    "provider": "truenas",
                    "name": self.name,
                    "host": self.host,
                    "size_bytes": len(data),
                    "content_hash": h,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )

    async def _auth(self):
        await self._call("auth.login_with_api_key", [self.api_key])

    async def _create_backup(self) -> Tuple[str, str]:
        """
        Normalize ALL possible TrueNAS response shapes.
        """

        result = await self._call(
            "core.download",
            ["config.save", [{"secretseed": True}], "config.tar"],
        )

        # Case 1: dict response
        if isinstance(result, dict):
            job_id = result.get("job_id", "")
            url = result.get("url") or result.get("download_url")
            if not url:
                raise RuntimeError(f"TrueNAS missing download URL: {result}")
            return job_id, url

        # Case 2: list/tuple response
        if isinstance(result, (list, tuple)):
            if len(result) >= 2:
                return str(result[0]), str(result[1])
            raise RuntimeError(f"Unexpected TrueNAS list response: {result}")

        # Case 3: string response (rare fallback)
        if isinstance(result, str):
            return "", result

        raise RuntimeError(f"Unknown TrueNAS response type: {type(result)}")

    async def _download(self, url: str) -> bytes:
        def fetch():
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            with urllib.request.urlopen(
                req,
                context=ssl._create_unverified_context()
            ) as r:
                return r.read()

        return await asyncio.to_thread(fetch)

    def _normalize(self, url: str) -> str:
        if url.startswith("http"):
            return url

        scheme = "https" if self.use_tls else "http"
        return f"{scheme}://{self.host}{url}"

    async def _call(self, method: str, params=None):
        self._req_id += 1

        await self._ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": method,
            "params": params or [],
        }))

        resp = json.loads(await self._ws.recv())

        if "error" in resp:
            raise RuntimeError(resp["error"])

        return resp["result"]