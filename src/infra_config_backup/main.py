import logging
import os
import sys
from pathlib import Path

from .config import load_config, ConfigurationError
from .engine import ExecutionEngine
from .git import GitError


def resolve_config_path():
    for candidate in (
        os.getenv("CONFIG_FILE"),
        "config/config.yaml",
        "/config/config.yaml",
    ):
        if candidate and Path(candidate).is_file():
            return candidate

    raise FileNotFoundError("config not found")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )


def main():
    setup_logging()
    log = logging.getLogger(__name__)

    try:
        log.info("starting")

        config = load_config(resolve_config_path())

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