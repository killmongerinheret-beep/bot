from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Agency, MonitorTask, CheckResult, Proxy, SiteCredential
from .serializers import (
    AgencySerializer, MonitorTaskSerializer, CheckResultSerializer,
    ProxySerializer, SiteCredentialSerializer
)

class AgencyViewSet(viewsets.ModelViewSet):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

class MonitorTaskViewSet(viewsets.ModelViewSet):
    serializer_class = MonitorTaskSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = MonitorTask.objects.all()
        agency_id = self.request.query_params.get('agency_id')
        if agency_id:
            queryset = queryset.filter(agency_id=agency_id)
        return queryset

    def perform_create(self, serializer):
        agency = serializer.validated_data['agency']
        plan = getattr(agency, 'plan', 'free')
        active_task_count = MonitorTask.objects.filter(agency=agency, is_active=True).count()
        
        limits = {
            'free': 2,
            'pro': 20,
            'agency': 500
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
        queryset = CheckResult.objects.all().order_by('-check_time')
        agency_id = self.request.query_params.get('agency_id')
        task_id = self.request.query_params.get('task')
        
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if agency_id:
            queryset = queryset.filter(task__agency_id=agency_id)
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
        owner_id = request.data.get('owner_id')
        email = request.data.get('email', 'Unknown')
        
        if not owner_id:
            return Response({'error': 'owner_id required'}, status=status.HTTP_400_BAD_REQUEST)
            
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
            'task_limit': {'free': 2, 'pro': 20, 'agency': 500}.get(agency.plan, 2)
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
                    visitors=2
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
