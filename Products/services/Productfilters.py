import django_filters
from ..models import Products

class ProductFilter(django_filters.FilterSet):
  category = django_filters.NumberFilter(field_name="category_id")
  brand = django_filters.CharFilter(field_name="brand",lookup_expr="iexact")
  min_price = django_filters.NumberFilter(field_name="price_inr",lookup_expr="gte")
  max_price = django_filters.NumberFilter(field_name="price_inr",lookup_expr="lte")


  class Meta:
    model = Products
    fields =['category','brand','min_price','max_price']

  