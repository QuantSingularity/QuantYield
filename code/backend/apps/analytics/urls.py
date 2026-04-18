from django.urls import path

from . import views

urlpatterns = [
    path("quick-price/", views.quick_price, name="quick-price"),
    path(
        "duration-approximation/",
        views.duration_approximation,
        name="duration-approximation",
    ),
    path("benchmark-spreads/", views.benchmark_spreads, name="benchmark-spreads"),
    path("rolling-volatility/", views.rolling_volatility, name="rolling-volatility"),
    path("yield-history/", views.yield_history, name="yield-history"),
]
