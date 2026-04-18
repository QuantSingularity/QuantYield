"""
QuantYield — Bond Models
Full Django ORM models for bonds with proper persistence.
"""

import re
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CouponFrequency(models.TextChoices):
    ANNUAL = "annual", "Annual"
    SEMIANNUAL = "semiannual", "Semi-Annual"
    QUARTERLY = "quarterly", "Quarterly"
    MONTHLY = "monthly", "Monthly"
    ZERO = "zero", "Zero (Discount)"


class BondType(models.TextChoices):
    FIXED = "fixed", "Fixed Rate"
    FLOATING = "floating", "Floating Rate"
    ZERO_COUPON = "zero_coupon", "Zero Coupon"
    INFLATION_LINKED = "inflation_linked", "Inflation Linked"
    CALLABLE = "callable", "Callable"


class DayCountConvention(models.TextChoices):
    ACT_ACT = "actual/actual", "Actual/Actual"
    ACT_360 = "actual/360", "Actual/360"
    ACT_365 = "actual/365", "Actual/365"
    THIRTY_360 = "30/360", "30/360"


class Bond(models.Model):
    """
    Persisted bond instrument.  All analytics are computed on-the-fly from
    stored terms; only mutable metadata (rating, sector, name) can be patched.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Identification ─────────────────────────────────────────────────────────
    isin = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        help_text="ISO 6166 ISIN (2-letter country code + 9 alphanumeric + check digit)",
    )
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)

    # ── Economic Terms ─────────────────────────────────────────────────────────
    face_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(0.000001)],
        default=1000.0,
    )
    coupon_rate = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Annual coupon rate as decimal (e.g. 0.05 = 5%)",
    )
    maturity_date = models.DateField()
    issue_date = models.DateField()
    settlement_date = models.DateField(blank=True, null=True)

    # ── Structure ──────────────────────────────────────────────────────────────
    coupon_frequency = models.CharField(
        max_length=20,
        choices=CouponFrequency.choices,
        default=CouponFrequency.SEMIANNUAL,
    )
    bond_type = models.CharField(
        max_length=20,
        choices=BondType.choices,
        default=BondType.FIXED,
    )
    day_count = models.CharField(
        max_length=20,
        choices=DayCountConvention.choices,
        default=DayCountConvention.ACT_ACT,
    )

    # ── Classification ─────────────────────────────────────────────────────────
    currency = models.CharField(max_length=3, default="USD")
    credit_rating = models.CharField(max_length=10, blank=True, null=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["issuer"]),
            models.Index(fields=["bond_type"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["credit_rating"]),
            models.Index(fields=["currency"]),
            models.Index(fields=["maturity_date"]),
        ]
        verbose_name = "Bond"
        verbose_name_plural = "Bonds"

    def __str__(self):
        return f"{self.name} ({self.issuer}) — {self.maturity_date}"

    def clean(self):
        if self.maturity_date and self.issue_date:
            if self.maturity_date <= self.issue_date:
                raise ValidationError("maturity_date must be strictly after issue_date")
        if self.isin:
            v = self.isin.upper().strip()
            if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", v):
                raise ValidationError(
                    "ISIN must be 12 characters: 2-letter country code, "
                    "9 alphanumeric characters, and 1 numeric check digit"
                )
        if self.bond_type == BondType.ZERO_COUPON and self.coupon_rate != 0:
            raise ValidationError("Zero coupon bonds must have coupon_rate = 0")


class CallSchedule(models.Model):
    """A single call date / call price entry on a callable bond."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bond = models.ForeignKey(
        Bond, on_delete=models.CASCADE, related_name="call_schedule"
    )
    call_date = models.DateField()
    call_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=100.0,
        validators=[MinValueValidator(0.0001)],
        help_text="Call price as percentage of face value (e.g. 102.0 = 102%)",
    )

    class Meta:
        ordering = ["call_date"]
        unique_together = [("bond", "call_date")]
        verbose_name = "Call Schedule Entry"
        verbose_name_plural = "Call Schedule"

    def __str__(self):
        return f"{self.bond.name} callable at {self.call_price}% on {self.call_date}"
