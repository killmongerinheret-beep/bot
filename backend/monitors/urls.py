from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgencyViewSet, MonitorTaskViewSet, CheckResultViewSet,
    ProxyViewSet, SiteCredentialViewSet, AgencyLoginView, MyAgencyView,
    get_vatican_tickets  # ✅ NEW
)

router = DefaultRouter()
router.register(r'agencies', AgencyViewSet)
router.register(r'tasks', MonitorTaskViewSet, basename='monitortask')
router.register(r'results', CheckResultViewSet, basename='checkresult')
router.register(r'proxies', ProxyViewSet)
router.register(r'credentials', SiteCredentialViewSet)

urlpatterns = [
    path('login/', AgencyLoginView.as_view(), name='agency-login'),
    path('my-agency/', MyAgencyView.as_view(), name='my-agency'),
    path('vatican/tickets/', get_vatican_tickets, name='vatican-tickets'),  # ✅ NEW
    path('', include(router.urls)),
]
