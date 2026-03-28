from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Agency, MonitorTask, CheckResult, Proxy, SiteCredential, User
from .serializers import (
    AgencySerializer, MonitorTaskSerializer, CheckResultSerializer,
    ProxySerializer, SiteCredentialSerializer
)
import logging
import secrets
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================
# Authentication APIs
# ============================================

@api_view(['POST'])
def register_user(request):
    """
    Register a new user.
    Body: {
        "email": "user@example.com",
        "username": "username",
        "password": "password123",
        "full_name": "Full Name",
        "agency_id": 1  # Optional - if not provided, creates new agency
    }
    """
    try:
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')
        agency_id = request.data.get('agency_id')
        
        # Validation
        if not email or not username or not password:
            return Response({'error': 'Email, username, and password are required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=400)
        
        # Get or create agency
        if agency_id:
            try:
                agency = Agency.objects.get(id=agency_id)
            except Agency.DoesNotExist:
                return Response({'error': 'Agency not found'}, status=404)
        else:
            # Create new agency for this user
            agency = Agency.objects.create(
                name=f"{username}'s Agency",
                api_key=secrets.token_hex(16),
                plan='free'
            )
        
        # Create user
        user = User.objects.create(
            email=email,
            username=username,
            full_name=full_name,
            agency=agency
        )
        user.set_password(password)
        user.save()
        
        # Generate session token (simple token for now)
        session_token = secrets.token_urlsafe(32)
        
        # Store session in cache (expires in 7 days)
        from django.core.cache import cache
        cache.set(f"session:{session_token}", {
            'user_id': user.id,
            'agency_id': agency.id,
            'username': user.username
        }, timeout=7*24*60*60)
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'session_token': session_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name
            },
            'agency': {
                'id': agency.id,
                'name': agency.name,
                'plan': agency.plan
            }
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def login_user(request):
    """
    Login user.
    Body: {
        "username": "username or email",
        "password": "password123"
    }
    """
    try:
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response({'error': 'Username/email and password are required'}, status=400)
        
        # Find user by username or email
        from django.db.models import Q
        user = User.objects.filter(
            Q(username=username_or_email) | Q(email=username_or_email)
        ).first()
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        
        if not user.is_active:
            return Response({'error': 'Account is inactive'}, status=403)
        
        # Check password
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=401)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Store session in cache (expires in 7 days)
        from django.core.cache import cache
        cache.set(f"session:{session_token}", {
            'user_id': user.id,
            'agency_id': user.agency.id,
            'username': user.username,
            'is_super_admin': user.is_super_admin  # Include super admin flag
        }, timeout=7*24*60*60)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'session_token': session_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin  # Include in response
            },
            'agency': {
                'id': user.agency.id,
                'name': user.agency.name,
                'plan': user.agency.plan,
                'telegram_chat_id': user.agency.telegram_chat_id
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def logout_user(request):
    """
    Logout user.
    Headers: Authorization: Bearer <session_token>
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response({'error': 'Invalid authorization header'}, status=401)
        
        session_token = auth_header.replace('Bearer ', '')
        
        # Delete session from cache
        from django.core.cache import cache
        cache.delete(f"session:{session_token}")
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def verify_session(request):
    """
    Verify session token and return user info.
    Headers: Authorization: Bearer <session_token>
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response({'error': 'Invalid authorization header'}, status=401)
        
        session_token = auth_header.replace('Bearer ', '')
        
        # Get session from cache
        from django.core.cache import cache
        session_data = cache.get(f"session:{session_token}")
        
        if not session_data:
            return Response({'error': 'Invalid or expired session'}, status=401)
        
        # Get user
        user = User.objects.select_related('agency').get(id=session_data['user_id'])
        
        if not user.is_active:
            return Response({'error': 'Account is inactive'}, status=403)
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin
            },
            'agency': {
                'id': user.agency.id,
                'name': user.agency.name,
                'plan': user.agency.plan,
                'telegram_chat_id': user.agency.telegram_chat_id
            }
        })
        
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Session verification error: {e}")
        return Response({'error': str(e)}, status=500)


def get_user_from_request(request):
    """Helper function to get user from session token"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        session_token = auth_header.replace('Bearer ', '')
        
        from django.core.cache import cache
        session_data = cache.get(f"session:{session_token}")
        
        if not session_data:
            return None
        
        user = User.objects.select_related('agency').get(id=session_data['user_id'])
        return user if user.is_active else None
        
    except:
        return None


class AgencyViewSet(viewsets.ModelViewSet):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        """Filter agencies based on authenticated user"""
        user = get_user_from_request(self.request)
        if user:
            # User can only see their own agency
            return Agency.objects.filter(id=user.agency.id)
        # If no auth, return empty (or all for backwards compatibility during migration)
        return Agency.objects.all()


class MonitorTaskViewSet(viewsets.ModelViewSet):
    serializer_class = MonitorTaskSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_queryset(self):
        """Filter tasks based on authenticated user's agency"""
        user = get_user_from_request(self.request)
        
        queryset = MonitorTask.objects.all()
        
        # Filter by user's agency if authenticated
        if user:
            queryset = queryset.filter(agency=user.agency)
        else:
            # Backwards compatibility: allow agency_id query param
            agency_id = self.request.query_params.get('agency_id')
            if agency_id:
                queryset = queryset.filter(agency_id=agency_id)
        
        return queryset

    def perform_create(self, serializer):
        # No monitor count limits — plan gates tier features (hold/snipe), not quantity
        serializer.save()

class CheckResultViewSet(viewsets.ModelViewSet):
    serializer_class = CheckResultSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_queryset(self):
        """Filter results based on authenticated user's agency"""
        user = get_user_from_request(self.request)
        
        queryset = CheckResult.objects.all().order_by('-check_time')
        task_id = self.request.query_params.get('task')
        
        # Filter by user's agency if authenticated
        if user:
            queryset = queryset.filter(task__agency=user.agency)
        else:
            # Backwards compatibility
            agency_id = self.request.query_params.get('agency_id')
            if agency_id:
                queryset = queryset.filter(task__agency_id=agency_id)
        
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            
        return queryset

class ProxyViewSet(viewsets.ModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

class SiteCredentialViewSet(viewsets.ModelViewSet):
    queryset = SiteCredential.objects.all()
    serializer_class = SiteCredentialSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

class AgencyLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # ✅ Disable SessionAuth to bypass CSRF

    def post(self, request):
        name = request.data.get('name')
        api_key = request.data.get('api_key')
        
        if not name or not api_key:
            return Response({'error': 'Name and API Key search required'}, status=status.HTTP_400_BAD_REQUEST)
            
        agency = Agency.objects.filter(name=name, api_key=api_key).order_by('id').first()
        
        if not agency:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not agency.is_active:
            return Response({'error': 'Agency account is inactive'}, status=status.HTTP_403_FORBIDDEN)
            
        return Response({
            'id': agency.id,
            'name': agency.name,
            'chat_id': agency.telegram_chat_id
        })

class MyAgencyView(APIView):
    """
    Get or Create an Agency for the authenticated Clerk User.
    Expects 'owner_id' in request data.
    """
    permission_classes = [permissions.AllowAny] # In future, verify JWT
    authentication_classes = []  # ✅ Disable SessionAuth to bypass CSRF

    def post(self, request):
        owner_id = request.data.get('owner_id', 'local-admin')
        email = request.data.get('email', 'admin@local.com')
        
        # 1. Try to find by ID first
        agency = Agency.objects.filter(owner_id=owner_id).first()
        created = False
        
        if not agency:
             # 2. Account Recovery: Try to find orphaned agency by name pattern
             email_prefix = email.split('@')[0]
             potential_name = f"Agency-{email_prefix}"
             
             # Also try relaxed match if name was user-edited, but this is risky.
             # Stick to default name pattern for auto-recovery.
             agency = Agency.objects.filter(name=potential_name, owner_id__isnull=True).first()
             
             if agency:
                 # ✅ Claim it!
                 agency.owner_id = owner_id
                 agency.save()
             else:
                 # 3. Create new
                 import uuid
                 defaults = {
                    'name': f"Agency-{email_prefix}",
                    'api_key': str(uuid.uuid4())[:8]
                 }
                 agency, created = Agency.objects.get_or_create(
                    owner_id=owner_id,
                    defaults=defaults
                 )
            
        return Response({
            'id': agency.id,
            'name': agency.name,
            'api_key': agency.api_key,
            'chat_id': agency.telegram_chat_id,
            'plan': agency.plan,
            'task_limit': {'free': 1000, 'pro': 2000, 'agency': 5000}.get(agency.plan, 1000)
        })


# ✅ NEW: Vatican Ticket Discovery API
from rest_framework.decorators import api_view

@api_view(['GET'])
def get_vatican_tickets(request):
    """
    Returns list of available Vatican tickets with their IDs and language requirements.
    Dynamically fetches from Vatican website using HydraBot.
    Cleans up and groups tickets for better display.
    
    Query params:
        date: DD/MM/YYYY format (default: 20/02/2026)
    
    Returns:
        {
            'date': '20/02/2026',
            'tickets': [...],
            'grouped': {...}  # Tickets grouped by category
        }
    """
    date = request.query_params.get('date', '20/02/2026')
    visitors = int(request.query_params.get('visitors', 1))
    
    # Ticket name mappings - ORDER MATTERS! Check ticket types FIRST, locations LAST
    # These are checked in order, so more specific terms should come first
    TICKET_TYPE_KEYWORDS = [
        # Ticket types (check these FIRST)
        ('visita guidata', 'Guided Tour'),
        ('tour guidato', 'Guided Tour'),
        ('visite guidate', 'Guided Tour'),
        ('audioguida', 'Entry + Audio Guide'),
        ('ingresso intero', 'Standard Entry (Full Price)'),
        ('ingresso ridotto', 'Standard Entry (Reduced)'),
        ('ingresso gratuito', 'Standard Entry (Free)'),
        ('biglietto di ingresso', 'Standard Entry'),
        ('biglietto ingresso', 'Standard Entry'),
        ("biglietti d'ingresso", 'Standard Entry'),
        ('biglietti di ingresso', 'Standard Entry'),
        # Special experiences
        ('prime experience', 'Prime Experience'),
        ('experience', 'Special Experience'),
        # Locations (check LAST as fallback)
        ('cappella sistina', 'Sistine Chapel'),
        ('giardini vaticani', 'Vatican Gardens'),
    ]
    
    def normalize_ticket_name(raw_name):
        """Parse Italian ticket name and return clean English label + time slot"""
        name_lower = raw_name.lower()
        
        # Extract time slot if present (e.g., "09:00", "14:30")
        import re
        time_match = re.search(r'(\d{1,2}[:\.]?\d{2})', raw_name)
        time_slot = time_match.group(1).replace('.', ':') if time_match else None
        
        # Determine category - check in order, first match wins
        category = 'Vatican Museums'  # Default fallback
        for italian, english in TICKET_TYPE_KEYWORDS:
            if italian in name_lower:
                category = english
                break
        
        # Build clean name
        if time_slot:
            clean_name = f"{category} - {time_slot}"
        else:
            clean_name = category
            
        return {
            'clean_name': clean_name,
            'category': category,
            'time_slot': time_slot,
            'original_name': raw_name
        }
    
    try:
        from worker_vatican.hydra_monitor import HydraBot
        import asyncio
        import logging
        
        async def fetch_category(browser, bot, ticket_type):
            """Helper to fetch a specific category in its own page"""
            try:
                page = await browser.new_page()
                tickets = await bot.resolve_all_dynamic_ids(
                    page,
                    ticket_type=ticket_type,
                    target_date=date,
                    visitors=visitors
                )
                await page.close()
                return tickets
            except Exception as e:
                logger.error(f"Failed to fetch types={ticket_type}: {e}")
                return []

        async def fetch_tickets():
            bot = HydraBot()
            result = []
            
            try:
                async with bot.get_browser() as browser:
                    # Run standard (0) and guided (1) in parallel
                    task_standard = fetch_category(browser, bot, 0)
                    task_guided = fetch_category(browser, bot, 1)
                    
                    results = await asyncio.gather(task_standard, task_guided)
                    standard_tickets, guided_tickets = results
                    
                    # Process Standard
                    for ticket in standard_tickets:
                        try:
                            parsed = normalize_ticket_name(ticket['name'])
                            result.append({
                                'id': ticket['id'],
                                'name': parsed['clean_name'],
                                'originalName': parsed['original_name'],
                                'description': ticket.get('description', ''),
                                'category': parsed['category'],
                                'timeSlot': parsed['time_slot'],
                                'needsLanguage': False,
                                'availableLanguages': [],
                                'ticketType': 0,
                                'deepLink': ticket.get('deep_link', '')
                            })
                        except Exception as e:
                            logger.error(f"Error parsing ticket {ticket}: {e}")

                    # Process Guided
                    for ticket in guided_tickets:
                        try:
                            parsed = normalize_ticket_name(ticket['name'])
                            result.append({
                                'id': ticket['id'],
                                'name': parsed['clean_name'],
                                'originalName': parsed['original_name'],
                                'description': ticket.get('description', ''),
                                'category': parsed['category'],
                                'timeSlot': parsed['time_slot'],
                                'needsLanguage': True,
                                'availableLanguages': ['ENG', 'ITA', 'FRA', 'DEU', 'SPA'],
                                'ticketType': 1,
                                'deepLink': ticket.get('deep_link', '')
                            })
                        except Exception as e:
                            logger.error(f"Error parsing ticket {ticket}: {e}")
            
            except Exception as e:
                logger.error(f"Browser error: {e}")
                # Don't raise, return what we have (or empty) so UI doesn't crash 500
                pass
            
            return result
        
        tickets = asyncio.run(fetch_tickets())
        
        # Group tickets by category for cleaner display
        grouped = {}
        for ticket in tickets:
            cat = ticket['category']
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(ticket)
        
        # Sort each group by time slot
        for cat in grouped:
            grouped[cat].sort(key=lambda t: t['timeSlot'] or '99:99')
        
        return Response({
            'date': date,
            'tickets': tickets,
            'grouped': grouped,
            'total': len(tickets)
        })
    
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)



# ============================================
# Telegram Group Management APIs
# ============================================

@api_view(['GET'])
def list_telegram_groups(request):
    """
    List all Telegram groups with their approval status.
    Query params:
        status: Filter by status (pending/approved/rejected/suspended)
    """
    from .models import TelegramGroup
    
    status_filter = request.query_params.get('status')
    
    groups = TelegramGroup.objects.all()
    
    if status_filter:
        groups = groups.filter(status=status_filter)
    
    groups = groups.order_by('-created_at')
    
    data = []
    for group in groups:
        data.append({
            'id': group.id,
            'chat_id': group.chat_id,
            'chat_title': group.chat_title,
            'chat_type': group.chat_type,
            'chat_username': group.chat_username,
            'status': group.status,
            'agency': {
                'id': group.agency.id,
                'name': group.agency.name
            } if group.agency else None,
            'added_by': {
                'user_id': group.added_by_user_id,
                'username': group.added_by_username,
                'first_name': group.added_by_first_name
            },
            'member_count': group.member_count,
            'notification_enabled': group.notification_enabled,
            'created_at': group.created_at.isoformat(),
            'approved_at': group.approved_at.isoformat() if group.approved_at else None,
            'approved_by': group.approved_by,
            'rejection_reason': group.rejection_reason,
            'last_activity': group.last_activity.isoformat() if group.last_activity else None
        })
    
    return Response(data)


@api_view(['POST'])
def approve_telegram_group(request, group_id):
    """
    Approve a Telegram group.
    Body params:
        agency_id: Optional - Link group to specific agency
    """
    from .models import TelegramGroup, Agency
    import os
    
    try:
        group = TelegramGroup.objects.get(id=group_id)
        agency_id = request.data.get('agency_id')
        
        # Link to agency if provided
        if agency_id:
            try:
                agency = Agency.objects.get(id=agency_id)
                group.agency = agency
                group.save()
            except Agency.DoesNotExist:
                return Response({'error': 'Agency not found'}, status=404)
        
        # Approve
        admin_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'admin'
        group.approve(admin_id=str(admin_id))
        
        # Send approval notification to group
        try:
            from telegram import Bot
            bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
            
            bot.send_message(
                chat_id=group.chat_id,
                text=(
                    f"✅ **Group Approved!**\n\n"
                    f"Your group has been approved by an admin.\n\n"
                    f"You will now receive notifications when Vatican tickets become available!\n\n"
                    f"Use /start to manage your monitors."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Group approved',
            'group': {
                'id': group.id,
                'chat_id': group.chat_id,
                'chat_title': group.chat_title,
                'status': group.status
            }
        })
        
    except TelegramGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error approving group: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def reject_telegram_group(request, group_id):
    """
    Reject a Telegram group.
    Body params:
        reason: Rejection reason (required)
    """
    from .models import TelegramGroup
    import os
    
    try:
        group = TelegramGroup.objects.get(id=group_id)
        reason = request.data.get('reason', 'Not specified')
        
        # Reject
        admin_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'admin'
        group.reject(admin_id=str(admin_id), reason=reason)
        
        # Send rejection notification to group
        try:
            from telegram import Bot
            bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
            
            bot.send_message(
                chat_id=group.chat_id,
                text=(
                    f"❌ **Group Rejected**\n\n"
                    f"Your group approval request has been rejected.\n\n"
                    f"**Reason:** {reason}\n\n"
                    f"Please contact support if you believe this is an error."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Group rejected',
            'group': {
                'id': group.id,
                'chat_id': group.chat_id,
                'chat_title': group.chat_title,
                'status': group.status
            }
        })
        
    except TelegramGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error rejecting group: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def suspend_telegram_group(request, group_id):
    """
    Suspend a Telegram group.
    Body params:
        reason: Suspension reason (optional)
    """
    from .models import TelegramGroup
    
    try:
        group = TelegramGroup.objects.get(id=group_id)
        reason = request.data.get('reason')
        
        group.suspend(reason=reason)
        
        return Response({
            'success': True,
            'message': 'Group suspended',
            'group': {
                'id': group.id,
                'chat_id': group.chat_id,
                'chat_title': group.chat_title,
                'status': group.status
            }
        })
        
    except TelegramGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error suspending group: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def list_held_slots(request):
    """List all active held slots — all holds for super admin, agency-filtered otherwise."""
    from .models import HeldSlot
    from django.core.cache import cache

    # Check session for super admin
    auth_header = request.headers.get('Authorization', '')
    session_data = None
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
        session_data = cache.get(f"session:{token}")

    status_filter = request.query_params.get('status', 'held')

    # Super admin or no auth — return all holds
    if session_data and session_data.get('is_super_admin'):
        holds = HeldSlot.objects.all()
    else:
        agency = _get_agency_from_request(request)
        if not agency:
            # No auth — return all holds (for dashboard display)
            holds = HeldSlot.objects.all()
        else:
            holds = HeldSlot.objects.filter(task__agency=agency)

    if status_filter != 'all':
        holds = holds.filter(status=status_filter)

    holds = holds.order_by('date', 'slot_time', 'visitors')

    data = []
    for h in holds:
        data.append({
            'id': h.id,
            'date': h.date,
            'slot_time': h.slot_time,
            'ticket_name': h.ticket_name,
            'visitors': h.visitors,
            'total_price': str(h.total_price),
            'status': h.status,
            'hold_duration_minutes': h.hold_duration_minutes(),
            'last_keepalive_at': h.last_keepalive_at.isoformat(),
            'hold_started_at': h.hold_started_at.isoformat(),
        })
    return Response(data)


@api_view(['POST'])
def release_held_slot(request, hold_id):
    """Release a held slot."""
    from .models import HeldSlot
    from .hold_manager import release_slot
    agency = _get_agency_from_request(request)
    if not agency:
        return Response({'error': 'Not authenticated'}, status=401)

    try:
        hold = HeldSlot.objects.get(id=hold_id, task__agency=agency)
        release_slot(hold)
        return Response({'success': True, 'message': f'Hold #{hold_id} released'})
    except HeldSlot.DoesNotExist:
        return Response({'error': 'Hold not found'}, status=404)


def _get_agency_from_request(request):
    """Helper to get agency from session."""
    from .models import Agency
    agency_id = request.session.get('agency_id')
    if agency_id:
        return Agency.objects.filter(id=agency_id).first()
    return None


from django.http import HttpResponse, StreamingHttpResponse
import requests as req_lib
import os
from django.views.decorators.csrf import csrf_exempt

VATICAN_BASE = 'https://tickets.museivaticani.va'

@csrf_exempt
def checkout_redirect(request, hold_id):
    """
    Two modes:
    - GET  → show hold details page with "Get Payment Link" button
    - POST → call Vatican /api/visit/reservation server-side, return epay URL
    """
    from .models import HeldSlot, BuyerProfile

    try:
        hold = HeldSlot.objects.select_related('task__agency').get(id=hold_id, status='held')
    except HeldSlot.DoesNotExist:
        return HttpResponse(_error_page("Hold not found or already expired."),
                           status=404, content_type='text/html')

    if request.method == 'POST':
        return _do_reservation(request, hold)

    # GET — show the hold details page
    agency = hold.task.agency
    has_profile = BuyerProfile.objects.filter(agency=agency).exists()

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Vatican Checkout — {hold.date} {hold.slot_time}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#fff;
         min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
    .card{{background:#111;border:1px solid #222;border-radius:20px;padding:32px;max-width:480px;width:100%}}
    .badge{{display:inline-block;background:#00E37C20;color:#00E37C;border:1px solid #00E37C40;
            border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;margin-bottom:20px}}
    h2{{font-size:22px;font-weight:700;margin-bottom:8px}}
    .meta{{color:#666;font-size:14px;margin-bottom:28px}}
    .row{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #1a1a1a;font-size:14px}}
    .row:last-of-type{{border-bottom:none}}
    .label{{color:#666}}.value{{color:#fff;font-weight:500}}
    .total{{color:#00E37C;font-size:18px;font-weight:700}}
    .btn{{display:block;width:100%;margin-top:28px;padding:16px;background:#00E37C;color:#000;
          border:none;border-radius:14px;font-size:16px;font-weight:700;cursor:pointer;transition:opacity .2s}}
    .btn:hover{{opacity:.9}}.btn:disabled{{opacity:.5;cursor:not-allowed}}
    .btn-secondary{{background:#1a1a1a;color:#888;border:1px solid #262626;margin-top:12px}}
    .warn{{margin-top:16px;padding:12px;background:#ff4d4d15;border:1px solid #ff4d4d30;
           border-radius:10px;font-size:13px;color:#ff4d4d}}
    .info{{margin-top:16px;padding:12px;background:#00E37C10;border:1px solid #00E37C30;
           border-radius:10px;font-size:13px;color:#00E37C}}
    #result{{margin-top:20px;display:none}}
    .pay-link{{display:block;margin-top:12px;padding:16px;background:#00E37C;color:#000;
               border-radius:14px;font-size:15px;font-weight:700;text-align:center;text-decoration:none}}
    .spinner{{display:inline-block;width:16px;height:16px;border:2px solid #000;
              border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:8px}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
  </style>
</head>
<body>
<div class="card">
  <div class="badge">🔒 SLOT HELD</div>
  <h2>Vatican Checkout</h2>
  <p class="meta">Hold #{hold.id} &bull; Agency: {agency.name}</p>

  <div class="row"><span class="label">Date</span><span class="value">{hold.date}</span></div>
  <div class="row"><span class="label">Time</span><span class="value">{hold.slot_time}</span></div>
  <div class="row"><span class="label">Visitors</span><span class="value">{hold.visitors}</span></div>
  <div class="row"><span class="label">Total</span><span class="value total">&euro;{hold.total_price}</span></div>

  {'<div class="warn">⚠️ No buyer profile set. <a href="#" style="color:#ff4d4d">Set profile</a> to generate payment link.</div>' if not has_profile else ''}

  <div style="margin-top:20px">
    <label style="font-size:12px;color:#666;display:block;margin-bottom:6px">
      reCAPTCHA Token (optional — paste from browser DevTools for instant payment)
    </label>
    <textarea id="recaptchaToken" placeholder="Paste reCAPTCHA token here, or leave empty to auto-solve..."
      style="width:100%;background:#1a1a1a;border:1px solid #262626;border-radius:10px;
             padding:10px;color:#fff;font-size:11px;font-family:monospace;resize:vertical;
             min-height:60px;outline:none"></textarea>
    <p style="font-size:11px;color:#444;margin-top:4px">
      To get token: open Vatican site → DevTools → Network → filter "reservation" → copy recaptcha value
    </p>
  </div>

  <button class="btn" id="payBtn" onclick="getPaymentLink()" {'disabled' if not has_profile else ''}>
    💳 Generate Payment Link
  </button>

  <div id="result"></div>
  <p style="margin-top:16px;font-size:12px;color:#444;text-align:center">
    ⚠️ Single-use link. Do not share until ready to pay.
  </p>
</div>

<script>
async function getPaymentLink() {{
  var btn = document.getElementById('payBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Generating...';

  try {{
    var resp = await fetch(window.location.href, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')}},
      body: JSON.stringify({{recaptcha: document.getElementById('recaptchaToken').value.trim()}})
    }});
    var data = await resp.json();

    var result = document.getElementById('result');
    if (data.payment_url) {{
      result.innerHTML = '<div class="info">✅ Reservation confirmed! Payment page opens in new tab.</div>' +
        '<a class="pay-link" href="' + data.payment_url + '" target="_blank">💳 Pay Now — epay.catholica.va</a>' +
        '<p style="font-size:11px;color:#555;margin-top:8px">This is a clean payment link — no session needed. Share it or open it in any browser.</p>';
      result.style.display = 'block';
      window.open(data.payment_url, '_blank');
      btn.innerHTML = '✅ Payment Link Ready';
    }} else {{
      result.innerHTML = '<div class="warn">❌ ' + (data.error || 'Failed to generate link') + '</div>';
      result.style.display = 'block';
      btn.disabled = false;
      btn.innerHTML = '💳 Generate Payment Link';
    }}
  }} catch(e) {{
    document.getElementById('result').innerHTML = '<div class="warn">❌ Network error: ' + e.message + '</div>';
    document.getElementById('result').style.display = 'block';
    btn.disabled = false;
    btn.innerHTML = '💳 Generate Payment Link';
  }}
}}

function getCookie(name) {{
  var v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : '';
}}
</script>
</body>
</html>"""

    return HttpResponse(html, content_type='text/html')


def _do_reservation(request, held):
    """
    Call Vatican /api/visit/reservation server-side using held JSESSIONID.
    Vatican uses Cloudflare Turnstile (sitekey: 0x4AAAAAAB2Edz1zEK7o5Rj1).
    After success, Vatican redirects to epay.catholica.va — that's the payment URL.
    """
    import json as _json, re
    from django.http import JsonResponse
    from .models import BuyerProfile

    try:
        profile = BuyerProfile.objects.get(agency=held.task.agency)
    except BuyerProfile.DoesNotExist:
        return JsonResponse({'error': 'No buyer profile set for this agency'}, status=400)

    try:
        req_body = _json.loads(request.body or '{}')
    except Exception:
        req_body = {}
    turnstile_token = req_body.get('recaptcha', '')

    participants = profile.to_participant_list(held.visitors, ticket_id=60, service_ids=[58])

    body = {
        "recaptcha": turnstile_token,
        "lang": "it",
        "recapId": held.recap_id or '',
        "visitorNum": held.visitors,
        "visitId": held.slot_id,
        "visitTypeId": int(held.ticket_id),
        "tickets": [
            {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": held.visitors},
            {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": 0},
        ],
        "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": held.visitors}],
        "representativeUser": profile.to_representative_user(),
        "participantUser": participants,
        "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
    }

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'Referer': f'{VATICAN_BASE}/home/checkout',
        'Origin': VATICAN_BASE,
        'Content-Type': 'application/json',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    }

    s = req_lib.Session()
    s.cookies.set('JSESSIONID', held.jsessionid, domain='tickets.museivaticani.va')
    if held.ticketmv:
        s.cookies.set('ticketmv', held.ticketmv, domain='tickets.museivaticani.va')

    try:
        r = s.post(
            f'{VATICAN_BASE}/api/visit/reservation',
            json=body, headers=headers, timeout=20,
            allow_redirects=False  # catch the redirect manually
        )

        # Vatican returns 302 redirect to epay on success
        if r.status_code in (200, 302):
            payment_url = ''

            # Check Location header (302 redirect)
            if r.status_code == 302:
                payment_url = r.headers.get('Location', '')

            # Check response body for epay URL
            if not payment_url:
                match = re.search(r'https://epay\.catholica\.va[^\s"\'\\]+', r.text)
                if match:
                    payment_url = match.group(0)

            # Check JSON keys
            if not payment_url:
                try:
                    data = r.json()
                    # Vatican response format: {"total":"2500","referenceOrder":"...","epay":{"url":"https://epay.catholica.va/...",...}}
                    epay = data.get('epay', {})
                    payment_url = (
                        epay.get('url') or
                        data.get('redirectUrl') or
                        data.get('paymentUrl') or
                        data.get('url') or
                        ''
                    )
                    # Build full epay URL if we have the components
                    if not payment_url:
                        siv_id = data.get('sivTransactionId') or data.get('transactionId')
                        mac = data.get('uppRedirectMac') or data.get('mac')
                        if siv_id and mac:
                            jsid_epay = s.cookies.get('JSESSIONID', held.jsessionid)
                            payment_url = f"https://epay.catholica.va/pay/public/init/{siv_id}/{mac}/it;jsessionid={jsid_epay}"
                except Exception:
                    pass

            if payment_url:
                held.status = 'paying'
                held.payment_url = payment_url
                held.save(update_fields=['status', 'payment_url'])
                return JsonResponse({'payment_url': payment_url, 'recap_id': held.recap_id})
            else:
                return JsonResponse({
                    'error': 'Reservation succeeded but no payment URL found',
                    'raw': r.text[:500],
                    'status': r.status_code,
                    'headers': dict(r.headers),
                })
        else:
            err_msg = ''
            try:
                err_msg = r.json().get('message', r.text[:200])
            except Exception:
                err_msg = r.text[:200]
            return JsonResponse({
                'error': f'Reservation failed ({r.status_code}): {err_msg}',
            }, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _error_page(msg):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Error</title>
<style>body{{font-family:sans-serif;background:#111;color:#fff;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column;gap:12px;}}
h2{{color:#ff4d4d;}}p{{color:#888;}}</style></head>
<body><h2>⚠️ {msg}</h2><p>The hold session may have expired.</p></body></html>"""

    """
    Serves a page with a bookmarklet/button that injects the JSESSIONID
    into the browser for tickets.museivaticani.va, then redirects to checkout.

    Flow:
    1. User opens this page
    2. Page shows hold details + "Open Checkout" button
    3. Button opens tickets.museivaticani.va in a new tab
    4. After 2s (page loads), injects JSESSIONID via postMessage trick
    5. Redirects that tab to /home/checkout
    """
    from .models import HeldSlot

    try:
        hold = HeldSlot.objects.get(id=hold_id, status='held')
    except HeldSlot.DoesNotExist:
        return HttpResponse(_error_page("Hold not found or already expired."),
                           status=404, content_type='text/html')

    jsessionid = hold.jsessionid
    ticketmv = hold.ticketmv or ''

    # Build the bookmarklet JS — injects cookie then goes to checkout
    cookie_js = (
        f"document.cookie='JSESSIONID={jsessionid};domain=.museivaticani.va;path=/;SameSite=Lax';"
        + (f"document.cookie='ticketmv={ticketmv};domain=.museivaticani.va;path=/;SameSite=Lax';" if ticketmv else "")
        + "window.location.href='https://tickets.museivaticani.va/home/checkout';"
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Vatican Checkout — {hold.date} {hold.slot_time}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #fff;
           min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
    .card {{ background: #111; border: 1px solid #222; border-radius: 20px;
             padding: 32px; max-width: 480px; width: 100%; }}
    .badge {{ display: inline-block; background: #00E37C20; color: #00E37C;
              border: 1px solid #00E37C40; border-radius: 20px; padding: 4px 12px;
              font-size: 12px; font-weight: 600; margin-bottom: 20px; }}
    h2 {{ font-size: 22px; font-weight: 700; margin-bottom: 8px; }}
    .meta {{ color: #666; font-size: 14px; margin-bottom: 28px; }}
    .row {{ display: flex; justify-content: space-between; padding: 12px 0;
            border-bottom: 1px solid #1a1a1a; font-size: 14px; }}
    .row:last-of-type {{ border-bottom: none; }}
    .label {{ color: #666; }}
    .value {{ color: #fff; font-weight: 500; }}
    .total {{ color: #00E37C; font-size: 18px; font-weight: 700; }}
    .btn {{ display: block; width: 100%; margin-top: 28px; padding: 16px;
            background: #00E37C; color: #000; border: none; border-radius: 14px;
            font-size: 16px; font-weight: 700; cursor: pointer; text-align: center;
            text-decoration: none; transition: opacity 0.2s; }}
    .btn:hover {{ opacity: 0.9; }}
    .btn:active {{ transform: scale(0.98); }}
    .step {{ margin-top: 20px; padding: 16px; background: #0f0f0f;
             border: 1px solid #1a1a1a; border-radius: 12px; }}
    .step p {{ font-size: 13px; color: #555; line-height: 1.6; }}
    .step code {{ background: #1a1a1a; padding: 2px 6px; border-radius: 4px;
                  font-size: 12px; color: #00E37C; }}
    .warning {{ margin-top: 12px; font-size: 12px; color: #555; text-align: center; }}
    #status {{ margin-top: 16px; padding: 12px; border-radius: 10px;
               font-size: 13px; text-align: center; display: none; }}
    .status-ok {{ background: #00E37C15; color: #00E37C; border: 1px solid #00E37C30; }}
    .status-err {{ background: #ff4d4d15; color: #ff4d4d; border: 1px solid #ff4d4d30; }}
  </style>
</head>
<body>
<div class="card">
  <div class="badge">🔒 SLOT HELD</div>
  <h2>Vatican Checkout</h2>
  <p class="meta">Hold #{hold.id} &bull; Session active</p>

  <div class="row"><span class="label">Date</span><span class="value">{hold.date}</span></div>
  <div class="row"><span class="label">Time</span><span class="value">{hold.slot_time}</span></div>
  <div class="row"><span class="label">Visitors</span><span class="value">{hold.visitors}</span></div>
  <div class="row"><span class="label">Total</span><span class="value total">&euro;{hold.total_price}</span></div>

  <button class="btn" onclick="openCheckout()">💳 Open Vatican Checkout</button>

  <div id="status"></div>

  <div class="step">
    <p>
      Clicking the button opens Vatican in a new tab and injects your session automatically.<br><br>
      If it redirects to the homepage instead of checkout, use the manual method:<br>
      1. Open <code>tickets.museivaticani.va</code> in your browser<br>
      2. Open DevTools → Console<br>
      3. Paste the code below and press Enter
    </p>
  </div>

  <div class="step" style="margin-top:8px">
    <p style="color:#888;margin-bottom:8px;font-size:12px">Manual cookie injection:</p>
    <code id="snippet" style="display:block;word-break:break-all;font-size:11px;color:#00E37C;cursor:pointer"
          onclick="copySnippet()" title="Click to copy">
      {cookie_js}
    </code>
    <p style="margin-top:8px;font-size:11px;color:#444">Click code to copy</p>
  </div>

  <p class="warning">⚠️ This link is single-use. Do not share it.</p>
</div>

<script>
  var JSESSIONID = '{jsessionid}';
  var TICKETMV = '{ticketmv}';
  var vatTab = null;

  function openCheckout() {{
    var btn = document.querySelector('.btn');
    btn.textContent = '⏳ Opening...';
    btn.disabled = true;

    // Open Vatican homepage first (needed to accept cookies for that domain)
    vatTab = window.open('https://tickets.museivaticani.va/home', '_blank');

    if (!vatTab) {{
      showStatus('Popup blocked. Allow popups for this site and try again.', false);
      btn.textContent = '💳 Open Vatican Checkout';
      btn.disabled = false;
      return;
    }}

    // After Vatican loads, inject cookie and navigate to checkout
    var attempts = 0;
    var interval = setInterval(function() {{
      attempts++;
      try {{
        // Try to inject cookie via postMessage to the Vatican tab
        // This works if Vatican doesn't block it
        vatTab.postMessage({{
          type: 'SET_SESSION',
          jsessionid: JSESSIONID
        }}, 'https://tickets.museivaticani.va');
      }} catch(e) {{}}

      // After 3 seconds, navigate to checkout with cookie in URL param
      // Vatican's Angular app reads jsessionid from URL on init
      if (attempts >= 6) {{
        clearInterval(interval);
        try {{
          vatTab.location.href = 'https://tickets.museivaticani.va/home/checkout;jsessionid=' + JSESSIONID;
        }} catch(e) {{
          // Cross-origin block — use the direct URL approach
          vatTab.close();
          window.open('https://tickets.museivaticani.va/home/checkout;jsessionid=' + JSESSIONID, '_blank');
        }}
        showStatus('Vatican checkout opened in new tab. Complete your payment there.', true);
        btn.textContent = '✅ Checkout Opened';
      }}
    }}, 500);
  }}

  function showStatus(msg, ok) {{
    var el = document.getElementById('status');
    el.textContent = msg;
    el.className = ok ? 'status-ok' : 'status-err';
    el.style.display = 'block';
  }}

  function copySnippet() {{
    var code = document.getElementById('snippet').textContent.trim();
    navigator.clipboard.writeText(code).then(function() {{
      showStatus('✅ Copied! Paste in browser console on tickets.museivaticani.va', true);
    }});
  }}
</script>
</body>
</html>"""

    return HttpResponse(html, content_type='text/html')


def _error_page(msg):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Error</title>
<style>body{{font-family:sans-serif;background:#111;color:#fff;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column;gap:12px;}}
h2{{color:#ff4d4d;}}p{{color:#888;}}</style></head>
<body><h2>⚠️ {msg}</h2><p>The hold session may have expired.</p></body></html>"""
