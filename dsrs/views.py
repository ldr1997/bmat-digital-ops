from rest_framework import viewsets, generics
from django.db.models import Sum
from. models import DSR
from .serializers import DSRSerializer, ResourceSerializer
# from . import models, serializers
from .util import get_top_percentile


class DSRViewSet(viewsets.ModelViewSet):
    queryset = DSR.objects.all()
    serializer_class = DSRSerializer


class PercentileView(generics.ListAPIView):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        number = self.kwargs['number']

        query = self.request.query_params
        territory_code = query.get('territory')
        period_start = query.get("period_start")
        period_end = query.get("period_end")

        return get_top_percentile(
            number,
            territory_code,
            period_start,
            period_end
        )
