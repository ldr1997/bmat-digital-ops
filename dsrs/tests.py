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


def create_dsr_object(offset=0):
    month = 6 + offset
    territory_code2 = ['NO', 'ES', 'CH', 'GB'][offset]
    currency_code = ['NOK', 'EUR', 'CHF', 'GBP'][offset]

    return generate_dsr_object_to_db(
        path='path/to/dsr.csv',
        period_start=date(2020, month, 1),
        period_end=date(2020, month, 30),
        territory_code2=territory_code2,
        currency_code=currency_code
    )


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
    def test_get_top_percentile(self):
        dsr = create_dsr_object()
        
        self.assertEqual(1,1)