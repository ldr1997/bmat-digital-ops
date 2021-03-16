from rest_framework import viewsets, filters, generics
from django.http import HttpResponse
from django.db.models import Sum
from . import models, serializers
import logging

class DSRViewSet(viewsets.ModelViewSet):
    queryset = models.DSR.objects.all()
    serializer_class = serializers.DSRSerializer

class PercentileView(generics.ListAPIView):
    serializer_class = serializers.ResourceSerializer

    def get_queryset(self):
        number = self.kwargs['number']

        query = self.request.query_params
        territory_code = query.get('territory')
        period_start = query.get("period_start")
        period_end = query.get("period_end")

        to_return = []
        try:
            territory = models.Territory.objects.get(code_2=territory_code)
            dsr = models.DSR.objects.get(territory=territory, period_start=period_start, period_end=period_end)
            resources = models.Resource.objects.exclude(
                revenue__isnull=True
            ).filter(dsrs__in=[dsr.id]).order_by('-revenue')
        
            # percentile = int((number/100) * (len(resources) + 1))
            # to_return = resources[:percentile]
            to_return = resources.aggregate(Sum('field_name'))
        except Exception as e:
            print(f"Not found: {e}")
        return to_return