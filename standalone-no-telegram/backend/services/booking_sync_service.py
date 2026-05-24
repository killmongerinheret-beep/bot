"""
Booking Sync Service - Syncs booking requests from Google Sheets to MonitorTasks
No Telegram required - fully automated from Google Sheets
"""

import logging
from datetime import datetime
from django.utils import timezone
from monitors.models import Agency, MonitorTask, BuyerProfile
import json

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Simple Google Sheets reader"""
    
    def read_sheet(self, sheet_url, sheet_name='Sheet1'):
        """Read data from Google Sheets"""
        try:
            import gspread
            from google.oauth2 import service_account
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                '/app/google-credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Open sheet
            client = gspread.authorize(credentials)
            
            # Extract sheet ID from URL
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            spreadsheet = client.open_by_key(sheet_id)
            
            # Get worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                # If sheet name not found, use first sheet
                worksheet = spreadsheet.get_worksheet(0)
            
            # Get all values
            return worksheet.get_all_values()
            
        except Exception as e:
            logger.error(f"Error reading Google Sheet: {e}")
            raise


class BookingSyncService:
    """
    Syncs booking requests from Google Sheets to MonitorTasks
    """
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
    
    def sync_booking_requests(self, agency_id):
        """
        Read booking requests from Google Sheets and create MonitorTasks
        """
        try:
            agency = Agency.objects.get(id=agency_id)
            
            if not agency.google_sheet_url:
                logger.warning(f"Agency {agency_id} has no Google Sheet URL")
                return {'success': False, 'error': 'No Google Sheet URL'}
            
            logger.info(f"Syncing booking requests for agency {agency_id}")
            
            # Read booking requests sheet
            requests = self._read_booking_requests(agency.google_sheet_url)
            logger.info(f"Found {len(requests)} booking requests")
            
            # Read participants sheet
            participants_map = self._read_participants(agency.google_sheet_url)
            logger.info(f"Found participants for {len(participants_map)} requests")
            
            created_count = 0
            skipped_count = 0
            
            for request in requests:
                request_id = request.get('request_id')
                status = request.get('status', 'pending').lower()
                
                # Only process pending requests
                if status != 'pending':
                    skipped_count += 1
                    continue
                
                # Check if task already exists
                existing_task = MonitorTask.objects.filter(
                    agency=agency,
                    external_reference=request_id
                ).first()
                
                if existing_task:
                    logger.info(f"Task already exists for {request_id}")
                    skipped_count += 1
                    continue
                
                # Create new monitoring task
                task = self._create_task_from_request(agency, request, participants_map)
                
                if task:
                    created_count += 1
                    logger.info(f"Created task {task.id} for request {request_id}")
            
            logger.info(f"Sync complete: {created_count} created, {skipped_count} skipped")
            
            return {
                'success': True,
                'created': created_count,
                'skipped': skipped_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing booking requests: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _read_booking_requests(self, sheet_url):
        """Read booking requests from Sheet 1"""
        try:
            data = self.sheets_service.read_sheet(sheet_url, sheet_name='Booking Requests')
            
            if not data or len(data) < 2:
                logger.warning("No booking requests found in sheet")
                return []
            
            # Parse headers
            headers = [h.lower().replace(' ', '_') for h in data[0]]
            requests = []
            
            # Parse data rows
            for row in data[1:]:
                if not row or len(row) == 0:
                    continue
                
                # Skip empty rows
                if not any(row):
                    continue
                
                request = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        request[header] = row[i].strip() if row[i] else ''
                
                # Only add if has request_id
                if request.get('request_id'):
                    requests.append(request)
            
            return requests
            
        except Exception as e:
            logger.error(f"Error reading booking requests: {e}")
            return []
    
    def _read_participants(self, sheet_url):
        """Read participants from Sheet 2, grouped by request_id"""
        try:
            data = self.sheets_service.read_sheet(sheet_url, sheet_name='Participants')
            
            if not data or len(data) < 2:
                logger.warning("No participants found in sheet")
                return {}
            
            # Parse headers
            headers = [h.lower().replace(' ', '_') for h in data[0]]
            participants_map = {}
            
            # Parse data rows
            for row in data[1:]:
                if not row or len(row) == 0:
                    continue
                
                # Skip empty rows
                if not any(row):
                    continue
                
                participant = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        participant[header] = row[i].strip() if row[i] else ''
                
                request_id = participant.get('request_id')
                if request_id:
                    if request_id not in participants_map:
                        participants_map[request_id] = []
                    participants_map[request_id].append(participant)
            
            return participants_map
            
        except Exception as e:
            logger.error(f"Error reading participants: {e}")
            return {}
    
    def _create_task_from_request(self, agency, request, participants_map):
        """Create MonitorTask from booking request"""
        try:
            request_id = request.get('request_id')
            date = request.get('date')
            visitors = int(request.get('visitors', 1))
            ticket_type_str = request.get('ticket_type', 'standard').lower()
            language = request.get('language', '').upper() or None
            
            # Validate required fields
            if not request_id or not date:
                logger.error(f"Missing required fields: request_id={request_id}, date={date}")
                return None
            
            # Map ticket type
            ticket_type = 0 if ticket_type_str == 'standard' else 1
            
            # Get participants for this request
            participants = participants_map.get(request_id, [])
            
            if not participants:
                logger.warning(f"No participants found for request {request_id}")
            
            # Create or update buyer profile
            if participants:
                first_participant = participants[0]
                profile, created = BuyerProfile.objects.get_or_create(
                    agency=agency,
                    defaults={
                        'first_name': first_participant.get('first_name', ''),
                        'last_name': first_participant.get('last_name', ''),
                        'email': first_participant.get('email', ''),
                        'phone': first_participant.get('phone', ''),
                        'city': first_participant.get('city', 'Roma'),
                        'country': first_participant.get('country', 'Italia'),
                        'birth_date': first_participant.get('birth_date') or None,
                        'participants_json': json.dumps(participants)
                    }
                )
                
                if not created:
                    # Update participants
                    profile.participants_json = json.dumps(participants)
                    profile.save()
                    logger.info(f"Updated BuyerProfile for agency {agency.id}")
            
            # Create monitoring task
            task = MonitorTask.objects.create(
                agency=agency,
                date=date,
                visitors=visitors,
                ticket_type=ticket_type,
                language=language,
                external_reference=request_id,
                is_active=True,
                created_via='google_sheets'
            )
            
            logger.info(f"Created task {task.id} for request {request_id}: {date}, {visitors} visitors")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from request: {e}", exc_info=True)
            return None
    
    def update_booking_completion(self, task_id, booking_reference):
        """
        Update Google Sheets when booking is completed
        """
        try:
            task = MonitorTask.objects.get(id=task_id)
            
            if not task.external_reference:
                logger.info(f"Task {task_id} has no external reference, skipping sheet update")
                return
            
            agency = task.agency
            if not agency.google_sheet_url:
                logger.info(f"Agency {agency.id} has no Google Sheet URL, skipping sheet update")
                return
            
            logger.info(f"Updating Google Sheets for task {task_id}, request {task.external_reference}")
            
            # Read current sheet data
            data = self.sheets_service.read_sheet(agency.google_sheet_url, sheet_name='Booking Requests')
            
            if not data or len(data) < 2:
                logger.warning("No data in Booking Requests sheet")
                return
            
            # Find row with matching request_id
            headers = [h.lower().replace(' ', '_') for h in data[0]]
            request_id_col = headers.index('request_id') if 'request_id' in headers else 0
            status_col = headers.index('status') if 'status' in headers else -1
            booking_ref_col = headers.index('booking_ref') if 'booking_ref' in headers else -1
            
            # Update the row (this is simplified - full implementation would use Google Sheets API)
            logger.info(f"Would update row for {task.external_reference}: status=booked, ref={booking_reference}")
            
            # TODO: Implement actual Google Sheets update using gspread
            # worksheet.update_cell(row, status_col + 1, 'booked')
            # worksheet.update_cell(row, booking_ref_col + 1, booking_reference)
            
        except Exception as e:
            logger.error(f"Error updating booking completion: {e}", exc_info=True)
