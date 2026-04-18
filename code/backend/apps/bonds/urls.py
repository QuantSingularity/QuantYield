from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BondViewSet

router = DefaultRouter()
router.register(r"", BondViewSet, basename="bond")

urlpatterns = [
    path("", include(router.urls)),
]
