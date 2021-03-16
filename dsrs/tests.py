from django.test import TestCase
from django.urls import reverse, path
from rest_framework.renderers import JSONRenderer

from .models import *
from .serializers import DSRSerializer, ResourceSerializer

import pycountry
from datetime import datetime, date
from currency_symbols import CurrencySymbols


def generate_dsr_object_to_db(path, period_start, period_end, territory_code2, currency_code):
    # Load currency
    currency_obj = pycountry.currencies.get(alpha_3=currency_code)
    currency_name = currency_obj.name
    currency_symbol = CurrencySymbols.get_symbol(currency_code)

    currency, _ = Currency.objects.get_or_create(
        name=currency_name,
        symbol=currency_symbol,
        code=currency_code
    )

    # Load territory
    territory_obj = pycountry.countries.get(alpha_2=territory_code2)
    territory_name = territory_obj.name
    territory_code3 = territory_obj.alpha_3

    territory, _ = Territory.objects.get_or_create(
        name=territory_name,
        code_2=territory_code2,
        code_3=territory_code3,
        local_currency=currency
    )
    
    return DSR.objects.create(
        path=path,
        period_start=period_start,
        period_end=period_end,
        territory=territory,
        currency=currency
    )


def create_dsr_object(offset=0, offset_territory=True):
    month = 6 + offset
    territories = ['NO', 'ES', 'CH', 'GB']
    currencies = ['NOK', 'EUR', 'CHF', 'GBP']

    if (offset_territory): offset1 = offset
    else: offset1 = 0

    territory_code2 = territories[offset1]
    currency_code = currencies[offset1]

    return generate_dsr_object_to_db(
        path='path/to/dsr.csv',
        period_start=date(2020, month, 1),
        period_end=date(2020, month, 30),
        territory_code2=territory_code2,
        currency_code=currency_code
    )

def create_resources(dsr, usages, revenues):
    for i in range(len(revenues)):
        new_res, created = Resource.objects.get_or_create(
            dsp_id=f"dsp_id{i}",
            title=f"title{i}",
            artists=f"artist{i}",
            usages=usages[i],
            revenue=revenues[i],
        )
        new_res.dsrs.add(dsr)
        new_res.save()


class DSRTests(TestCase):
    
    def get_expected_output_DSR(self, many=True, dsr=None):
        if (many):
            serializer = DSRSerializer(DSR.objects.all(), many=many)
        else:
            serializer = DSRSerializer(dsr, many=many)
        return JSONRenderer().render(serializer.data)


    # endpoint /dsrs/
    def test_list_dsrs_multiple(self):
        for offset in range(2):
            create_dsr_object(offset)

        response = self.client.get(reverse('dsr-list'))
        expected_output = self.get_expected_output_DSR()

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, expected_output)

    def test_list_dsrs_none(self):
        response = self.client.get(reverse('dsr-list'))
        expected_output=b'[]'

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, expected_output)

    def test_list_dsrs_one(self):
        dsr = create_dsr_object()
        response = self.client.get(reverse('dsr-list'))
        expected_output = self.get_expected_output_DSR()

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, expected_output)


    # endpoint /dsrs/{id}
    def test_get_dsr_details(self):
        dsr = create_dsr_object()
        response = self.client.get(reverse('dsr-detail', args=[dsr.id]))
        expected_output = self.get_expected_output_DSR(False, dsr)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, expected_output)

    def test_get_dsr_details_none(self):
        dsr = create_dsr_object()
        response = self.client.get(reverse('dsr-detail', args=[0]))
        expected_output = b'{"detail":"Not found."}'
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.content, expected_output)


class ResourceTests(TestCase):

    # endpoint /resources/percentile/{number}
    
    def get_expected_output_resource(self, many=True, resource=None):
        if (many):
            serializer = ResourceSerializer(
                Resource.objects.all().order_by('-revenue'),
                many=many
            )
        else:
            serializer = ResourceSerializer(resource, many=many)
        return JSONRenderer().render(serializer.data)
    
    def get_expected_output_percentile(self, dsr_ids, cutoff):
        resources = Resource.objects.exclude(
            revenue__isnull=True
        ).filter(dsrs__in=dsr_ids).order_by('-revenue')

        serializer = ResourceSerializer(resources[:cutoff], many=True)
        return JSONRenderer().render(serializer.data)


    def test_get_top_percentile_multiple_dsrs(self):
        dsrs = [create_dsr_object(i, offset_territory=False) for i in [0,1]]
        for dsr in dsrs:
            create_resources(dsr,
                [i for i in range(10)],
                [10 for i in range(10)]
            )
        response = self.client.get(reverse('percentile_url', args=[25]), {
            'territory': dsr.territory.code_2,
            'period_start': dsrs[0].period_start,
            'period_end': dsrs[1].period_end
        })
        
        expected_output = self.get_expected_output_percentile([dsr.id],5)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(expected_output,response.content)


    def test_get_top_percentile(self):
        dsr = create_dsr_object()
        create_resources(dsr,
            [i for i in range(10)],
            [10 for i in range(10)]
        )
        response = self.client.get(reverse('percentile_url', args=[22]), {
            'territory': dsr.territory.code_2,
            'period_start': dsr.period_start,
            'period_end': dsr.period_end
        })
        
        expected_output = self.get_expected_output_percentile([dsr.id],2)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(expected_output,response.content)


    def test_get_top_percentile_100(self):
        dsr = create_dsr_object()
        create_resources(dsr, [0,0,0], [5,1,4])
        response = self.client.get(reverse('percentile_url', args=[100]), {
            'territory': dsr.territory.code_2,
            'period_start': dsr.period_start,
            'period_end': dsr.period_end
        })

        self.assertEquals(response.status_code, 200)
        self.assertEqual(self.get_expected_output_resource(),response.content)


    def test_get_top_percentile_empty(self):
        dsr = create_dsr_object()
        create_resources(dsr, [0,0,0], [5,1,4])
        response = self.client.get(reverse('percentile_url', args=[100]), {
            'territory': dsr.territory.code_2,
            'period_start': dsr.period_end,
            'period_end': dsr.period_start
        })
        
        self.assertEquals(response.status_code, 200)
        self.assertEqual(b'[]',response.content)