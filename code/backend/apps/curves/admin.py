from django.contrib import admin

from .models import CurveDataPoint, YieldCurve


class CurveDataPointInline(admin.TabularInline):
    model = CurveDataPoint
    extra = 0
    fields = ["tenor", "rate", "instrument"]


@admin.register(YieldCurve)
class YieldCurveAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model",
        "curve_type",
        "currency",
        "as_of_date",
        "r_squared",
        "rmse",
    ]
    list_filter = ["model", "curve_type", "currency"]
    search_fields = ["name"]
    ordering = ["-as_of_date"]
    readonly_fields = [
        "id",
        "parameters",
        "r_squared",
        "rmse",
        "created_at",
        "updated_at",
    ]
    inlines = [CurveDataPointInline]


@admin.register(CurveDataPoint)
class CurveDataPointAdmin(admin.ModelAdmin):
    list_display = ["curve", "tenor", "rate", "instrument"]
    list_filter = ["instrument"]
    search_fields = ["curve__name"]
    ordering = ["curve", "tenor"]
