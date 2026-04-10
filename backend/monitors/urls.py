from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgencyViewSet, MonitorTaskViewSet, CheckResultViewSet,
    ProxyViewSet, SiteCredentialViewSet, AgencyLoginView, MyAgencyView,
    get_vatican_tickets,
    list_telegram_groups, approve_telegram_group, reject_telegram_group, suspend_telegram_group,
    register_user, login_user, logout_user, verify_session,
    list_held_slots, release_held_slot, checkout_redirect, generate_realtime_epay, generate_test_profiles,
    mark_slot_paid, get_browser_trigger_group, get_browser_pending,
)
from .admin_views import (
    AdminAgencyViewSet, AdminUserViewSet, AdminTaskViewSet, AdminDashboardViewSet
)

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
    path('holds/<int:hold_id>/release/', release_held_slot, name='release-held-slot'),
    path('holds/<int:hold_id>/checkout/', checkout_redirect, name='checkout-redirect'),
    path('mark-paid/', mark_slot_paid, name='mark-slot-paid'),
    path('browser-trigger-group/', get_browser_trigger_group, name='browser-trigger-group'),
    path('browser-pending/', get_browser_pending, name='browser-pending'),
    path('epay/generate/', generate_realtime_epay, name='generate-realtime-epay'),
    path('test/profiles/', generate_test_profiles, name='generate-test-profiles'),
    path('', include(router.urls)),
]
