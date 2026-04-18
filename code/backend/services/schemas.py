"""
QuantYield — Service Layer Schemas
Plain dataclasses used by the service layer (pricing, risk, curve_builder, etc.).
These are decoupled from Django ORM models so services remain framework-agnostic.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

# ── Bond ──────────────────────────────────────────────────────────────────────


@dataclass
class CallDateSchema:
    call_date: date
    call_price: float = 100.0  # as % of face value


@dataclass
class BondSchema:
    name: str
    issuer: str
    face_value: float
    coupon_rate: float
    maturity_date: date
    issue_date: date
    coupon_frequency: str = "semiannual"
    bond_type: str = "fixed"
    day_count: str = "actual/actual"
    currency: str = "USD"
    credit_rating: Optional[str] = None
    sector: Optional[str] = None
    settlement_date: Optional[date] = None
    call_schedule: Optional[list] = None  # list[CallDateSchema]
    isin: Optional[str] = None


# ── Yield Curve ───────────────────────────────────────────────────────────────


@dataclass
class CurvePointSchema:
    tenor: float
    rate: float
    instrument: Optional[str] = None


@dataclass
class NelsonSiegelParams:
    beta0: float
    beta1: float
    beta2: float
    lambda1: float

    def model_dump(self):
        return {
            "beta0": self.beta0,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "lambda1": self.lambda1,
        }


@dataclass
class SvenssonParams:
    beta0: float
    beta1: float
    beta2: float
    beta3: float
    lambda1: float
    lambda2: float

    def model_dump(self):
        return {
            "beta0": self.beta0,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "beta3": self.beta3,
            "lambda1": self.lambda1,
            "lambda2": self.lambda2,
        }


# ── Portfolio / Risk ──────────────────────────────────────────────────────────


@dataclass
class ScenarioShiftSchema:
    parallel_shift_bps: float = 0.0
    twist_short_bps: float = 0.0
    twist_long_bps: float = 0.0
    credit_spread_shift_bps: float = 0.0


@dataclass
class ScenarioResultSchema:
    scenario_name: str
    pnl: float
    pnl_pct: float
    new_portfolio_value: float
    duration_contribution: float
    convexity_contribution: float

    def model_dump(self):
        return {
            "scenario_name": self.scenario_name,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "new_portfolio_value": self.new_portfolio_value,
            "duration_contribution": self.duration_contribution,
            "convexity_contribution": self.convexity_contribution,
        }
