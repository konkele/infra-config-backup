import logging
import os
import sys
from pathlib import Path

from .config import ConfigurationError, load_config
from .engine import ExecutionEngine
from .git import GitError


def resolve_config_path() -> str:
    candidates = (
        os.getenv("CONFIG_FILE"),
        "/config/config.yaml",
        "config/config.yaml",
    )

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    raise FileNotFoundError(
        "config not found; expected CONFIG_FILE, "
        "/config/config.yaml, or config/config.yaml"
    )


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )


def main() -> None:
    setup_logging()
    log = logging.getLogger(__name__)

    try:
        log.info("starting")

        config_path = resolve_config_path()
        log.info("loading config path=%s", config_path)

        config = load_config(config_path)

        log.info(
            "configuration loaded providers=%d dry_run=%s",
            len(config.providers),
            config.dry_run,
        )

        ExecutionEngine(config).run()

        log.info("complete")

    except (ConfigurationError, GitError, FileNotFoundError) as e:
        log.error(str(e))
        sys.exit(1)

    except Exception:
        log.exception("fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
