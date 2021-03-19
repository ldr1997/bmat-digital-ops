from django.core.management.base import BaseCommand
from django.db import transaction

from .models import Currency, Territory, DSR, Resource

import os
from datetime import datetime
import json

import pandas as pd
from numpy import isnan
import pycountry
from currency_symbols import CurrencySymbols
from google_currency import convert

from tqdm import tqdm


class Command(BaseCommand):
    help = 'Load data located in "data" folder.'

    def handle(self, *args, **options):
        DSR_ROOT = 'data/'
        dsrs = os.listdir(DSR_ROOT)

        for dsr_file in dsrs:
            path = DSR_ROOT + dsr_file
            dsr_info = dsr_file.split('.')[0]
            split_filename = dsr_info.split('_')
            territory_code2 = split_filename[2]
            currency_code = split_filename[3]
            period = split_filename[4]

            # Load currency
            currency_obj = pycountry.currencies.get(alpha_3=currency_code)
            currency_name = currency_obj.name
            currency_symbol = CurrencySymbols.get_symbol(currency_code)

            currency, created = Currency.objects.get_or_create(
                name=currency_name,
                symbol=currency_symbol,
                code=currency_code
            )

            # get conversion rate
            conversion_rate = 1
            if (currency_code != 'EUR'):
                conversion_str = convert(currency_code, 'EUR', 1)
                conversion_rate = float(json.loads(conversion_str)['amount'])
                print(f"""Conversion rate of {currency_code}"""
                      """to EUR is {conversion_rate}.""")

            # Load territory
            territory_obj = pycountry.countries.get(alpha_2=territory_code2)
            territory_name = territory_obj.name
            territory_code3 = territory_obj.alpha_3

            territory, created = Territory.objects.get_or_create(
                name=territory_name,
                code_2=territory_code2,
                code_3=territory_code3,
                local_currency=currency
            )

            # Compute period
            period_split = period.split('-')
            period_start = datetime.strptime(period_split[0], '%Y%m%d')
            period_end = datetime.strptime(period_split[1], '%Y%m%d')

            # Load DSR
            dsr, created = DSR.objects.get_or_create(
                path=path,
                period_start=period_start,
                period_end=period_end,
                territory=territory,
                currency=currency
            )

            if(dsr.status == 'failed'):
                if (not created):
                    Resource.objects.filter(dsrs__in=[dsr.id]).delete()
                dsr_data = pd.read_csv(path, compression='gzip', sep='\t')
                load_resources(dsr_data, dsr, conversion_rate)


@transaction.atomic
def load_resources(dsr_data, dsr, conversion_rate):
    for i, row in tqdm(dsr_data.iterrows(), desc=str(dsr),
                       total=dsr_data.shape[0]):
        row_dict = {}
        for k, v in row.items():
            if k in ['dsp_id', 'dsrs']:
                continue
            elif k in ['title', 'artists', 'isrc'] and type(v) != str:
                v = ""
            elif k in ['usages', 'revenue'] and isnan(v):
                continue
            elif k == 'revenue':
                v *= conversion_rate
            row_dict.update({k: v})

        resource, _ = Resource.objects.get_or_create(dsp_id=row['dsp_id'])
        for k, v in row_dict.items():
            if getattr(resource, k) is None and v is not None:
                setattr(resource, k, v)

        resource.dsrs.add(dsr)
        resource.save()

    dsr.status = "ingested"
    dsr.save()
