import django_filters

from .models import Bond, BondType, CouponFrequency


class BondFilter(django_filters.FilterSet):
    issuer = django_filters.CharFilter(lookup_expr="icontains")
    sector = django_filters.CharFilter(lookup_expr="icontains")
    currency = django_filters.CharFilter(lookup_expr="iexact")
    credit_rating = django_filters.CharFilter(lookup_expr="iexact")
    bond_type = django_filters.ChoiceFilter(choices=BondType.choices)
    coupon_frequency = django_filters.ChoiceFilter(choices=CouponFrequency.choices)

    maturity_from = django_filters.DateFilter(
        field_name="maturity_date", lookup_expr="gte"
    )
    maturity_to = django_filters.DateFilter(
        field_name="maturity_date", lookup_expr="lte"
    )

    coupon_min = django_filters.NumberFilter(
        field_name="coupon_rate", lookup_expr="gte"
    )
    coupon_max = django_filters.NumberFilter(
        field_name="coupon_rate", lookup_expr="lte"
    )

    class Meta:
        model = Bond
        fields = [
            "issuer",
            "sector",
            "currency",
            "credit_rating",
            "bond_type",
            "coupon_frequency",
            "maturity_from",
            "maturity_to",
            "coupon_min",
            "coupon_max",
        ]
