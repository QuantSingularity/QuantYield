from django.contrib import admin

from .models import Bond, CallSchedule


class CallScheduleInline(admin.TabularInline):
    model = CallSchedule
    extra = 0
    fields = ["call_date", "call_price"]


@admin.register(Bond)
class BondAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "issuer",
        "isin",
        "bond_type",
        "coupon_rate",
        "maturity_date",
        "currency",
        "credit_rating",
        "sector",
        "created_at",
    ]
    list_filter = [
        "bond_type",
        "coupon_frequency",
        "currency",
        "credit_rating",
        "sector",
    ]
    search_fields = ["name", "issuer", "isin"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [CallScheduleInline]

    fieldsets = [
        (
            "Identification",
            {
                "fields": ["id", "isin", "name", "issuer", "description"],
            },
        ),
        (
            "Economic Terms",
            {
                "fields": [
                    "face_value",
                    "coupon_rate",
                    "maturity_date",
                    "issue_date",
                    "settlement_date",
                ],
            },
        ),
        (
            "Structure",
            {
                "fields": ["coupon_frequency", "bond_type", "day_count"],
            },
        ),
        (
            "Classification",
            {
                "fields": ["currency", "credit_rating", "sector"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(CallSchedule)
class CallScheduleAdmin(admin.ModelAdmin):
    list_display = ["bond", "call_date", "call_price"]
    list_filter = ["call_date"]
    search_fields = ["bond__name", "bond__isin"]
    ordering = ["call_date"]
