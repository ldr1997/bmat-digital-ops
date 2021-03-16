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
            # dsr = models.DSR.objects.get(
            #     territory=territory,
            #     period_start=period_start,
            #     period_end=period_end
            # )
            dsr_ids = models.DSR.objects.filter(
                period_start__gte=period_start
            ).filter(
                period_end__lte=period_end
            ).filter(territory=territory)

            resources = models.Resource.objects.exclude(
                revenue__isnull=True
            ).filter(dsrs__in=dsr_ids).order_by('-revenue')

            revenue_sum = resources.aggregate(sum=Sum('revenue'))['sum']
            revenue_limit = revenue_sum * (number / 100)

            # Get resources whose revenues add up to <number>%
            running_total = 0
            resources_to_return = []

            for resource in resources:
                space_left = revenue_limit - running_total
                if (resource.revenue > space_left): continue

                resources_to_return.append(resource)
                running_total += resource.revenue

                if (running_total >= revenue_limit): break

            to_return = resources_to_return

        except Exception as e:
            print(e)

        return to_return