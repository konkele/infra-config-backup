import logging
import json

from .config import AppConfig, ConfigurationError
from .git import GitRepo
from .providers.registry import get_provider

log = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repo = GitRepo(config.git)

    def run(self) -> None:
        log.info("event=engine_run_start")

        self.repo.clone()

        any_changes = False
        failed_providers = []

        try:
            for p in self.config.providers:
                if "type" not in p:
                    raise ConfigurationError("Provider missing 'type'")

                provider_type = p["type"]
                provider_name = p.get("name") or provider_type
                raw = p

                effective_dry_run = self.config.dry_run or bool(raw.get("dry_run", False))

                cls = get_provider(provider_type)

                log.info(
                    "event=provider_execute type=%s name=%s",
                    provider_type,
                    provider_name,
                )

                try:
                    # provider isolation block
                    with cls(raw) as instance:
                        result = instance.backup()

                        changed = self.repo.persist_result(
                            provider_type,
                            provider_name,
                            result,
                            effective_dry_run,
                        )

                        any_changes |= changed

                except Exception as e:
                    # failure isolation + tracking
                    log.error(
                        "event=provider_failed type=%s name=%s error=%s",
                        provider_type,
                        provider_name,
                        str(e),
                    )

                    failed_providers.append({
                        "type": provider_type,
                        "name": provider_name,
                        "error": str(e),
                    })

                    continue

            if any_changes:
                self.repo.commit_and_push("Automated infrastructure backup")
                log.info("event=commit status=success")
            else:
                log.info("event=commit_skipped reason=no_changes")

        finally:
            self.repo.cleanup()

            # run summary
            log.info(
                "event=engine_run_complete failed_count=%d success=%d",
                len(failed_providers),
                len(self.config.providers) - len(failed_providers),
            )

            if failed_providers:
                log.info(
                    "event=engine_failed_providers data=%s",
                    failed_providers,
                )

            log.info("event=engine_cleanup_complete")