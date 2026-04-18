from apps.bonds.serializers import BondAnalyticsSerializer
from rest_framework import serializers

from .models import Portfolio, Position


class PositionSerializer(serializers.ModelSerializer):
    bond_detail = BondAnalyticsSerializer(source="bond", read_only=True)

    class Meta:
        model = Position
        fields = [
            "id",
            "bond",
            "bond_detail",
            "face_amount",
            "purchase_price",
            "purchase_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "bond_detail", "created_at", "updated_at"]


class PositionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["bond", "face_amount", "purchase_price", "purchase_date", "notes"]


class PortfolioSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    position_count = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "description",
            "currency",
            "positions",
            "position_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "positions",
            "position_count",
            "created_at",
            "updated_at",
        ]

    def get_position_count(self, obj):
        return obj.positions.count()


class PortfolioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ["name", "description", "currency"]


class ScenarioShiftSerializer(serializers.Serializer):
    parallel_shift_bps = serializers.FloatField(default=0.0)
    twist_short_bps = serializers.FloatField(default=0.0)
    twist_long_bps = serializers.FloatField(default=0.0)
    credit_spread_shift_bps = serializers.FloatField(default=0.0)


class VaRRequestSerializer(serializers.Serializer):
    confidence_level = serializers.FloatField(
        default=0.99, min_value=0.9, max_value=0.9999
    )
    holding_period_days = serializers.IntegerField(
        default=1, min_value=1, max_value=252
    )
    method = serializers.ChoiceField(
        choices=["historical", "parametric"], default="historical"
    )
    lookback_days = serializers.IntegerField(default=252, min_value=21, max_value=2520)
