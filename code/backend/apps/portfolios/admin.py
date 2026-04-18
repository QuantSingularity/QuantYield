from django.contrib import admin

from .models import Portfolio, Position


class PositionInline(admin.TabularInline):
    model = Position
    extra = 0
    fields = ["bond", "face_amount", "purchase_price", "purchase_date"]
    autocomplete_fields = ["bond"]
    show_change_link = True


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["name", "currency", "position_count", "created_at"]
    list_filter = ["currency"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [PositionInline]

    def position_count(self, obj):
        return obj.positions.count()

    position_count.short_description = "Positions"


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = [
        "portfolio",
        "bond",
        "face_amount",
        "purchase_price",
        "purchase_date",
    ]
    list_filter = ["portfolio", "bond__sector"]
    search_fields = ["portfolio__name", "bond__name", "bond__isin"]
    autocomplete_fields = ["bond"]
    ordering = ["portfolio", "bond__maturity_date"]
