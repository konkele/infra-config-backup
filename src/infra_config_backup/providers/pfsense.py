import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import BackupResult
from .base import BaseProvider
from .registry import provider

log = logging.getLogger(__name__)


@provider("pfsense")
class PfSenseProvider(BaseProvider):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        self.host = config["host"]
        self.username = config["username"]
        self.password = config["password"]
        self.name = config.get("name", "pfsense")

        self.verify_ssl = config.get("tls", True)
        self.keep_rrd = config.get("keep_rrd", False)

        self.session = requests.Session()
        self.session.mount(
            "https://",
            HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5))
        )

    def connect(self):
        log.info("%s pfSense ready", self.name)

    def disconnect(self):
        self.session.close()

    def backup(self) -> BackupResult:

        url = f"https://{self.host}/diag_backup.php"

        r = self.session.get(url, verify=self.verify_ssl, timeout=15)
        r.raise_for_status()

        csrf = self._extract_csrf(r.text)

        # login step
        r = self.session.post(
            url,
            data={
                "login": "Login",
                "usernamefld": self.username,
                "passwordfld": self.password,
                "__csrf_magic": csrf,
            },
            verify=self.verify_ssl,
            timeout=15,
        )
        r.raise_for_status()

        csrf = self._extract_csrf(r.text)

        # download backup
        r = self.session.post(
            url,
            data={
                "download": "download",
                "donotbackuprrd": "yes" if not self.keep_rrd else "no",
                "__csrf_magic": csrf,
            },
            verify=self.verify_ssl,
            timeout=60,
        )
        r.raise_for_status()

        data = r.content
        h = hashlib.sha256(data).hexdigest()

        return BackupResult(
            provider="pfsense",
            name=self.name,
            filename=f"{self.name}-backup.xml",
            metadata_filename=f"{self.name}-metadata.json",
            data=data,
            content_hash=h,
            metadata={
                "provider": "pfsense",
                "name": self.name,
                "host": self.host,
                "size_bytes": len(data),
                "content_hash": h,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _extract_csrf(self, html: str) -> str:
        match = re.search(
            r"name='__csrf_magic'\s+value=\"([^\"]+)\"",
            html
        )
        if not match:
            raise RuntimeError("CSRF extraction failed")
        return match.group(1)