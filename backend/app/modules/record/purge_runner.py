"""CLI entrypoint for Record purge (GDPR retention).

Usage:
    python -m app.modules.record.purge_runner [--dry-run] [--retention-days N]

This is a standalone CLI tool - not part of the API.
Purge should be run explicitly (cron, manual, etc) - never per request.
"""
import argparse
import sys
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.modules.record.purge import purge_expired_records


def main() -> int:
    """CLI entrypoint for purge.
    
    Returns:
        0 on success, 1 on error
    """
    parser = argparse.ArgumentParser(
        description="Purge expired records (GDPR retention policy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default: uses RECORDER_PURGE_DRY_RUN env var)
  python -m app.modules.record.purge_runner --dry-run
  
  # Actual purge
  python -m app.modules.record.purge_runner
  
  # Override retention days
  python -m app.modules.record.purge_runner --retention-days 7
  
  # Dry run with custom retention
  python -m app.modules.record.purge_runner --dry-run --retention-days 30
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log what would be purged (default: use RECORDER_PURGE_DRY_RUN env var)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        help=f"Override retention days (default: {settings.recorder_retention_days} from RECORDER_RETENTION_DAYS)",
    )
    
    args = parser.parse_args()
    
    # Determine dry_run mode
    dry_run: Optional[bool] = None
    if args.dry_run:
        dry_run = True
    
    # Override retention days if provided (pass to purge function)
    retention_override = args.retention_days
    
    try:
        effective_retention = retention_override or settings.recorder_retention_days
        effective_dry_run = dry_run if dry_run is not None else settings.recorder_purge_dry_run
        
        logger.info("purge_run_started", extra={
            "dry_run": effective_dry_run,
            "retention_days": effective_retention,
        })
        
        result = purge_expired_records(dry_run=dry_run, retention_days=retention_override)
        
        # Print summary to stdout (for cron logs, etc)
        print(f"Purge complete:")
        print(f"  Dry run: {result['dry_run']}")
        print(f"  Retention days: {result['retention_days']}")
        print(f"  Purged records: {result['purged_count']}")
        print(f"  Files deleted: {result['files_deleted']}")
        print(f"  Exports deleted: {result['exports_deleted']}")
        print(f"  Errors: {result['errors']}")
        
        # Return non-zero if there were errors (but don't fail the process)
        if result["errors"] > 0:
            logger.warning("purge_run_complete_with_errors", extra={
                "errors": result["errors"],
            })
            return 1
        
        logger.info("purge_run_complete", extra={
            "purged_count": result["purged_count"],
            "files_deleted": result["files_deleted"],
            "exports_deleted": result["exports_deleted"],
        })
        return 0
    
    except KeyboardInterrupt:
        logger.warning("purge_run_interrupted")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        error_type = type(e).__name__
        logger.error("purge_run_failed", extra={"error_type": error_type})
        print(f"Error: {error_type}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

