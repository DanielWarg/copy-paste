"""Lifecycle startup/shutdown hooks.

Startup order (CRITICAL):
1. Config loaded (already done at import)
2. Logging initialized
3. Database initialized (if DATABASE_URL exists)
4. Migrations run (if DB exists)
5. Routers registered
6. App ready

This order ensures:
- Config errors fail fast (before logging)
- Logging available for DB init
- DB ready before /ready endpoint
"""
import subprocess
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger


async def startup() -> None:
    """Application startup hook with prod_brutal profile checks."""
    logger.info("app_startup", extra={"version": settings.app_version})
    
    # Prod_brutal profile: Fail-closed checks
    profile = os.getenv("PROFILE", "").lower()
    environment = os.getenv("ENVIRONMENT", "").lower()
    
    if profile == "prod_brutal" or (environment == "production" and profile == "prod_brutal"):
        # Check that cloud API keys are NOT set (fail-closed)
        cloud_keys = [
            ("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")),
            ("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY")),
            ("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY")),
        ]
        
        for key_name, key_value in cloud_keys:
            if key_value:
                logger.error(
                    "startup_cloud_key_blocked",
                    extra={
                        "error_type": "ConfigurationError",
                        "policy_code": "prod_brutal_no_cloud_keys",
                        "key_name": key_name
                    }
                )
                print(f"ERROR: {key_name} found in prod_brutal profile - external egress is blocked", file=sys.stderr)
                sys.exit(1)
        
        logger.info("startup_prod_brutal_checks_passed", extra={"profile": "prod_brutal"})

    # Initialize database if DATABASE_URL is set
    if settings.database_url:
        logger.info("db_init_start", extra={"database_url": "***"})
        try:
            init_db(settings.database_url)
            # Verify init succeeded
            from app.core.database import engine
            if engine is None:
                logger.error("db_init_failed", extra={"error": "init_db returned but engine is None"})
            else:
                logger.info("db_init_complete")
                
                # Run Alembic migrations only if init succeeded
                try:
                    # alembic.ini is in backend/ directory (same level as app/)
                    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
                    command.upgrade(alembic_cfg, "head")
                    logger.info("db_migrations_complete")
                except Exception as e:
                    logger.error("db_migration_failed", extra={"error_type": type(e).__name__})
                    # Don't fail startup - migrations might be run manually
        except Exception as e:
            logger.error("db_init_failed", extra={"error_type": type(e).__name__})
            # Don't fail startup - DB might be unavailable
    else:
        logger.info("db_not_configured")

    logger.info("app_startup_complete")


async def shutdown() -> None:
    """Application shutdown hook."""
    logger.info("app_shutdown_start")

    # Close database connections
    from app.core.database import engine

    if engine:
        engine.dispose()
        logger.info("db_connections_closed")

    logger.info("app_shutdown_complete")

