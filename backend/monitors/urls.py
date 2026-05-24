from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgencyViewSet, MonitorTaskViewSet, CheckResultViewSet,
    ProxyViewSet, SiteCredentialViewSet, AgencyLoginView, MyAgencyView,
    get_vatican_tickets,
    list_telegram_groups, approve_telegram_group, reject_telegram_group, suspend_telegram_group,
    register_user, login_user, logout_user, verify_session,
    list_held_slots, get_available_slots, release_held_slot, checkout_redirect, generate_realtime_epay, generate_test_profiles,
    mark_slot_paid, mark_slot_booked, sync_google_sheets, get_browser_trigger_group, get_browser_pending, get_buyer_profile, get_buyer_card,
    pause_hold_recap, resume_hold_recap, get_agent_config, set_agent_config,
    agent_heartbeat, list_agents, remote_snipe,
    create_test_slot, delete_test_slots,
)
from .admin_views import (
    AdminAgencyViewSet, AdminUserViewSet, AdminTaskViewSet, AdminDashboardViewSet, AdminRecapViewSet
)
from .views_worker import get_pending_snipes, claim_snipe, record_remote_hold, check_payment_signal

router = DefaultRouter()
router.register(r'agencies', AgencyViewSet)
router.register(r'tasks', MonitorTaskViewSet, basename='monitortask')
router.register(r'results', CheckResultViewSet, basename='checkresult')
router.register(r'proxies', ProxyViewSet)
router.register(r'credentials', SiteCredentialViewSet)

# Admin router
admin_router = DefaultRouter()
admin_router.register(r'agencies', AdminAgencyViewSet, basename='admin-agencies')
admin_router.register(r'users', AdminUserViewSet, basename='admin-users')
admin_router.register(r'tasks', AdminTaskViewSet, basename='admin-tasks')
admin_router.register(r'dashboard', AdminDashboardViewSet, basename='admin-dashboard')
admin_router.register(r'recap', AdminRecapViewSet, basename='admin-recap')

urlpatterns = [
    # Authentication
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/verify/', verify_session, name='verify-session'),
    # Admin Panel
    path('admin/', include(admin_router.urls)),
    # Legacy
    path('login/', AgencyLoginView.as_view(), name='agency-login'),
    path('my-agency/', MyAgencyView.as_view(), name='my-agency'),
    path('vatican/tickets/', get_vatican_tickets, name='vatican-tickets'),  # ✅ Vatican tickets API
    # Telegram group management
    path('telegram-groups/', list_telegram_groups, name='list-telegram-groups'),
    path('telegram-groups/<int:group_id>/approve/', approve_telegram_group, name='approve-telegram-group'),
    path('telegram-groups/<int:group_id>/reject/', reject_telegram_group, name='reject-telegram-group'),
    path('telegram-groups/<int:group_id>/suspend/', suspend_telegram_group, name='suspend-telegram-group'),
    path('holds/', list_held_slots, name='list-held-slots'),
    path('available-slots/', get_available_slots, name='available-slots'),
    path('holds/<int:hold_id>/release/', release_held_slot, name='release-held-slot'),
    path('holds/<int:hold_id>/checkout/', checkout_redirect, name='checkout-redirect'),
    path('holds/<int:hold_id>/pause-recap/', pause_hold_recap, name='pause-hold-recap'),
    path('holds/<int:hold_id>/resume-recap/', resume_hold_recap, name='resume-hold-recap'),
    path('mark-paid/', mark_slot_paid, name='mark-slot-paid'),
    path('slots/<int:slot_id>/mark-booked/', mark_slot_booked, name='mark-slot-booked'),
    path('google-sheets/sync/', sync_google_sheets, name='sync-google-sheets'),
    path('browser-trigger-group/', get_browser_trigger_group, name='browser-trigger-group'),
    path('browser-pending/', get_browser_pending, name='browser-pending'),
    path('agent-config/', get_agent_config, name='agent-config'),
    path('agent-config/set/', set_agent_config, name='set-agent-config'),
    path('agent-heartbeat/', agent_heartbeat, name='agent-heartbeat'),
    path('agents/', list_agents, name='list-agents'),
    path('remote-snipe/', remote_snipe, name='remote-snipe'),
    path('buyer-profile/', get_buyer_profile, name='buyer-profile'),
    path('buyer-card/', get_buyer_card, name='buyer-card'),
    path('epay/generate/', generate_realtime_epay, name='generate-realtime-epay'),
    path('test/profiles/', generate_test_profiles, name='generate-test-profiles'),
    path('test/create-slot/', create_test_slot, name='create-test-slot'),
    path('test/delete-slots/', delete_test_slots, name='delete-test-slots'),
    
    # Distributed Worker API
    path('worker/tasks/', get_pending_snipes, name='worker-tasks'),
    path('worker/claim/<int:task_id>/', claim_snipe, name='worker-claim'),
    path('worker/hold/record/', record_remote_hold, name='worker-hold-record'),
    path('worker/hold/<int:hold_id>/signal/', check_payment_signal, name='worker-hold-signal'),

    path('', include(router.urls)),
]
