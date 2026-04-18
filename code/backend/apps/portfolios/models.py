"""
QuantYield — Portfolio Models
"""

import uuid

from apps.bonds.models import Bond
from django.core.validators import MinValueValidator
from django.db import models


class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["currency"]),
            models.Index(fields=["name"]),
        ]
        verbose_name = "Portfolio"
        verbose_name_plural = "Portfolios"

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Position(models.Model):
    """A single bond holding within a portfolio."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="positions"
    )
    bond = models.ForeignKey(Bond, on_delete=models.PROTECT, related_name="positions")
    face_amount = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        validators=[MinValueValidator(0.0001)],
        help_text="Notional face amount held",
    )
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="Clean price at purchase (per unit of face value)",
    )
    purchase_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["portfolio", "bond__maturity_date"]
        unique_together = [("portfolio", "bond")]
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"{self.portfolio.name} | {self.bond.name} × {self.face_amount}"
