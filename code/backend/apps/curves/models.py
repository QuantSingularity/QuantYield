"""
QuantYield — Yield Curve Models
"""

import uuid

from django.db import models


class CurveModel(models.TextChoices):
    NELSON_SIEGEL = "nelson_siegel", "Nelson-Siegel"
    SVENSSON = "svensson", "Svensson"
    BOOTSTRAP = "bootstrap", "Bootstrap"
    CUBIC_SPLINE = "cubic_spline", "Cubic Spline"


class CurveType(models.TextChoices):
    GOVERNMENT = "government", "Government"
    SWAP = "swap", "Swap"
    CORPORATE = "corporate", "Corporate"
    OIS = "ois", "OIS"


class YieldCurve(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    curve_type = models.CharField(
        max_length=20, choices=CurveType.choices, default=CurveType.GOVERNMENT
    )
    currency = models.CharField(max_length=3, default="USD")
    model = models.CharField(
        max_length=20, choices=CurveModel.choices, default=CurveModel.NELSON_SIEGEL
    )
    as_of_date = models.DateField()
    # Fitted parameters stored as JSON
    parameters = models.JSONField(default=dict, blank=True)
    r_squared = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-as_of_date", "-created_at"]
        indexes = [
            models.Index(fields=["as_of_date"]),
            models.Index(fields=["curve_type"]),
            models.Index(fields=["currency"]),
        ]
        verbose_name = "Yield Curve"
        verbose_name_plural = "Yield Curves"

    def __str__(self):
        return f"{self.name} ({self.model}) — {self.as_of_date}"


class CurveDataPoint(models.Model):
    """Individual par-rate point that was used to fit the curve."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curve = models.ForeignKey(
        YieldCurve, on_delete=models.CASCADE, related_name="points"
    )
    tenor = models.FloatField(help_text="Tenor in years")
    rate = models.FloatField(help_text="Par yield / rate as decimal")
    instrument = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["tenor"]
        unique_together = [("curve", "tenor")]
        verbose_name = "Curve Data Point"

    def __str__(self):
        return f"{self.curve.name} @ {self.tenor}Y = {self.rate:.4%}"
