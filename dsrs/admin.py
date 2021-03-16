from django.contrib import admin
from django.core.management import call_command
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.db import transaction

from .models import *

def delete_dsr_and_resources(modeladmin, request, queryset):
    for dsr in queryset:
        delete_resources_under_dsr(dsr.id)
        DSR.objects.get(id=dsr.id).delete()
delete_dsr_and_resources.short_description = "Delete DSR and all resources"

@transaction.atomic
def delete_resources_under_dsr(dsr_id):
    dsr_resources = Resource.objects.filter(dsrs__in=[dsr_id])
    to_be_deleted = []
    for resource in dsr_resources:
        if (resource.dsrs.count() == 1):
            to_be_deleted.append(resource.dsp_id)
            
    dsr_resources.filter(dsp_id__in=to_be_deleted).delete()


# Register your models here.
class TerritoryAdmin(admin.ModelAdmin):
    list_display=('name', 'code_2', 'code_3', 'local_currency')

class CurrencyAdmin(admin.ModelAdmin):
    list_display=('name', 'symbol', 'code')

class DSRAdmin(admin.ModelAdmin):
    actions = [delete_dsr_and_resources]
    change_list_template = "dsr_changelist.html"
    list_display=('territory', 'period_start', 'period_end', 'currency', 'status', 'dsr_actions')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('reload/', self.load_DSRs),
            path(r'remove_all/<int:dsr_id>', self.delete_DSR, name='remove-all-dsr')
        ]
        return my_urls + urls

    def load_DSRs(self, request):
        call_command('load')
        self.message_user(request, "Reloaded DSRs!")
        return HttpResponseRedirect('../')

    def delete_DSR(self, request, **kwargs):
        if request.POST.get('post'):
            dsr_id = kwargs['dsr_id']
            delete_resources_under_dsr(dsr_id)
            DSR.objects.get(id=dsr_id).delete()

            self.message_user(request, f"Deleted DSR {dsr_id}!")
            return HttpResponseRedirect('../')
        else:
            request.current_app = self.admin_site.name
            return TemplateResponse(request, "dsr_delete_confirmation.html")

    def dsr_actions(self, obj):
        record_url = (
            reverse("admin:dsrs_resource_changelist")
            + f"?dsr__id__exact={obj.pk}"
        )
        delete_url = (
            reverse('admin:remove-all-dsr', args=(obj.pk,))
        )
        return format_html(
            '<a class="button" href="{}">View DSR</a>&nbsp;'
            '<a class="button", href="{}">Delete</a>',
            record_url, delete_url
        )


class ResourceAdmin(admin.ModelAdmin):
    list_display=('dsp_id', 'title', 'artists', 'isrc', 'usages', 'revenue', 'display_dsrs')
    list_filter = ['dsrs']

    def display_dsrs(self, obj):
        return str([d.id for d in obj.dsrs.all()])

    display_dsrs.short_description = "DSRs"


admin.site.register(DSR, DSRAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Territory, TerritoryAdmin)
admin.site.register(Resource, ResourceAdmin)