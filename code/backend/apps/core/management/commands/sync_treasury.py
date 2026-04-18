"""
Management command: sync_treasury
Refreshes the Treasury curve cache and optionally saves a snapshot to the DB.
Can be run as a cron job every 5 minutes during market hours.
"""

import asyncio
from datetime import date

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Refresh the live Treasury curve cache from FRED and optionally save a DB snapshot"

    def add_arguments(self, parser):
        parser.add_argument(
            "--save-snapshot",
            action="store_true",
            help="Save today's curve as a YieldCurve record in the database",
        )

    def handle(self, *args, **options):
        from services.curve_builder import bootstrap_spot_rates, fit_nelson_siegel
        from services.data_feed import TREASURY_CURVE_CACHE_KEY, fetch_treasury_curve
        from services.schemas import CurvePointSchema

        self.stdout.write("Fetching live Treasury curve from FRED...")

        # Invalidate cache to force a fresh fetch
        cache.delete(TREASURY_CURVE_CACHE_KEY)

        points = asyncio.run(fetch_treasury_curve())
        self.stdout.write(f"  ✓ Fetched {len(points)} Treasury points")

        if options["save_snapshot"]:
            from apps.curves.models import CurveDataPoint, YieldCurve

            curve_pts = [CurvePointSchema(**p) for p in points]
            ns_params, r2, rmse = fit_nelson_siegel(curve_pts)
            bootstrap_spot_rates(curve_pts)

            today = date.today()
            curve_name = f"US Treasury Snapshot {today.isoformat()}"

            curve, created = YieldCurve.objects.get_or_create(
                name=curve_name,
                as_of_date=today,
                defaults={
                    "curve_type": "government",
                    "currency": "USD",
                    "model": "nelson_siegel",
                    "parameters": ns_params.model_dump(),
                    "r_squared": r2,
                    "rmse": rmse,
                },
            )

            if created:
                for pt in points:
                    CurveDataPoint.objects.create(
                        curve=curve,
                        tenor=pt["tenor"],
                        rate=pt["rate"],
                        instrument=pt.get("instrument", "FRED"),
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Saved snapshot: {curve_name}")
                )
            else:
                self.stdout.write(
                    f"  — Snapshot already exists for {today.isoformat()}"
                )

        self.stdout.write(self.style.SUCCESS("Treasury curve sync complete"))
