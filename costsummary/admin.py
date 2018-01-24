from django.forms import ModelForm
from django.contrib import admin
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import Http404
from django.db import connection as RawConnection

# import django_excel

from . import models
from .dumps import ParseArray


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


class SupplierDistanceInline(admin.TabularInline):
    """ Edit distance in supplier admin page """
    model = models.SupplierDistance
    max_num = 4
    extra = 0


@admin.register(models.Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """ Supplier admin class """
    list_display = (
        'duns',
        'name',
        'original_source',
        'is_mono_address',
        'is_promised_address',
        'address',
        'post_code',
        'region',
        'province',
        'district',
        'comment',
        'is_removable'
    )

    search_fields = [
        'original_source',
        'duns',
        'name',
        'address',
        'region',
        'province',
        'district'
    ]

    list_filter = (
        'original_source',
        'is_mono_address',
        'is_promised_address',
        'province'
    )

    inlines = [
        SupplierDistanceInline
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


class InboundTCSInline(admin.StackedInline):
    model = models.InboundTCS
    extra = 0


class InboundBuyerInline(admin.StackedInline):
    model = models.InboundBuyer
    extra = 0


class SupplierDistanceForm(ModelForm):
    """ Limit supplier dropdown list. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'instance') and self.instance.id and self.instance.bom.duns:
            self.fields['supplier_matched'].queryset = models.Supplier.objects.filter(duns=self.instance.bom.duns)

            if self.instance.supplier_matched:
                self.fields['supplier_distance_matched'].queryset = models.SupplierDistance.objects.filter(
                    supplier=self.instance.supplier_matched,
                    base__gte=0
                )
            else:
                self.fields['supplier_distance_matched'].queryset = models.SupplierDistance.objects.filter(
                    supplier__duns=self.instance.bom.duns,
                    base__gte=0
                )


class InboundAddressInline(admin.StackedInline):
    form = SupplierDistanceForm
    model = models.InboundAddress
    extra = 0


class InboundTCSPackageInline(admin.StackedInline):
    model = models.InboundTCSPackage
    extra = 0


class InboundHeaderPartInline(admin.StackedInline):
    model = models.InboundHeaderPart
    extra = 0


@admin.register(models.Ebom)
class EbomAdmin(admin.ModelAdmin):
    """ EBOM admin. """
    change_list_template = 'costsummary/change_list.html'

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
        EbomConfigurationInline,
        InboundTCSInline,
        InboundBuyerInline,
        InboundAddressInline,
        InboundTCSPackageInline,
        InboundHeaderPartInline,
    ]


@admin.register(models.AEbomEntry)
class AEbomEntryAdmin(admin.ModelAdmin):
    """ EBOM entry admin. """
    list_display = (
        'label',
        'model_year',
        'row_count',
        'user',
        'whether_loaded',
        'etl_time',
        'loaded_time',
    )

    list_filter = (
        'label',
        'model_year',
        'row_count',
        'etl_time'
    )

    readonly_fields = (
        'label',
        'model_year',
        'row_count',
        'etl_time',
        'loaded_time',
        'user'
    )

    def load(self, request, queryset):
        """ Load ebom of selected labels """
        for entry_object in queryset:
            label = entry_object.label

            if not entry_object.whether_loaded:
                # fetch all ebom records
                with RawConnection.cursor() as cursor:
                    cursor.execute("""
                        SELECT UPC, FNA, 
                          COMPONENT_MATERIAL_NUMBER, COMPONENT_MATERIAL_DESC_E, COMPONENT_MATERIAL_DESC_C, 
                          HEADER_PART_NUMBER, AR_EM_MATERIAL_FLAG, 
                          WORKSHOP, DUNS_NUMBER, VENDOR_NAME, EWO_NUMBER, MODEL_OPTION, VPPS, 
                          PACKAGE, ORDER_SAMPLE, USAGE_QTY
                          FROM ta_ebom 
                          WHERE MODEL_YEAR = %d AND BOOK = '%s' AND PLANT_CODE = '%s' AND MODEL = '%s'
                    """ % (entry_object.model_year, label.book, label.plant_code, label.model))

                    for row in cursor.fetchall():
                        if row[6] == 'AR':
                            _ar_em = True
                        elif row[6] == 'EM':
                            _ar_em = False
                        else:
                            _ar_em = None

                        ebom_object, _ = models.Ebom.objects.get_or_create(
                            label=label,
                            upc=row[0],
                            fna=row[1],
                            part_number=row[2],
                            description_en=row[3],
                            description_cn=row[4],
                            header_part_number=row[5],
                            ar_em_material_indicator=_ar_em,
                            work_shop=row[7],
                            vendor_duns_number=row[8],
                            supplier_name=row[9],
                            ewo_number=row[10],
                            model_and_option=row[11],
                            vpps=row[12]
                        )

                        configuration_object = models.EbomConfiguration(
                            bom=ebom_object,
                            package=row[13],
                            order_sample=row[14],
                            quantity=row[15]
                        )

                        configuration_object.save()

                        # create related object
                        # tcs object
                        if not hasattr(ebom_object, 'rel_tcs'):
                            tcs_object = models.InboundTCS(
                                bom=ebom_object
                            )
                            tcs_object.save()

                        # buyer object
                        if not hasattr(ebom_object, 'rel_buyer'):
                            buyer_object = models.InboundBuyer(
                                bom=ebom_object
                            )
                            buyer_object.save()

                        # address object
                        if not hasattr(ebom_object, 'rel_address'):
                            address_object = models.InboundAddress(
                                bom=ebom_object
                            )

                            if ebom_object.duns:
                                supplier_queryset = models.Supplier.objects.filter(duns=ebom_object.duns)

                                if supplier_queryset.count() == 1:
                                    address_object.supplier_matched = supplier_queryset.first()

                            address_object.save()

                        # tcs package object
                        if not hasattr(ebom_object, 'rel_tcs_package'):
                            tcs_pkg_object = models.InboundTCSPackage(
                                bom=ebom_object
                            )
                            tcs_pkg_object.save()

                        # header part object
                        if not hasattr(ebom_object, 'rel_header'):
                            tcs_header_object = models.InboundHeaderPart(
                                bom=ebom_object
                            )
                            tcs_header_object.save()

                    # update entry object
                    entry_object.whether_loaded = True
                    entry_object.loaded_time = timezone.now()
                    entry_object.user = request.user
                    entry_object.save()

                self.message_user(request, f"车型 {str(label)} 已成功加载.")

            else:
                self.message_user(request, f"车型 {str(label)} 之前已加载.")

            return HttpResponseRedirect(reverse('admin:costsummary_%s_changelist' % models.Ebom._meta.model_name) +
                                        '?label__id__exact=%d' % queryset[0].label.id)

    load.short_description = "载入选中的车型"

    actions = ['load']


@admin.register(models.UploadHandler)
class UploadHandlerAdmin(admin.ModelAdmin):
    """ Upload handler admin. """
    list_display = [
        'model_name',
        'upload_time'
    ]

    def get_readonly_fields(self, request, obj=None):
        """ Read-only fields according to request. """
        print(request.GET)
        model_name = request.GET.get('model_name')

        if model_name == '1':
            return ['download_tcs_template']

        elif model_name == '2':
            return ['download_buyer_template']

        else:
            return super().get_readonly_fields(request)

    def response_add(self, request, obj, post_url_continue=None):
        """ Redirect when add work completed. """
        post_file = request.FILES['file_to_be_uploaded']

        # default the only first sheet
        matrix = post_file.get_array()

        if obj.model_name == 1:
            # TCS data
            ParseArray.parse_tcs(matrix)

        elif obj.model_name == 2:
            # Buyer data
            ParseArray.parse_buyer(matrix)

        else:
            raise Http404('无法识别的数据模式.')

        return HttpResponseRedirect(reverse('admin:costsummary_%s_changelist' % models.Ebom._meta.model_name))

    def download_tcs_template(self, obj):
        """ Download tcs template. """
        _, _ = self, obj
        return '<a href="/costsummary/sheet/tcs">下载</a>'

    def download_buyer_template(self, obj):
        """ Download buyer template. """
        _, _ = self, obj
        return '<a href="/costsummary/sheet/buyer">下载</a>'

    download_tcs_template.short_description = 'TCS 物流跟踪表模板'
    download_buyer_template.short_description = 'TCS 采购定点表模板'

    download_tcs_template.allow_tags = True
    download_buyer_template.allow_tags = True
