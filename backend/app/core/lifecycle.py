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
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger


async def startup() -> None:
    """Application startup hook."""
    logger.info("app_startup", extra={"version": settings.app_version})

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

