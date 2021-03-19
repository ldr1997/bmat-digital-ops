from rest_framework import viewsets, generics
from django.db.models import Sum
from . import models, serializers


def get_top_percentile(number, territory_code, period_start, period_end):
    try:
        territory = models.Territory.objects.get(code_2=territory_code)

        dsr_ids = models.DSR.objects.filter(
            period_start__gte=period_start
        ).filter(
            period_end__lte=period_end
        ).filter(territory=territory)
    except:
        return []

    resources = models.Resource.objects.exclude(
        revenue__isnull=True
    ).filter(dsrs__in=dsr_ids).order_by('-revenue')

    if(len(resources) == 0):
        return []

    revenue_sum = resources.aggregate(sum=Sum('revenue'))['sum']
    revenue_limit = revenue_sum * (number / 100)

    # Get resources whose revenues add up to <number>%
    running_total = 0
    resources_to_return = []

    for resource in resources:
        space_left = revenue_limit - running_total
        if (resource.revenue > space_left):
            continue

        resources_to_return.append(resource)
        running_total += resource.revenue

        if (running_total >= revenue_limit):
            break

    return resources_to_return
