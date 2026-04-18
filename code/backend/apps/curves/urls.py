from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import YieldCurveViewSet

router = DefaultRouter()
router.register(r"", YieldCurveViewSet, basename="curve")

urlpatterns = [
    path("", include(router.urls)),
]
