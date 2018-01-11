from django.contrib import admin

from . import models


# rename admin labels
admin.site.index_title = '首页'
admin.site.site_header = 'Inbound 入厂物流成本'
admin.site.site_title = 'Inbound 数据管理'


# Register your models here.
@admin.register(models.TecCore)
class TecCoreAdmin(admin.ModelAdmin):
    """ Tec Core admin. """
    list_display = [
        'tec_id',
        'common_part_name',
    ]

    search_fields = [
        'tec_id',
        'common_part_name',
    ]

    list_per_page = 20

    ordering = [
        'tec_id',
    ]


@admin.register(models.NominalLabelMapping)
class NominalLabelMappingAdmin(admin.ModelAdmin):
    """Nominal label mapping admin. """

    list_display = (
        'value',
        'book',
        'plant_code',
        'model'
    )

    search_fields = [
        'value'
    ]

    list_filter = (
        'book',
        'plant_code',
        'model'
    )


class EbomConfigurationInline(admin.StackedInline):
    """ EBOM configuration data as inline. """
    model = models.EbomConfiguration
    extra = 0


@admin.register(models.Ebom)
class EbomAdmin(admin.ModelAdmin):
    """ EBOM admin. """
    list_display = (
        'part_number',
        'label',
        'upc',
        'fna',
        'description_en',
        'description_cn',
        'work_shop',
        'vendor_duns_number',
        'supplier_name',
        'model_and_option',
        'vpps'
    )

    search_fields = [
        'part_number',
        'description_en',
        'description_cn',
        'supplier_name'
    ]

    list_filter = (
        'label',
    )

    inlines = [
        EbomConfigurationInline
    ]
