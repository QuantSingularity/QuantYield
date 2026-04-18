from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_view, name="root"),
    path("health/", views.health_view, name="health"),
]
