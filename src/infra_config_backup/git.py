import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .config import GitConfig
from .models import BackupResult


class GitError(RuntimeError):
    pass


class GitRepo:
    def __init__(self, config: GitConfig):
        self._config = config
        self.path: Optional[Path] = None
        self._workspace: Optional[tempfile.TemporaryDirectory] = None

    def clone(self) -> None:
        if self.path is not None:
            raise GitError("already cloned")

        self._workspace = tempfile.TemporaryDirectory(
            prefix="infra-config-backup-"
        )
        self.path = Path(self._workspace.name)

        try:
            self._run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    self._config.branch,
                    self._config.repo,
                    str(self.path),
                ],
                cwd=None,
            )

            self._configure_identity()

        except Exception:
            self.cleanup()
            raise

    def cleanup(self) -> None:
        self.path = None

        if self._workspace:
            self._workspace.cleanup()
            self._workspace = None

    def write_file(self, relative_path: str, data: bytes) -> bool:
        repo = self._require_repo()

        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)

        previous = path.read_bytes() if path.exists() else None

        if previous == data:
            return False

        path.write_bytes(data)
        return True

    def write_json(self, relative_path: str, obj: dict) -> bool:
        return self.write_file(
            relative_path,
            json.dumps(obj, indent=2).encode(),
        )

    def persist_result(
        self,
        provider_type: str,
        name: str,
        result: BackupResult,
        dry_run: bool,
    ) -> bool:
        if dry_run:
            return False

        backup_path = f"{provider_type}/{result.filename}"
        meta_path = f"{provider_type}/{result.metadata_filename}"

        changed = self.write_file(backup_path, result.data)

        if changed:
            self.write_json(meta_path, result.metadata)

        return changed

    def commit_and_push(self, message: str) -> bool:
        repo = self._require_repo()

        self._run(["git", "add", "-A"], cwd=repo)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
            env=self._git_env(),
        )

        if not status.stdout.strip():
            return False

        self._run(["git", "commit", "-m", message], cwd=repo)
        self._run(["git", "push"], cwd=repo)

        return True

    def _configure_identity(self) -> None:
        repo = self._require_repo()
        author = self._config.author

        if author.get("name"):
            self._run(
                ["git", "config", "user.name", author["name"]],
                cwd=repo,
            )

        if author.get("email"):
            self._run(
                ["git", "config", "user.email", author["email"]],
                cwd=repo,
            )

    def _require_repo(self) -> Path:
        if not self.path:
            raise GitError("not cloned")

        return self.path

    def _git_env(self) -> dict[str, str]:
        """
        Build the environment for git commands.

        If an SSH key is configured, use it via GIT_SSH_COMMAND.
        Otherwise, fall back to the normal SSH configuration.
        """
        env = os.environ.copy()

        ssh_key = self._config.ssh.key
        known_hosts = self._config.ssh.known_hosts

        if not ssh_key:
            return env

        cmd = [
            "ssh",
            "-i",
            ssh_key,
            "-o",
            "IdentitiesOnly=yes",
        ]

        if known_hosts:
            cmd.extend(
                [
                    "-o",
                    "StrictHostKeyChecking=yes",
                    "-o",
                    f"UserKnownHostsFile={known_hosts}",
                ]
            )

        env["GIT_SSH_COMMAND"] = " ".join(cmd)

        return env

    def _run(self, cmd: list[str], cwd: Optional[Path]) -> None:
        try:
            subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                env=self._git_env(),
            )
        except subprocess.CalledProcessError as e:
            raise GitError(
                e.stderr or e.stdout or "git error"
            ) from e

    def __enter__(self):
        self.clone()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()
