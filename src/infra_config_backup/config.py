import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GitConfig:
    repo: str
    branch: str
    author: dict[str, str]


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

    author = git.get("author") or {}

    return AppConfig(
        git=GitConfig(
            repo=git["repo"],
            branch=git.get("branch", "main"),
            author=author,
        ),
        providers=raw.get("providers", []),
        dry_run=bool(raw.get("dry_run", False)),
    )


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}"):
            return os.getenv(value[2:-1], "")
        return value

    if isinstance(value, list):
        return [_expand_env(v) for v in value]

    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}

    return value