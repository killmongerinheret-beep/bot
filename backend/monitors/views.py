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
        agency = serializer.validated_data['agency']
        plan = getattr(agency, 'plan', 'free')
        active_task_count = MonitorTask.objects.filter(agency=agency, is_active=True).count()
        
        limits = {
            'free': 1000,
            'pro': 2000,
            'agency': 5000
        }
        limit = limits.get(plan, 2)
        
        if active_task_count >= limit:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': f"Monitor limit reached for your '{plan}' plan ({limit} tasks). Please upgrade."})
            
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
