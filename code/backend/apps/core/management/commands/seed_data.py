"""
Management command: seed_data
Populates the database with representative bonds, portfolios, and yield curves
for development and demo purposes.
"""

import logging
from datetime import date

from django.core.management.base import BaseCommand

logger = logging.getLogger("quantyield")


class Command(BaseCommand):
    help = "Seed the database with representative fixed income data for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true", help="Clear existing data before seeding"
        )

    def handle(self, *args, **options):
        from apps.bonds.models import Bond, CallSchedule
        from apps.curves.models import CurveDataPoint, YieldCurve
        from apps.portfolios.models import Portfolio, Position

        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Position.objects.all().delete()
            Portfolio.objects.all().delete()
            CallSchedule.objects.all().delete()
            Bond.objects.all().delete()
            CurveDataPoint.objects.all().delete()
            YieldCurve.objects.all().delete()

        self.stdout.write("Seeding bonds...")
        bonds = self._seed_bonds()

        self.stdout.write("Seeding portfolios...")
        self._seed_portfolios(bonds)

        self.stdout.write("Seeding yield curves...")
        self._seed_curves()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Seeded {len(bonds)} bonds, 2 portfolios, 3 yield curves"
            )
        )

    def _seed_bonds(self):
        from apps.bonds.models import Bond, CallSchedule

        bond_data = [
            dict(
                name="US Treasury 4.625% 2026",
                issuer="US Treasury",
                isin="US912828YK00",
                face_value=1000,
                coupon_rate=0.04625,
                maturity_date=date(2026, 2, 15),
                issue_date=date(2023, 2, 15),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="AAA",
                sector="Government",
            ),
            dict(
                name="Apple 3.85% 2043",
                issuer="Apple Inc",
                isin="US037833AK68",
                face_value=1000,
                coupon_rate=0.0385,
                maturity_date=date(2043, 8, 4),
                issue_date=date(2023, 8, 4),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="AA+",
                sector="Technology",
            ),
            dict(
                name="JPMorgan Chase 5.0% 2028",
                issuer="JPMorgan Chase",
                isin="US46625HRL53",
                face_value=1000,
                coupon_rate=0.05,
                maturity_date=date(2028, 8, 1),
                issue_date=date(2023, 8, 1),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="A-",
                sector="Financials",
            ),
            dict(
                name="Microsoft 2.921% 2052",
                issuer="Microsoft Corp",
                isin="US594918BU11",
                face_value=1000,
                coupon_rate=0.02921,
                maturity_date=date(2052, 3, 17),
                issue_date=date(2022, 3, 17),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="AAA",
                sector="Technology",
            ),
            dict(
                name="Ford Motor 6.1% 2032",
                issuer="Ford Motor Credit",
                face_value=1000,
                coupon_rate=0.061,
                maturity_date=date(2032, 8, 19),
                issue_date=date(2022, 8, 19),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="BB+",
                sector="Consumer Discretionary",
            ),
            dict(
                name="US Treasury 0% STRIP 2030",
                issuer="US Treasury",
                face_value=1000,
                coupon_rate=0.0,
                maturity_date=date(2030, 5, 15),
                issue_date=date(2020, 5, 15),
                coupon_frequency="zero",
                bond_type="zero_coupon",
                day_count="actual/actual",
                currency="USD",
                credit_rating="AAA",
                sector="Government",
            ),
            dict(
                name="Verizon Callable 4.5% 2033",
                issuer="Verizon Communications",
                face_value=1000,
                coupon_rate=0.045,
                maturity_date=date(2033, 9, 15),
                issue_date=date(2023, 9, 15),
                coupon_frequency="semiannual",
                bond_type="callable",
                day_count="actual/actual",
                currency="USD",
                credit_rating="BBB+",
                sector="Telecommunications",
            ),
            dict(
                name="Exxon Mobil 3.482% 2051",
                issuer="Exxon Mobil",
                face_value=1000,
                coupon_rate=0.03482,
                maturity_date=date(2051, 3, 19),
                issue_date=date(2021, 3, 19),
                coupon_frequency="semiannual",
                bond_type="fixed",
                day_count="actual/actual",
                currency="USD",
                credit_rating="AA-",
                sector="Energy",
            ),
        ]

        created_bonds = []
        for data in bond_data:
            bond, created = Bond.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            if created:
                self.stdout.write(f"  + {bond.name}")
            # Add call schedule for callable bond
            if bond.bond_type == "callable" and not bond.call_schedule.exists():
                for i, (yr, px) in enumerate(
                    [(2026, 102.0), (2027, 101.5), (2028, 101.0), (2029, 100.5)]
                ):
                    CallSchedule.objects.create(
                        bond=bond,
                        call_date=date(yr, 9, 15),
                        call_price=px,
                    )
            created_bonds.append(bond)

        return created_bonds

    def _seed_portfolios(self, bonds):
        from apps.portfolios.models import Portfolio, Position

        # Core government portfolio
        gov_port, _ = Portfolio.objects.get_or_create(
            name="Core Government Portfolio",
            defaults={
                "description": "High-quality sovereign and agency bonds",
                "currency": "USD",
            },
        )
        gov_bonds = [b for b in bonds if b.sector == "Government"]
        for bond in gov_bonds:
            Position.objects.get_or_create(
                portfolio=gov_port,
                bond=bond,
                defaults={
                    "face_amount": 100000,
                    "purchase_price": float(bond.face_value),
                    "purchase_date": date(2023, 9, 1),
                },
            )

        # Mixed credit portfolio
        mixed_port, _ = Portfolio.objects.get_or_create(
            name="Investment Grade Mixed Portfolio",
            defaults={
                "description": "Diversified investment grade credit",
                "currency": "USD",
            },
        )
        for bond in bonds[:6]:
            Position.objects.get_or_create(
                portfolio=mixed_port,
                bond=bond,
                defaults={
                    "face_amount": 50000,
                    "purchase_price": float(bond.face_value) * 0.98,
                    "purchase_date": date(2023, 6, 1),
                },
            )

    def _seed_curves(self):
        from apps.curves.models import CurveDataPoint, YieldCurve
        from services.curve_builder import bootstrap_spot_rates, fit_nelson_siegel
        from services.schemas import CurvePointSchema

        treasury_points = [
            (0.0833, 0.0526),
            (0.25, 0.0532),
            (0.5, 0.0530),
            (1.0, 0.0515),
            (2.0, 0.0489),
            (3.0, 0.0472),
            (5.0, 0.0456),
            (7.0, 0.0452),
            (10.0, 0.0445),
            (20.0, 0.0471),
            (30.0, 0.0459),
        ]

        curve_configs = [
            ("US Treasury Nelson-Siegel", "nelson_siegel", "government"),
            ("US Treasury Bootstrap", "bootstrap", "government"),
            ("US Treasury Cubic Spline", "cubic_spline", "government"),
        ]

        pts = [CurvePointSchema(tenor=t, rate=r) for t, r in treasury_points]

        for name, model, curve_type in curve_configs:
            curve, created = YieldCurve.objects.get_or_create(
                name=name,
                defaults={
                    "curve_type": curve_type,
                    "currency": "USD",
                    "model": model,
                    "as_of_date": date.today(),
                },
            )
            if created:
                for tenor, rate in treasury_points:
                    CurveDataPoint.objects.create(
                        curve=curve, tenor=tenor, rate=rate, instrument="FRED"
                    )
                # Fit and save parameters
                if model == "nelson_siegel":
                    params, r2, rmse = fit_nelson_siegel(pts)
                    curve.parameters = params.model_dump()
                    curve.r_squared = r2
                    curve.rmse = rmse
                elif model == "bootstrap":
                    spot_rates = bootstrap_spot_rates(pts)
                    curve.parameters = {
                        "spot_rates": {str(k): v for k, v in spot_rates.items()}
                    }
                    curve.r_squared = 1.0
                    curve.rmse = 0.0
                else:
                    curve.parameters = {"model": "cubic_spline_fitted"}
                    curve.r_squared = 1.0
                    curve.rmse = 0.0
                curve.save()
                self.stdout.write(f"  + {name}")
