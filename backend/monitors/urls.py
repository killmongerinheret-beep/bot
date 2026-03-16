from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgencyViewSet, MonitorTaskViewSet, CheckResultViewSet,
    ProxyViewSet, SiteCredentialViewSet, AgencyLoginView, MyAgencyView,
    get_vatican_tickets,  # ✅ Vatican tickets API
    list_telegram_groups, approve_telegram_group, reject_telegram_group, suspend_telegram_group,  # ✅ Telegram group management
    register_user, login_user, logout_user, verify_session  # ✅ Authentication
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
    path('', include(router.urls)),
]
