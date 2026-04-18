from rest_framework import serializers

from .models import CurveDataPoint, YieldCurve


class CurveDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurveDataPoint
        fields = ["id", "tenor", "rate", "instrument"]
        read_only_fields = ["id"]


class YieldCurveSerializer(serializers.ModelSerializer):
    points = CurveDataPointSerializer(many=True, required=True)

    class Meta:
        model = YieldCurve
        fields = [
            "id",
            "name",
            "curve_type",
            "currency",
            "model",
            "as_of_date",
            "points",
            "parameters",
            "r_squared",
            "rmse",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "parameters",
            "r_squared",
            "rmse",
            "created_at",
            "updated_at",
        ]

    def validate_points(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("At least 2 data points are required")
        return value

    def create(self, validated_data):
        points_data = validated_data.pop("points")
        curve = YieldCurve.objects.create(**validated_data)
        for pt in points_data:
            CurveDataPoint.objects.create(curve=curve, **pt)
        return curve

    def update(self, instance, validated_data):
        points_data = validated_data.pop("points", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if points_data is not None:
            instance.points.all().delete()
            for pt in points_data:
                CurveDataPoint.objects.create(curve=instance, **pt)
        return instance


class CurveInterpolateSerializer(serializers.Serializer):
    tenors = serializers.ListField(
        child=serializers.FloatField(min_value=0),
        min_length=1,
    )


class ForwardRateSerializer(serializers.Serializer):
    start_tenor = serializers.FloatField(min_value=0)
    end_tenor = serializers.FloatField(min_value=0.001)

    def validate(self, data):
        if data["end_tenor"] <= data["start_tenor"]:
            raise serializers.ValidationError(
                "end_tenor must be greater than start_tenor"
            )
        return data


class CurveForecastSerializer(serializers.Serializer):
    horizon_days = serializers.IntegerField(default=30, min_value=1, max_value=252)
    model = serializers.CharField(default="lstm")
    confidence_intervals = serializers.BooleanField(default=True)
