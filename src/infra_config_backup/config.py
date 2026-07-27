import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GitSSHConfig:
    key: str | None = None
    known_hosts: str | None = None


@dataclass(frozen=True, slots=True)
class GitConfig:
    repo: str
    branch: str
    author: dict[str, str]
    ssh: GitSSHConfig


@dataclass(frozen=True, slots=True)
class AppConfig:
    git: GitConfig
    providers: list[dict[str, Any]]
    dry_run: bool


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as exc:
        raise ConfigurationError(f"Failed loading config: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("Config root must be a mapping")

    raw = _expand_env(raw)

    git = raw.get("git")
    if not isinstance(git, dict):
        raise ConfigurationError("Missing git config")

    repo = git.get("repo")
    if not repo:
        raise ConfigurationError("Missing git.repo")

    author = git.get("author") or {}
    if not isinstance(author, dict):
        raise ConfigurationError("git.author must be a mapping")

    ssh = git.get("ssh") or {}
    if not isinstance(ssh, dict):
        raise ConfigurationError("git.ssh must be a mapping")

    providers = raw.get("providers", [])
    if providers is None:
        providers = []

    if not isinstance(providers, list):
        raise ConfigurationError("providers must be a list")

    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            raise ConfigurationError(
                f"providers[{index}] must be a mapping"
            )

        if not provider.get("type"):
            raise ConfigurationError(
                f"providers[{index}] missing 'type'"
            )

        if provider.get("name") == "":
            raise ConfigurationError(
                f"providers[{index}] has an empty 'name'"
            )

    return AppConfig(
        git=GitConfig(
            repo=repo,
            branch=git.get("branch", "main"),
            author=author,
            ssh=GitSSHConfig(
                key=ssh.get("key"),
                known_hosts=ssh.get("known_hosts"),
            ),
        ),
        providers=providers,
        dry_run=bool(raw.get("dry_run", False)),
    )


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}"):
            variable = value[2:-1]

            result = os.getenv(variable)

            if result is None:
                raise ConfigurationError(
                    f"Environment variable '{variable}' is not set"
                )

            return result

        return value

    if isinstance(value, list):
        return [_expand_env(v) for v in value]

    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}

    return value
