"""
Celery Tasks for Booking Sync
Auto-syncs booking requests from Google Sheets every 5 minutes
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_booking_requests():
    """
    Sync booking requests from Google Sheets for all agencies
    Runs every 5 minutes via Celery Beat
    """
    from monitors.models import Agency
    from services.booking_sync_service import BookingSyncService
    
    logger.info("Starting booking requests sync for all agencies")
    
    service = BookingSyncService()
    
    # Get all active agencies with Google Sheets configured
    agencies = Agency.objects.filter(
        is_active=True,
        google_sheet_url__isnull=False
    ).exclude(google_sheet_url='')
    
    total_created = 0
    total_skipped = 0
    success_count = 0
    error_count = 0
    
    for agency in agencies:
        try:
            logger.info(f"Syncing booking requests for agency {agency.id} ({agency.name})")
            
            result = service.sync_booking_requests(agency.id)
            
            if result['success']:
                created = result.get('created', 0)
                skipped = result.get('skipped', 0)
                total_created += created
                total_skipped += skipped
                success_count += 1
                
                if created > 0:
                    logger.info(f"Agency {agency.id}: Created {created} tasks, skipped {skipped}")
                else:
                    logger.debug(f"Agency {agency.id}: No new tasks, skipped {skipped}")
            else:
                error_count += 1
                logger.error(f"Agency {agency.id}: Sync failed - {result.get('error')}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error syncing agency {agency.id}: {e}", exc_info=True)
    
    logger.info(
        f"Booking sync complete: {success_count} agencies synced, "
        f"{total_created} tasks created, {total_skipped} skipped, "
        f"{error_count} errors"
    )
    
    return {
        'success': True,
        'agencies_synced': success_count,
        'total_created': total_created,
        'total_skipped': total_skipped,
        'errors': error_count
    }


@shared_task
def sync_booking_requests_for_agency(agency_id):
    """
    Sync booking requests for a specific agency
    Can be called manually or via API
    """
    from services.booking_sync_service import BookingSyncService
    
    logger.info(f"Syncing booking requests for agency {agency_id}")
    
    service = BookingSyncService()
    result = service.sync_booking_requests(agency_id)
    
    if result['success']:
        logger.info(
            f"Agency {agency_id}: Created {result.get('created', 0)} tasks, "
            f"skipped {result.get('skipped', 0)}"
        )
    else:
        logger.error(f"Agency {agency_id}: Sync failed - {result.get('error')}")
    
    return result
