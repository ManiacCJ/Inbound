from django.forms import ModelForm
from django.contrib import admin
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import Http404
from django.db import connection as RawConnection
from django.db.models import Max
from django.apps import apps

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


class InboundOperationalModeInline(admin.StackedInline):
    model = models.InboundOperationalMode
    extra = 0


class InboundModeInline(admin.StackedInline):
    model = models.InboundMode
    extra = 0


class InboundOperationalPackageInline(admin.StackedInline):
    model = models.InboundOperationalPackage
    extra = 0


class InboundPackageInline(admin.StackedInline):
    model = models.InboundPackage
    extra = 0


class InboundCalculationInline(admin.StackedInline):
    model = models.InboundCalculation
    extra = 0


class LabelValueFilter(admin.SimpleListFilter):
    """  Filter by label value """
    title = '车型'
    parameter_name = 'labelvalue'

    def lookups(self, request, model_admin):
        existed_labels = models.Ebom.objects.values('label__value').distinct()
        return [(e['label__value'], e['label__value']) for e in existed_labels]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(label__value__exact=self.value())
        else:
            return queryset


@admin.register(models.Ebom)
class EbomAdmin(admin.ModelAdmin):
    """ EBOM admin. """
    change_list_template = 'costsummary/change_list.html'

    list_per_page = 8

    list_display = (
        'label',
        'upc',
        'fna',
        'structure_node',
        'tec',
        'part_number',
        'description_en',
        'description_cn',
        'header_part_number',
        'get_quantity',
        'ar_em_material_indicator',
        'work_shop',
        # 'duns',
        'vendor_duns_number',
        'supplier_name',
        'ewo_number',
        'model_and_option',
        'vpps',

        'get_inboundheaderpart_head_part_number',
        'get_inboundheaderpart_assembly_supplier', 'get_inboundheaderpart_color',

        'get_inboundtcs_bidder_list_number',
        'get_inboundtcs_program', 'get_inboundtcs_supplier_ship_from_address', 'get_inboundtcs_process',
        'get_inboundtcs_suggest_delivery_method', 'get_inboundtcs_sgm_transport_duty',
        'get_inboundtcs_supplier_transport_duty', 'get_inboundtcs_sgm_returnable_duty',
        'get_inboundtcs_supplier_returnable_duty', 'get_inboundtcs_consignment_mode', 'get_inboundtcs_comments',

        'get_inboundbuyer_buyer', 'get_inboundbuyer_contract_incoterm',
        'get_inboundbuyer_contract_supplier_transportation_cost', 'get_inboundbuyer_contract_supplier_pkg_cost',
        'get_inboundbuyer_contract_supplier_seq_cost',

        'get_inboundaddress_fu_address', 'get_inboundaddress_mr_address', 'get_inboundaddress_property',
        'get_inboundaddress_region_division', 'get_inboundaddress_country',
        'get_inboundaddress_province', 'get_inboundaddress_city', 'get_inboundaddress_mfg_location',
        'get_inboundaddress_distance_to_sgm_plant',
        'get_inboundaddress_distance_to_shanghai_cc', 'get_inboundaddress_warehouse_address',
        'get_inboundaddress_warehouse_to_sgm_plant',

        'get_inboundoperationalmode_ckd_logistics_mode', 'get_inboundoperationalmode_planned_logistics_mode',
        'get_inboundoperationalmode_if_supplier_seq', 'get_inboundoperationalmode_payment_mode',

        'get_inboundmode_logistics_incoterm_mode', 'get_inboundmode_operation_mode',

        'get_inboundtcspackage_supplier_pkg_name', 'get_inboundtcspackage_supplier_pkg_pcs',
        'get_inboundtcspackage_supplier_pkg_length', 'get_inboundtcspackage_supplier_pkg_width',
        'get_inboundtcspackage_supplier_pkg_height', 'get_inboundtcspackage_supplier_pkg_folding_rate',
        'get_inboundtcspackage_supplier_pkg_cubic_pcs', 'get_inboundtcspackage_supplier_pkg_cubic_veh',
        'get_inboundtcspackage_sgm_pkg_name', 'get_inboundtcspackage_sgm_pkg_pcs',
        'get_inboundtcspackage_sgm_pkg_length', 'get_inboundtcspackage_sgm_pkg_width',
        'get_inboundtcspackage_sgm_pkg_height', 'get_inboundtcspackage_sgm_pkg_folding_rate',

        'get_inboundoperationalpackage_supplier_pkg_name', 'get_inboundoperationalpackage_supplier_pkg_pcs',
        'get_inboundoperationalpackage_supplier_pkg_length', 'get_inboundoperationalpackage_supplier_pkg_width',
        'get_inboundoperationalpackage_supplier_pkg_height', 'get_inboundoperationalpackage_supplier_pkg_folding_rate',
        'get_inboundoperationalpackage_sgm_pkg_name', 'get_inboundoperationalpackage_sgm_pkg_pcs',
        'get_inboundoperationalpackage_sgm_pkg_length', 'get_inboundoperationalpackage_sgm_pkg_width',
        'get_inboundoperationalpackage_sgm_pkg_height', 'get_inboundoperationalpackage_sgm_pkg_folding_rate',

        'get_inboundpackage_supplier_pkg_name', 'get_inboundpackage_supplier_pkg_pcs',
        'get_inboundpackage_supplier_pkg_length', 'get_inboundpackage_supplier_pkg_width',
        'get_inboundpackage_supplier_pkg_height', 'get_inboundpackage_supplier_pkg_folding_rate',
        'get_inboundpackage_supplier_pkg_cubic_pcs', 'get_inboundpackage_supplier_pkg_cubic_veh',
        'get_inboundpackage_sgm_pkg_name', 'get_inboundpackage_sgm_pkg_pcs', 'get_inboundpackage_sgm_pkg_length',
        'get_inboundpackage_sgm_pkg_width', 'get_inboundpackage_sgm_pkg_height',
        'get_inboundpackage_sgm_pkg_folding_rate', 'get_inboundpackage_sgm_pkg_cubic_pcs',
        'get_inboundpackage_sgm_pkg_cubic_veh', 'get_inboundpackage_cubic_matrix',

        'get_inboundcalculation_ddp_pcs', 'get_inboundcalculation_linehaul_oneway_pcs',
        'get_inboundcalculation_linehaul_vmi_pcs', 'get_inboundcalculation_linehaul_backway_pcs',
        'get_inboundcalculation_dom_truck_ttl_pcs', 'get_inboundcalculation_dom_water_oneway_pcs',
        'get_inboundcalculation_dom_cc_operation_pcs', 'get_inboundcalculation_dom_water_backway_pcs',
        'get_inboundcalculation_dom_water_ttl_pcs', 'get_inboundcalculation_oversea_inland_pcs',
        'get_inboundcalculation_oversea_cc_op_pcs', 'get_inboundcalculation_international_ocean_pcs',
        'get_inboundcalculation_dom_pull_pcs', 'get_inboundcalculation_certificate_pcs',
        'get_inboundcalculation_oversea_ocean_ttl_pcs', 'get_inboundcalculation_oversea_air_pcs',
        'get_inboundcalculation_inbound_ttl_pcs', 'get_inboundcalculation_ddp_veh',
        'get_inboundcalculation_linehaul_oneway_veh', 'get_inboundcalculation_linehaul_vmi_veh',
        'get_inboundcalculation_linehaul_backway_veh', 'get_inboundcalculation_dom_truck_ttl_veh',
        'get_inboundcalculation_dom_water_oneway_veh', 'get_inboundcalculation_dom_cc_operation_veh',
        'get_inboundcalculation_dom_water_backway_veh', 'get_inboundcalculation_dom_water_ttl_veh',
        'get_inboundcalculation_oversea_inland_veh', 'get_inboundcalculation_oversea_cc_op_veh',
        'get_inboundcalculation_international_ocean_veh', 'get_inboundcalculation_dom_pull_veh',
        'get_inboundcalculation_certificate_veh', 'get_inboundcalculation_oversea_ocean_ttl_veh',
        'get_inboundcalculation_oversea_air_veh', 'get_inboundcalculation_inbound_ttl_veh'
    )

    search_fields = [
        'part_number',
        'description_en',
        'description_cn',
        'supplier_name'
    ]

    list_filter = (
        LabelValueFilter,
        ('label', admin.RelatedOnlyFieldListFilter),
    )

    inlines = [
        # EbomConfigurationInline,
        InboundHeaderPartInline,
        InboundTCSInline,
        InboundBuyerInline,
        InboundAddressInline,
        InboundTCSPackageInline,
        InboundOperationalModeInline,
        InboundModeInline,
        InboundOperationalPackageInline,
        InboundPackageInline,
        InboundCalculationInline
    ]

    def changelist_view(self, request, extra_context=None):
        """ filter by session value """
        q = request.GET.copy()

        if 'label__id__exact' in q:
            request.session['label'] = q['label__id__exact']

        else:
            if 'label' in request.session:
                q['label__id__exact'] = request.session['label']
                request.GET = q

        return super(EbomAdmin, self).changelist_view(request, extra_context=extra_context)

    def get_quantity(self, obj):
        """ max of configuration quanity. """
        _ = self
        conf_objects = obj.rel_configuration
        return conf_objects.aggregate(Max('quantity'))['quantity__max']

    get_quantity.short_description = 'Quantity'

    def get_inboundaddress_fu_address(self, obj):
        """ 运作功能块地址 & 最终地址梳理, FU提供的原始地址信息 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'fu_address'):
                return rel_obj.fu_address

        return None

    get_inboundaddress_fu_address.short_description = '运作功能块地址/FU提供的原始地址信息'

    def get_inboundaddress_mr_address(self, obj):
        """ 运作功能块地址 & 最终地址梳理, MR取货地址 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'mr_address'):
                return rel_obj.mr_address

        return None

    get_inboundaddress_mr_address.short_description = '运作功能块地址/MR取货地址'

    def get_inboundaddress_property(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 国产/进口/自制 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'property'):
                return rel_obj.get_property_display()

        return None

    get_inboundaddress_property.short_description = '国产/进口/自制'

    def get_inboundaddress_region_division(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 区域划分 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'region_division'):
                return rel_obj.region_division

        return None

    get_inboundaddress_region_division.short_description = '最终地址梳理/区域划分'

    def get_inboundaddress_country(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 国家 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'country'):
                return rel_obj.country

        return None

    get_inboundaddress_country.short_description = '最终地址梳理/国家'

    def get_inboundaddress_province(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 省 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'province'):
                return rel_obj.province

        return None

    get_inboundaddress_province.short_description = '最终地址梳理/省'

    def get_inboundaddress_city(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 市 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'city'):
                return rel_obj.city

        return None

    get_inboundaddress_city.short_description = '最终地址梳理/市'

    def get_inboundaddress_mfg_location(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 生产地址 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'mfg_location'):
                return rel_obj.mfg_location

        return None

    get_inboundaddress_mfg_location.short_description = '最终地址梳理/生产地址'

    def get_inboundaddress_distance_to_sgm_plant(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 运输距离-至生产厂区 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'distance_to_sgm_plant'):
                return rel_obj.distance_to_sgm_plant

        return None

    get_inboundaddress_distance_to_sgm_plant.short_description = '运输距离-至生产厂区'

    def get_inboundaddress_distance_to_shanghai_cc(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 运输距离-金桥C类 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'distance_to_shanghai_cc'):
                return rel_obj.distance_to_shanghai_cc

        return None

    get_inboundaddress_distance_to_shanghai_cc.short_description = '运输距离-金桥C类'

    def get_inboundaddress_warehouse_address(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 中转库地址 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'warehouse_address'):
                return rel_obj.warehouse_address

        return None

    get_inboundaddress_warehouse_address.short_description = '中转库地址'

    def get_inboundaddress_warehouse_to_sgm_plant(self, obj):
        """ 运作功能块地址 & 最终地址梳理, 中转库运输距离 """
        _ = self

        if hasattr(obj, 'rel_address'):
            rel_obj = obj.rel_address

            if hasattr(rel_obj, 'warehouse_to_sgm_plant'):
                return rel_obj.warehouse_to_sgm_plant

        return None

    get_inboundaddress_warehouse_to_sgm_plant.short_description = '中转库运输距离'

    def get_inboundbuyer_buyer(self, obj):
        """ 采购 信息, 采购员 """
        _ = self

        if hasattr(obj, 'rel_buyer'):
            rel_obj = obj.rel_buyer

            if hasattr(rel_obj, 'buyer'):
                return rel_obj.buyer

        return None

    get_inboundbuyer_buyer.short_description = '采购信息/采购员'

    def get_inboundbuyer_contract_incoterm(self, obj):
        """ 采购 信息, 合同条款 """
        _ = self

        if hasattr(obj, 'rel_buyer'):
            rel_obj = obj.rel_buyer

            if hasattr(rel_obj, 'contract_incoterm'):
                return rel_obj.contract_incoterm

        return None

    get_inboundbuyer_contract_incoterm.short_description = '采购信息/合同条款'

    def get_inboundbuyer_contract_supplier_transportation_cost(self, obj):
        """ 采购 信息, 供应商运费 """
        _ = self

        if hasattr(obj, 'rel_buyer'):
            rel_obj = obj.rel_buyer

            if hasattr(rel_obj, 'contract_supplier_transportation_cost'):
                return rel_obj.contract_supplier_transportation_cost

        return None

    get_inboundbuyer_contract_supplier_transportation_cost.short_description = '采购信息/供应商运费'

    def get_inboundbuyer_contract_supplier_pkg_cost(self, obj):
        """ 采购 信息, 供应商外包装费 """
        _ = self

        if hasattr(obj, 'rel_buyer'):
            rel_obj = obj.rel_buyer

            if hasattr(rel_obj, 'contract_supplier_pkg_cost'):
                return rel_obj.contract_supplier_pkg_cost

        return None

    get_inboundbuyer_contract_supplier_pkg_cost.short_description = '采购信息/供应商外包装费'

    def get_inboundbuyer_contract_supplier_seq_cost(self, obj):
        """ 采购 信息, 供应商排序费 """
        _ = self

        if hasattr(obj, 'rel_buyer'):
            rel_obj = obj.rel_buyer

            if hasattr(rel_obj, 'contract_supplier_seq_cost'):
                return rel_obj.contract_supplier_seq_cost

        return None

    get_inboundbuyer_contract_supplier_seq_cost.short_description = '采购信息/供应商排序费'

    def get_inboundheaderpart_head_part_number(self, obj):
        """ 头零件 信息, 头零件 """
        _ = self

        if hasattr(obj, 'rel_header'):
            rel_obj = obj.rel_header

            if hasattr(rel_obj, 'head_part_number'):
                return rel_obj.head_part_number

        return None

    get_inboundheaderpart_head_part_number.short_description = '头零件'

    def get_inboundheaderpart_assembly_supplier(self, obj):
        """ 头零件 信息, 总成供应商 """
        _ = self

        if hasattr(obj, 'rel_header'):
            rel_obj = obj.rel_header

            if hasattr(rel_obj, 'assembly_supplier'):
                return rel_obj.assembly_supplier

        return None

    get_inboundheaderpart_assembly_supplier.short_description = '头零件信息/总成供应商'

    def get_inboundheaderpart_color(self, obj):
        """ 头零件 信息, 颜色件 """
        _ = self

        if hasattr(obj, 'rel_header'):
            rel_obj = obj.rel_header

            if hasattr(rel_obj, 'color'):
                return rel_obj.color

        return None

    get_inboundheaderpart_color.short_description = '头零件信息/颜色件'

    def get_inboundmode_logistics_incoterm_mode(self, obj):
        """ 最终模式梳理 信息, 运输条款 """
        _ = self

        if hasattr(obj, 'rel_mode'):
            rel_obj = obj.rel_mode

            if hasattr(rel_obj, 'logistics_incoterm_mode'):
                return rel_obj.get_logistics_incoterm_mode_display()

        return None

    get_inboundmode_logistics_incoterm_mode.short_description = '最终模式/运输条款'

    def get_inboundmode_operation_mode(self, obj):
        """ 最终模式梳理 信息, 入厂物流模式 """
        _ = self

        if hasattr(obj, 'rel_mode'):
            rel_obj = obj.rel_mode

            if hasattr(rel_obj, 'operation_mode'):
                return rel_obj.get_operation_mode_display()

        return None

    get_inboundmode_operation_mode.short_description = '最终模式/入厂物流模式'

    def get_inboundoperationalmode_ckd_logistics_mode(self, obj):
        """ 运作功能块模式 信息, 海运FCL/海运LCL/空运 """
        _ = self

        if hasattr(obj, 'rel_op_mode'):
            rel_obj = obj.rel_op_mode

            if hasattr(rel_obj, 'ckd_logistics_mode'):
                return rel_obj.ckd_logistics_mode

        return None

    get_inboundoperationalmode_ckd_logistics_mode.short_description = '运作功能块模式/海运FCL/海运LCL/空运'

    def get_inboundoperationalmode_planned_logistics_mode(self, obj):
        """ 运作功能块模式 信息, 规划模式（A/B/C/自制/进口） """
        _ = self

        if hasattr(obj, 'rel_op_mode'):
            rel_obj = obj.rel_op_mode

            if hasattr(rel_obj, 'planned_logistics_mode'):
                return rel_obj.planned_logistics_mode

        return None

    get_inboundoperationalmode_planned_logistics_mode.short_description = '运作功能块模式/规划模式（A/B/C/自制/进口）'

    def get_inboundoperationalmode_if_supplier_seq(self, obj):
        """ 运作功能块模式 信息, 是否供应商排序(JIT) """
        _ = self

        if hasattr(obj, 'rel_op_mode'):
            rel_obj = obj.rel_op_mode

            if hasattr(rel_obj, 'if_supplier_seq'):
                return rel_obj.if_supplier_seq

        return None

    get_inboundoperationalmode_if_supplier_seq.short_description = '运作功能块模式/是否供应商排序(JIT)'

    def get_inboundoperationalmode_payment_mode(self, obj):
        """ 运作功能块模式 信息, 结费模式（2A/2B）以此为准 """
        _ = self

        if hasattr(obj, 'rel_op_mode'):
            rel_obj = obj.rel_op_mode

            if hasattr(rel_obj, 'payment_mode'):
                return rel_obj.payment_mode

        return None

    get_inboundoperationalmode_payment_mode.short_description = '运作功能块模式/结费模式（2A/2B）以此为准'

    def get_inboundoperationalpackage_supplier_pkg_name(self, obj):
        """ 运作功能块包装 信息, 供应商包装PK Name """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_name'):
                return rel_obj.supplier_pkg_name

        return None

    get_inboundoperationalpackage_supplier_pkg_name.short_description = '运作功能块包装/供应商包装PK Name'

    def get_inboundoperationalpackage_supplier_pkg_pcs(self, obj):
        """ 运作功能块包装 信息, 供应商包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_pcs'):
                return rel_obj.supplier_pkg_pcs

        return None

    get_inboundoperationalpackage_supplier_pkg_pcs.short_description = '运作功能块包装/供应商包装PKPCS'

    def get_inboundoperationalpackage_supplier_pkg_length(self, obj):
        """ 运作功能块包装 信息, 供应商包装PL """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_length'):
                return rel_obj.supplier_pkg_length

        return None

    get_inboundoperationalpackage_supplier_pkg_length.short_description = '运作功能块包装/供应商包装PL'

    def get_inboundoperationalpackage_supplier_pkg_width(self, obj):
        """ 运作功能块包装 信息, 供应商包装PW """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_width'):
                return rel_obj.supplier_pkg_width

        return None

    get_inboundoperationalpackage_supplier_pkg_width.short_description = '运作功能块包装/供应商包装PW'

    def get_inboundoperationalpackage_supplier_pkg_height(self, obj):
        """ 运作功能块包装 信息, 供应商包装PH """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_height'):
                return rel_obj.supplier_pkg_height

        return None

    get_inboundoperationalpackage_supplier_pkg_height.short_description = '运作功能块包装/供应商包装PH'

    def get_inboundoperationalpackage_supplier_pkg_folding_rate(self, obj):
        """ 运作功能块包装 信息, 供应商包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'supplier_pkg_folding_rate'):
                return rel_obj.supplier_pkg_folding_rate

        return None

    get_inboundoperationalpackage_supplier_pkg_folding_rate.short_description = '运作功能块包装/供应商包装折叠率'

    def get_inboundoperationalpackage_sgm_pkg_name(self, obj):
        """ 运作功能块包装 信息, SGM包装PK Name """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_name'):
                return rel_obj.sgm_pkg_name

        return None

    get_inboundoperationalpackage_sgm_pkg_name.short_description = '运作功能块包装/SGM包装PK Name'

    def get_inboundoperationalpackage_sgm_pkg_pcs(self, obj):
        """ 运作功能块包装 信息, SGM包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_pcs'):
                return rel_obj.sgm_pkg_pcs

        return None

    get_inboundoperationalpackage_sgm_pkg_pcs.short_description = '运作功能块包装/SGM包装PKPCS'

    def get_inboundoperationalpackage_sgm_pkg_length(self, obj):
        """ 运作功能块包装 信息, SGM包装PL """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_length'):
                return rel_obj.sgm_pkg_length

        return None

    get_inboundoperationalpackage_sgm_pkg_length.short_description = '运作功能块包装/SGM包装PL'

    def get_inboundoperationalpackage_sgm_pkg_width(self, obj):
        """ 运作功能块包装 信息, SGM包装PW """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_width'):
                return rel_obj.sgm_pkg_width

        return None

    get_inboundoperationalpackage_sgm_pkg_width.short_description = '运作功能块包装/SGM包装PW'

    def get_inboundoperationalpackage_sgm_pkg_height(self, obj):
        """ 运作功能块包装 信息, SGM包装PH """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_height'):
                return rel_obj.sgm_pkg_height

        return None

    get_inboundoperationalpackage_sgm_pkg_height.short_description = '运作功能块包装/SGM包装PH'

    def get_inboundoperationalpackage_sgm_pkg_folding_rate(self, obj):
        """ 运作功能块包装 信息, SGM包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_op_package'):
            rel_obj = obj.rel_op_package

            if hasattr(rel_obj, 'sgm_pkg_folding_rate'):
                return rel_obj.sgm_pkg_folding_rate

        return None

    get_inboundoperationalpackage_sgm_pkg_folding_rate.short_description = '运作功能块包装/SGM包装折叠率'

    def get_inboundpackage_supplier_pkg_name(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装PK Name """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_name'):
                return rel_obj.supplier_pkg_name

        return None

    get_inboundpackage_supplier_pkg_name.short_description = '最终包装信息/供应商包装PK Name'

    def get_inboundpackage_supplier_pkg_pcs(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_pcs'):
                return rel_obj.supplier_pkg_pcs

        return None

    get_inboundpackage_supplier_pkg_pcs.short_description = '最终包装信息/供应商包装PKPCS'

    def get_inboundpackage_supplier_pkg_length(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装PL """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_length'):
                return rel_obj.supplier_pkg_length

        return None

    get_inboundpackage_supplier_pkg_length.short_description = '最终包装信息/供应商包装PL'

    def get_inboundpackage_supplier_pkg_width(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装PW """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_width'):
                return rel_obj.supplier_pkg_width

        return None

    get_inboundpackage_supplier_pkg_width.short_description = '最终包装信息/供应商包装PW'

    def get_inboundpackage_supplier_pkg_height(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装PH """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_height'):
                return rel_obj.supplier_pkg_height

        return None

    get_inboundpackage_supplier_pkg_height.short_description = '最终包装信息/供应商包装PH'

    def get_inboundpackage_supplier_pkg_folding_rate(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_folding_rate'):
                return rel_obj.supplier_pkg_folding_rate

        return None

    get_inboundpackage_supplier_pkg_folding_rate.short_description = '最终包装信息/供应商包装折叠率'

    def get_inboundpackage_supplier_pkg_cubic_pcs(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装Cubic/Pcs """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_cubic_pcs'):
                return rel_obj.supplier_pkg_cubic_pcs

        return None

    get_inboundpackage_supplier_pkg_cubic_pcs.short_description = '最终包装信息/供应商包装Cubic/Pcs'

    def get_inboundpackage_supplier_pkg_cubic_veh(self, obj):
        """ 最终包装信息梳理 信息, 供应商包装Cubic/Veh """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'supplier_pkg_cubic_veh'):
                return rel_obj.supplier_pkg_cubic_veh

        return None

    get_inboundpackage_supplier_pkg_cubic_veh.short_description = '最终包装信息/供应商包装Cubic/Veh'

    def get_inboundpackage_sgm_pkg_name(self, obj):
        """ 最终包装信息梳理 信息, SGM包装PK Name """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_name'):
                return rel_obj.sgm_pkg_name

        return None

    get_inboundpackage_sgm_pkg_name.short_description = '最终包装信息/SGM包装PK Name'

    def get_inboundpackage_sgm_pkg_pcs(self, obj):
        """ 最终包装信息梳理 信息, SGM包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_pcs'):
                return rel_obj.sgm_pkg_pcs

        return None

    get_inboundpackage_sgm_pkg_pcs.short_description = '最终包装信息/SGM包装PKPCS'

    def get_inboundpackage_sgm_pkg_length(self, obj):
        """ 最终包装信息梳理 信息, SGM包装PL """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_length'):
                return rel_obj.sgm_pkg_length

        return None

    get_inboundpackage_sgm_pkg_length.short_description = '最终包装信息/SGM包装PL'

    def get_inboundpackage_sgm_pkg_width(self, obj):
        """ 最终包装信息梳理 信息, SGM包装PW """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_width'):
                return rel_obj.sgm_pkg_width

        return None

    get_inboundpackage_sgm_pkg_width.short_description = '最终包装信息/SGM包装PW'

    def get_inboundpackage_sgm_pkg_height(self, obj):
        """ 最终包装信息梳理 信息, SGM包装PH """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_height'):
                return rel_obj.sgm_pkg_height

        return None

    get_inboundpackage_sgm_pkg_height.short_description = '最终包装信息/SGM包装PH'

    def get_inboundpackage_sgm_pkg_folding_rate(self, obj):
        """ 最终包装信息梳理 信息, SGM包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_folding_rate'):
                return rel_obj.sgm_pkg_folding_rate

        return None

    get_inboundpackage_sgm_pkg_folding_rate.short_description = '最终包装信息/SGM包装折叠率'

    def get_inboundpackage_sgm_pkg_cubic_pcs(self, obj):
        """ 最终包装信息梳理 信息, SGM包装Cubic/Pcs """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_cubic_pcs'):
                return rel_obj.sgm_pkg_cubic_pcs

        return None

    get_inboundpackage_sgm_pkg_cubic_pcs.short_description = '最终包装信息/SGM包装Cubic/Pcs'

    def get_inboundpackage_sgm_pkg_cubic_veh(self, obj):
        """ 最终包装信息梳理 信息, SGM包装Cubic/Veh """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'sgm_pkg_cubic_veh'):
                return rel_obj.sgm_pkg_cubic_veh

        return None

    get_inboundpackage_sgm_pkg_cubic_veh.short_description = '最终包装信息/SGM包装Cubic/Veh'

    def get_inboundpackage_cubic_matrix(self, obj):
        """ 最终包装信息梳理 信息, 体积放大系数 """
        _ = self

        if hasattr(obj, 'rel_package'):
            rel_obj = obj.rel_package

            if hasattr(rel_obj, 'cubic_matrix'):
                return rel_obj.cubic_matrix

        return None

    get_inboundpackage_cubic_matrix.short_description = '最终包装信息/体积放大系数'

    def get_inboundtcs_bidder_list_number(self, obj):
        """ TCS 物流跟踪 信息, Bidder号 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'bidder_list_number'):
                return rel_obj.bidder_list_number

        return None

    get_inboundtcs_bidder_list_number.short_description = 'TCS 物流跟踪/Bidder号'

    def get_inboundtcs_program(self, obj):
        """ TCS 物流跟踪 信息, 定点项目 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'program'):
                return rel_obj.program

        return None

    get_inboundtcs_program.short_description = 'TCS 物流跟踪/定点项目'

    def get_inboundtcs_supplier_ship_from_address(self, obj):
        """ TCS 物流跟踪 信息, 供应商发货地址 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'supplier_ship_from_address'):
                return rel_obj.supplier_ship_from_address

        return None

    get_inboundtcs_supplier_ship_from_address.short_description = 'TCS 物流跟踪/供应商发货地址'

    def get_inboundtcs_process(self, obj):
        """ TCS 物流跟踪 信息, 报价条款 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'process'):
                return rel_obj.get_process_display()

        return None

    get_inboundtcs_process.short_description = 'TCS 物流跟踪/报价条款'

    def get_inboundtcs_suggest_delivery_method(self, obj):
        """ TCS 物流跟踪 信息, 运输模式 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'suggest_delivery_method'):
                return rel_obj.get_suggest_delivery_method_display()

        return None

    get_inboundtcs_suggest_delivery_method.short_description = 'TCS 物流跟踪/运输模式'

    def get_inboundtcs_sgm_transport_duty(self, obj):
        """ TCS 物流跟踪 信息, SGM运输责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'sgm_transport_duty'):
                return rel_obj.get_sgm_transport_duty_display()

        return None

    get_inboundtcs_sgm_transport_duty.short_description = 'TCS 物流跟踪/SGM运输责任'

    def get_inboundtcs_supplier_transport_duty(self, obj):
        """ TCS 物流跟踪 信息, 供应商运输责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'supplier_transport_duty'):
                return rel_obj.get_supplier_transport_duty_display()

        return None

    get_inboundtcs_supplier_transport_duty.short_description = 'TCS 物流跟踪/供应商运输责任'

    def get_inboundtcs_sgm_returnable_duty(self, obj):
        """ TCS 物流跟踪 信息, SGM外包装责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'sgm_returnable_duty'):
                return rel_obj.get_sgm_returnable_duty_display()

        return None

    get_inboundtcs_sgm_returnable_duty.short_description = 'TCS 物流跟踪/SGM外包装责任'

    def get_inboundtcs_supplier_returnable_duty(self, obj):
        """ TCS 物流跟踪 信息, 供应商外包装责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'supplier_returnable_duty'):
                return rel_obj.get_supplier_returnable_duty_display()

        return None

    get_inboundtcs_supplier_returnable_duty.short_description = 'TCS 物流跟踪/供应商外包装责任'

    def get_inboundtcs_consignment_mode(self, obj):
        """ TCS 物流跟踪 信息, 外协加工业务模式 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'consignment_mode'):
                return rel_obj.get_consignment_mode_display()

        return None

    get_inboundtcs_consignment_mode.short_description = 'TCS 物流跟踪/外协加工业务模式'

    def get_inboundtcs_comments(self, obj):
        """ TCS 物流跟踪 信息, 备注 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'comments'):
                return rel_obj.comments

        return None

    get_inboundtcs_comments.short_description = 'TCS 物流跟踪/备注'

    def get_inboundtcspackage_supplier_pkg_name(self, obj):
        """ TCS包装 信息, 供应商出厂包装PK Name """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_name'):
                return rel_obj.supplier_pkg_name

        return None

    get_inboundtcspackage_supplier_pkg_name.short_description = 'TCS包装/供应商出厂包装PK Name'

    def get_inboundtcspackage_supplier_pkg_pcs(self, obj):
        """ TCS包装 信息, 供应商出厂包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_pcs'):
                return rel_obj.supplier_pkg_pcs

        return None

    get_inboundtcspackage_supplier_pkg_pcs.short_description = 'TCS包装/供应商出厂包装PKPCS'

    def get_inboundtcspackage_supplier_pkg_length(self, obj):
        """ TCS包装 信息, 供应商出厂包装PL """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_length'):
                return rel_obj.supplier_pkg_length

        return None

    get_inboundtcspackage_supplier_pkg_length.short_description = 'TCS包装/供应商出厂包装PL'

    def get_inboundtcspackage_supplier_pkg_width(self, obj):
        """ TCS包装 信息, 供应商出厂包装PW """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_width'):
                return rel_obj.supplier_pkg_width

        return None

    get_inboundtcspackage_supplier_pkg_width.short_description = 'TCS包装/供应商出厂包装PW'

    def get_inboundtcspackage_supplier_pkg_height(self, obj):
        """ TCS包装 信息, 供应商出厂包装PH """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_height'):
                return rel_obj.supplier_pkg_height

        return None

    get_inboundtcspackage_supplier_pkg_height.short_description = 'TCS包装/供应商出厂包装PH'

    def get_inboundtcspackage_supplier_pkg_folding_rate(self, obj):
        """ TCS包装 信息, 供应商出厂包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_folding_rate'):
                return rel_obj.supplier_pkg_folding_rate

        return None

    get_inboundtcspackage_supplier_pkg_folding_rate.short_description = 'TCS包装/供应商出厂包装折叠率'

    def get_inboundtcspackage_supplier_pkg_cubic_pcs(self, obj):
        """ TCS包装 信息, 供应商出厂包装Cubic/Pcs """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_cubic_pcs'):
                return rel_obj.supplier_pkg_cubic_pcs

        return None

    get_inboundtcspackage_supplier_pkg_cubic_pcs.short_description = 'TCS包装/供应商出厂包装Cubic/Pcs'

    def get_inboundtcspackage_supplier_pkg_cubic_veh(self, obj):
        """ TCS包装 信息, 供应商出厂包装Cubic/Veh """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'supplier_pkg_cubic_veh'):
                return rel_obj.supplier_pkg_cubic_veh

        return None

    get_inboundtcspackage_supplier_pkg_cubic_veh.short_description = 'TCS包装/供应商出厂包装Cubic/Veh'

    def get_inboundtcspackage_sgm_pkg_name(self, obj):
        """ TCS包装 信息, 先期规划包装PK Name """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_name'):
                return rel_obj.sgm_pkg_name

        return None

    get_inboundtcspackage_sgm_pkg_name.short_description = 'TCS包装/先期规划包装PK Name'

    def get_inboundtcspackage_sgm_pkg_pcs(self, obj):
        """ TCS包装 信息, 先期规划包装PKPCS """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_pcs'):
                return rel_obj.sgm_pkg_pcs

        return None

    get_inboundtcspackage_sgm_pkg_pcs.short_description = 'TCS包装/先期规划包装PKPCS'

    def get_inboundtcspackage_sgm_pkg_length(self, obj):
        """ TCS包装 信息, 先期规划包装PL """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_length'):
                return rel_obj.sgm_pkg_length

        return None

    get_inboundtcspackage_sgm_pkg_length.short_description = 'TCS包装/先期规划包装PL'

    def get_inboundtcspackage_sgm_pkg_width(self, obj):
        """ TCS包装 信息, 先期规划包装PW """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_width'):
                return rel_obj.sgm_pkg_width

        return None

    get_inboundtcspackage_sgm_pkg_width.short_description = 'TCS包装/先期规划包装PW'

    def get_inboundtcspackage_sgm_pkg_height(self, obj):
        """ TCS包装 信息, 先期规划包装PH """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_height'):
                return rel_obj.sgm_pkg_height

        return None

    get_inboundtcspackage_sgm_pkg_height.short_description = 'TCS包装/先期规划包装PH'

    def get_inboundtcspackage_sgm_pkg_folding_rate(self, obj):
        """ TCS包装 信息, 先期规划包装折叠率 """
        _ = self

        if hasattr(obj, 'rel_tcs_package'):
            rel_obj = obj.rel_tcs_package

            if hasattr(rel_obj, 'sgm_pkg_folding_rate'):
                return rel_obj.sgm_pkg_folding_rate

        return None

    get_inboundtcspackage_sgm_pkg_folding_rate.short_description = 'TCS包装/先期规划包装折叠率'

    def get_inboundcalculation_ddp_pcs(self, obj):
        """ 计算, DDP运费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'ddp_pcs'):
                return rel_obj.ddp_pcs

        return None

    get_inboundcalculation_ddp_pcs.short_description = '计算/DDP运费/pcs'

    def get_inboundcalculation_linehaul_oneway_pcs(self, obj):
        """ 计算, 干线去程/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_oneway_pcs'):
                return rel_obj.linehaul_oneway_pcs

        return None

    get_inboundcalculation_linehaul_oneway_pcs.short_description = '计算/干线去程/pcs'

    def get_inboundcalculation_linehaul_vmi_pcs(self, obj):
        """ 计算, 干线VMI/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_vmi_pcs'):
                return rel_obj.linehaul_vmi_pcs

        return None

    get_inboundcalculation_linehaul_vmi_pcs.short_description = '计算/干线VMI/pcs'

    def get_inboundcalculation_linehaul_backway_pcs(self, obj):
        """ 计算, 干线返程/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_backway_pcs'):
                return rel_obj.linehaul_backway_pcs

        return None

    get_inboundcalculation_linehaul_backway_pcs.short_description = '计算/干线返程/pcs'

    def get_inboundcalculation_dom_truck_ttl_pcs(self, obj):
        """ 计算, 国内陆运/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_truck_ttl_pcs'):
                return rel_obj.dom_truck_ttl_pcs

        return None

    get_inboundcalculation_dom_truck_ttl_pcs.short_description = '计算/国内陆运/pcs'

    def get_inboundcalculation_dom_water_oneway_pcs(self, obj):
        """ 计算, 国内水运-去程/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_oneway_pcs'):
                return rel_obj.dom_water_oneway_pcs

        return None

    get_inboundcalculation_dom_water_oneway_pcs.short_description = '计算/国内水运-去程/pcs'

    def get_inboundcalculation_dom_cc_operation_pcs(self, obj):
        """ 计算, 国内CC操作费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_cc_operation_pcs'):
                return rel_obj.dom_cc_operation_pcs

        return None

    get_inboundcalculation_dom_cc_operation_pcs.short_description = '计算/国内CC操作费/pcs'

    def get_inboundcalculation_dom_water_backway_pcs(self, obj):
        """ 计算, 国内水运-返程/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_backway_pcs'):
                return rel_obj.dom_water_backway_pcs

        return None

    get_inboundcalculation_dom_water_backway_pcs.short_description = '计算/国内水运-返程/pcs'

    def get_inboundcalculation_dom_water_ttl_pcs(self, obj):
        """ 计算, 国内水运/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_ttl_pcs'):
                return rel_obj.dom_water_ttl_pcs

        return None

    get_inboundcalculation_dom_water_ttl_pcs.short_description = '计算/国内水运/pcs'

    def get_inboundcalculation_oversea_inland_pcs(self, obj):
        """ 计算, 海外段内陆运输/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_inland_pcs'):
                return rel_obj.oversea_inland_pcs

        return None

    get_inboundcalculation_oversea_inland_pcs.short_description = '计算/海外段内陆运输/pcs'

    def get_inboundcalculation_oversea_cc_op_pcs(self, obj):
        """ 计算, 海外CC操作费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_cc_op_pcs'):
                return rel_obj.oversea_cc_op_pcs

        return None

    get_inboundcalculation_oversea_cc_op_pcs.short_description = '计算/海外CC操作费/pcs'

    def get_inboundcalculation_international_ocean_pcs(self, obj):
        """ 计算, 国际海运费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'international_ocean_pcs'):
                return rel_obj.international_ocean_pcs

        return None

    get_inboundcalculation_international_ocean_pcs.short_description = '计算/国际海运费/pcs'

    def get_inboundcalculation_dom_pull_pcs(self, obj):
        """ 计算, 国内拉动费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_pull_pcs'):
                return rel_obj.dom_pull_pcs

        return None

    get_inboundcalculation_dom_pull_pcs.short_description = '计算/国内拉动费/pcs'

    def get_inboundcalculation_certificate_pcs(self, obj):
        """ 计算, 单证费/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'certificate_pcs'):
                return rel_obj.certificate_pcs

        return None

    get_inboundcalculation_certificate_pcs.short_description = '计算/单证费/pcs'

    def get_inboundcalculation_oversea_ocean_ttl_pcs(self, obj):
        """ 计算, 进口海运/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_ocean_ttl_pcs'):
                return rel_obj.oversea_ocean_ttl_pcs

        return None

    get_inboundcalculation_oversea_ocean_ttl_pcs.short_description = '计算/进口海运/pcs'

    def get_inboundcalculation_oversea_air_pcs(self, obj):
        """ 计算, 进口空运/pcs """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_air_pcs'):
                return rel_obj.oversea_air_pcs

        return None

    get_inboundcalculation_oversea_air_pcs.short_description = '计算/进口空运/pcs'

    def get_inboundcalculation_inbound_ttl_pcs(self, obj):
        """ 计算, IB Cost """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'inbound_ttl_pcs'):
                return rel_obj.inbound_ttl_pcs

        return None

    get_inboundcalculation_inbound_ttl_pcs.short_description = '计算/IB Cost'

    def get_inboundcalculation_ddp_veh(self, obj):
        """ 计算, 单车费用 DDP运费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'ddp_veh'):
                return rel_obj.ddp_veh

        return None

    get_inboundcalculation_ddp_veh.short_description = '计算/单车费用 DDP运费/veh'

    def get_inboundcalculation_linehaul_oneway_veh(self, obj):
        """ 计算, 单车费用 干线去程/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_oneway_veh'):
                return rel_obj.linehaul_oneway_veh

        return None

    get_inboundcalculation_linehaul_oneway_veh.short_description = '计算/单车费用 干线去程/veh'

    def get_inboundcalculation_linehaul_vmi_veh(self, obj):
        """ 计算, 单车费用 干线VMI/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_vmi_veh'):
                return rel_obj.linehaul_vmi_veh

        return None

    get_inboundcalculation_linehaul_vmi_veh.short_description = '计算/单车费用 干线VMI/veh'

    def get_inboundcalculation_linehaul_backway_veh(self, obj):
        """ 计算, 单车费用 干线返程/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'linehaul_backway_veh'):
                return rel_obj.linehaul_backway_veh

        return None

    get_inboundcalculation_linehaul_backway_veh.short_description = '计算/单车费用 干线返程/veh'

    def get_inboundcalculation_dom_truck_ttl_veh(self, obj):
        """ 计算, 单车费用 国内陆运/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_truck_ttl_veh'):
                return rel_obj.dom_truck_ttl_veh

        return None

    get_inboundcalculation_dom_truck_ttl_veh.short_description = '计算/单车费用 国内陆运/veh'

    def get_inboundcalculation_dom_water_oneway_veh(self, obj):
        """ 计算, 单车费用 国内海运-去程/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_oneway_veh'):
                return rel_obj.dom_water_oneway_veh

        return None

    get_inboundcalculation_dom_water_oneway_veh.short_description = '计算/单车费用 国内海运-去程/veh'

    def get_inboundcalculation_dom_cc_operation_veh(self, obj):
        """ 计算, 单车费用 国内CC操作费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_cc_operation_veh'):
                return rel_obj.dom_cc_operation_veh

        return None

    get_inboundcalculation_dom_cc_operation_veh.short_description = '计算/单车费用 国内CC操作费/veh'

    def get_inboundcalculation_dom_water_backway_veh(self, obj):
        """ 计算, 单车费用 国内海运-返程/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_backway_veh'):
                return rel_obj.dom_water_backway_veh

        return None

    get_inboundcalculation_dom_water_backway_veh.short_description = '计算/单车费用 国内海运-返程/veh'

    def get_inboundcalculation_dom_water_ttl_veh(self, obj):
        """ 计算, 单车费用 国内海运/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_water_ttl_veh'):
                return rel_obj.dom_water_ttl_veh

        return None

    get_inboundcalculation_dom_water_ttl_veh.short_description = '计算/单车费用 国内海运/veh'

    def get_inboundcalculation_oversea_inland_veh(self, obj):
        """ 计算, 单车费用 海外段内陆运输/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_inland_veh'):
                return rel_obj.oversea_inland_veh

        return None

    get_inboundcalculation_oversea_inland_veh.short_description = '计算/单车费用 海外段内陆运输/veh'

    def get_inboundcalculation_oversea_cc_op_veh(self, obj):
        """ 计算, 单车费用 海外CC操作费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_cc_op_veh'):
                return rel_obj.oversea_cc_op_veh

        return None

    get_inboundcalculation_oversea_cc_op_veh.short_description = '计算/单车费用 海外CC操作费/veh'

    def get_inboundcalculation_international_ocean_veh(self, obj):
        """ 计算, 单车费用 国际海运费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'international_ocean_veh'):
                return rel_obj.international_ocean_veh

        return None

    get_inboundcalculation_international_ocean_veh.short_description = '计算/单车费用 国际海运费/veh'

    def get_inboundcalculation_dom_pull_veh(self, obj):
        """ 计算, 单车费用 国内拉动费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'dom_pull_veh'):
                return rel_obj.dom_pull_veh

        return None

    get_inboundcalculation_dom_pull_veh.short_description = '计算/单车费用 国内拉动费/veh'

    def get_inboundcalculation_certificate_veh(self, obj):
        """ 计算, 单车费用 单证费/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'certificate_veh'):
                return rel_obj.certificate_veh

        return None

    get_inboundcalculation_certificate_veh.short_description = '计算/单车费用 单证费/veh'

    def get_inboundcalculation_oversea_ocean_ttl_veh(self, obj):
        """ 计算, 单车费用 进口海运/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_ocean_ttl_veh'):
                return rel_obj.oversea_ocean_ttl_veh

        return None

    get_inboundcalculation_oversea_ocean_ttl_veh.short_description = '计算/单车费用 进口海运/veh'

    def get_inboundcalculation_oversea_air_veh(self, obj):
        """ 计算, 单车费用 进口空运/veh """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'oversea_air_veh'):
                return rel_obj.oversea_air_veh

        return None

    get_inboundcalculation_oversea_air_veh.short_description = '计算/单车费用 进口空运/veh'

    def get_inboundcalculation_inbound_ttl_veh(self, obj):
        """ 计算, 单车费用 TTL IB Cost """
        _ = self

        if hasattr(obj, 'rel_calc'):
            rel_obj = obj.rel_calc

            if hasattr(rel_obj, 'inbound_ttl_veh'):
                return rel_obj.inbound_ttl_veh

        return None

    get_inboundcalculation_inbound_ttl_veh.short_description = '计算/单车费用 TTL IB Cost'


# @admin.register(models.AEbomEntry)
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
                            header_object = models.InboundHeaderPart(
                                bom=ebom_object
                            )
                            header_object.save()

                        # operational mode object
                        if not hasattr(ebom_object, 'rel_op_mode'):
                            op_mode_object = models.InboundOperationalMode(
                                bom=ebom_object
                            )
                            op_mode_object.save()

                        # mode object
                        if not hasattr(ebom_object, 'rel_mode'):
                            mode_object = models.InboundMode(
                                bom=ebom_object
                            )
                            mode_object.save()

                        # operational package object
                        if not hasattr(ebom_object, 'rel_op_package'):
                            op_pkg_object = models.InboundOperationalPackage(
                                bom=ebom_object
                            )
                            op_pkg_object.save()

                        # package object
                        if not hasattr(ebom_object, 'rel_package'):
                            pkg_object = models.InboundPackage(
                                bom=ebom_object
                            )
                            pkg_object.save()

                        # calculation object
                        if not hasattr(ebom_object, 'rel_calc'):
                            calc_object = models.InboundCalculation(
                                bom=ebom_object
                            )
                            calc_object.save()

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


class UploadForm(ModelForm):
    """ Upload handler form. """
    def clean(self):
        """ custom validator """
        cleaned_data = super().clean()

        model_name = cleaned_data.get("model_name")
        label = cleaned_data.get("label")

        if model_name == 999 and label is None:
            self.add_error('label', "请指定一个车型!")


@admin.register(models.UploadHandler)
class UploadHandlerAdmin(admin.ModelAdmin):
    """ Upload handler admin. """
    form = UploadForm

    list_display = [
        'model_name',
        'upload_time'
    ]

    def get_fields(self, request, obj=None):
        """ If upload wide table, show label. """
        model_name = request.GET.get('model_name')
        fields = super().get_fields(request)

        if model_name != '999':
            fields.remove('label')

        return fields

    def get_readonly_fields(self, request, obj=None):
        """ Read-only fields according to request. """
        model_name = request.GET.get('model_name')

        if model_name == '1':
            return ['download_tcs_template']

        elif model_name == '2':
            return ['download_buyer_template']

        elif model_name == '999':
            return ['download_wide_template']

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

        elif obj.model_name == 999:
            # wide table
            self.parse_wide(matrix)

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

    def download_wide_template(self, obj):
        """ Download wide table template. """
        _, _ = self, obj
        return '<a href="/costsummary/sheet/wide">下载</a>'

    download_tcs_template.short_description = 'TCS 物流跟踪表模板'
    download_buyer_template.short_description = 'TCS 采购定点表模板'
    download_wide_template.short_description = '宽表模板'

    download_tcs_template.allow_tags = True
    download_buyer_template.allow_tags = True
    download_wide_template.allow_tags = True

    def parse_wide(self, matrix: list):
        """ Parse wide table """
        _ = self

        WIDE_HEADER = [
            {'r_offset': 0, 'ex_header': 'UPC', 'in_header': 'upc', 'model_name': 'ebom', 'field_name': 'upc',
             'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'FNA', 'in_header': 'fna', 'model_name': 'ebom', 'field_name': 'fna',
             'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'STRUCTURE NODE', 'in_header': 'structure_node', 'model_name': 'ebom',
             'field_name': 'structure_node', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TEC NO.', 'in_header': 'tec', 'model_name': 'ebom', 'field_name': 'tec_id',
             'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'P/N-PART NUMBER', 'in_header': 'part_number', 'model_name': 'ebom',
             'field_name': 'part_number', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'DESCRIPTION EN', 'in_header': 'description_en', 'model_name': 'ebom',
             'field_name': 'description_en', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'DESCRIPTION CN', 'in_header': 'description_cn', 'model_name': 'ebom',
             'field_name': 'description_cn', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'HEADER PART NUMBER', 'in_header': 'header_part_number', 'model_name': 'ebom',
             'field_name': 'header_part_number', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'QUANTITY', 'in_header': 'get_quantity', 'model_name': 'ebom',
             'field_name': 'quantity', 'skip': True, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'AR/EM MATERIAL INDICATOR', 'in_header': 'ar_em_material_indicator',
             'model_name': 'ebom', 'field_name': 'ar_em_material_indicator', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'WORK SHOP', 'in_header': 'work_shop', 'model_name': 'ebom',
             'field_name': 'work_shop', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'DUNS / VENDOR NUMBER', 'in_header': 'vendor_duns_number',
             'model_name': 'ebom', 'field_name': 'vendor_duns_number', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'SUPPLIER NAME', 'in_header': 'supplier_name', 'model_name': 'ebom',
             'field_name': 'supplier_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'EWO NUMBER', 'in_header': 'ewo_number', 'model_name': 'ebom',
             'field_name': 'ewo_number', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'MODEL & OPTION', 'in_header': 'model_and_option', 'model_name': 'ebom',
             'field_name': 'model_and_option', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'VPPS', 'in_header': 'vpps', 'model_name': 'ebom', 'field_name': 'vpps',
             'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '头零件', 'in_header': 'get_inboundheaderpart_head_part_number',
             'model_name': 'inboundheaderpart', 'field_name': 'head_part_number', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '头零件信息/总成供应商', 'in_header': 'get_inboundheaderpart_assembly_supplier',
             'model_name': 'inboundheaderpart', 'field_name': 'assembly_supplier', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '头零件信息/颜色件', 'in_header': 'get_inboundheaderpart_color',
             'model_name': 'inboundheaderpart', 'field_name': 'color', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/BIDDER号', 'in_header': 'get_inboundtcs_bidder_list_number',
             'model_name': 'inboundtcs', 'field_name': 'bidder_list_number', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/定点项目', 'in_header': 'get_inboundtcs_program',
             'model_name': 'inboundtcs', 'field_name': 'program', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/供应商发货地址', 'in_header': 'get_inboundtcs_supplier_ship_from_address',
             'model_name': 'inboundtcs', 'field_name': 'supplier_ship_from_address', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/报价条款', 'in_header': 'get_inboundtcs_process',
             'model_name': 'inboundtcs', 'field_name': 'process', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/运输模式', 'in_header': 'get_inboundtcs_suggest_delivery_method',
             'model_name': 'inboundtcs', 'field_name': 'suggest_delivery_method', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/SGM运输责任', 'in_header': 'get_inboundtcs_sgm_transport_duty',
             'model_name': 'inboundtcs', 'field_name': 'sgm_transport_duty', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/供应商运输责任', 'in_header': 'get_inboundtcs_supplier_transport_duty',
             'model_name': 'inboundtcs', 'field_name': 'supplier_transport_duty', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/SGM外包装责任', 'in_header': 'get_inboundtcs_sgm_returnable_duty',
             'model_name': 'inboundtcs', 'field_name': 'sgm_returnable_duty', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/供应商外包装责任', 'in_header': 'get_inboundtcs_supplier_returnable_duty',
             'model_name': 'inboundtcs', 'field_name': 'supplier_returnable_duty', 'skip': False,
             'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/外协加工业务模式', 'in_header': 'get_inboundtcs_consignment_mode',
             'model_name': 'inboundtcs', 'field_name': 'consignment_mode', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS 物流跟踪/备注', 'in_header': 'get_inboundtcs_comments',
             'model_name': 'inboundtcs', 'field_name': 'comments', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '采购信息/采购员', 'in_header': 'get_inboundbuyer_buyer',
             'model_name': 'inboundbuyer', 'field_name': 'buyer', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '采购信息/合同条款', 'in_header': 'get_inboundbuyer_contract_incoterm',
             'model_name': 'inboundbuyer', 'field_name': 'contract_incoterm', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '采购信息/供应商运费',
             'in_header': 'get_inboundbuyer_contract_supplier_transportation_cost', 'model_name': 'inboundbuyer',
             'field_name': 'contract_supplier_transportation_cost', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '采购信息/供应商外包装费', 'in_header': 'get_inboundbuyer_contract_supplier_pkg_cost',
             'model_name': 'inboundbuyer', 'field_name': 'contract_supplier_pkg_cost', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '采购信息/供应商排序费', 'in_header': 'get_inboundbuyer_contract_supplier_seq_cost',
             'model_name': 'inboundbuyer', 'field_name': 'contract_supplier_seq_cost', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块地址/FU提供的原始地址信息', 'in_header': 'get_inboundaddress_fu_address',
             'model_name': 'inboundaddress', 'field_name': 'fu_address', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块地址/MR取货地址', 'in_header': 'get_inboundaddress_mr_address',
             'model_name': 'inboundaddress', 'field_name': 'mr_address', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '国产/进口/自制', 'in_header': 'get_inboundaddress_property',
             'model_name': 'inboundaddress', 'field_name': 'property', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': '最终地址梳理/区域划分', 'in_header': 'get_inboundaddress_region_division',
             'model_name': 'inboundaddress', 'field_name': 'region_division', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终地址梳理/国家', 'in_header': 'get_inboundaddress_country',
             'model_name': 'inboundaddress', 'field_name': 'country', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终地址梳理/省', 'in_header': 'get_inboundaddress_province',
             'model_name': 'inboundaddress', 'field_name': 'province', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终地址梳理/市', 'in_header': 'get_inboundaddress_city',
             'model_name': 'inboundaddress', 'field_name': 'city', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终地址梳理/生产地址', 'in_header': 'get_inboundaddress_mfg_location',
             'model_name': 'inboundaddress', 'field_name': 'mfg_location', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运输距离-至生产厂区', 'in_header': 'get_inboundaddress_distance_to_sgm_plant',
             'model_name': 'inboundaddress', 'field_name': 'distance_to_sgm_plant', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运输距离-金桥C类', 'in_header': 'get_inboundaddress_distance_to_shanghai_cc',
             'model_name': 'inboundaddress', 'field_name': 'distance_to_shanghai_cc', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '中转库地址', 'in_header': 'get_inboundaddress_warehouse_address',
             'model_name': 'inboundaddress', 'field_name': 'warehouse_address', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '中转库运输距离', 'in_header': 'get_inboundaddress_warehouse_to_sgm_plant',
             'model_name': 'inboundaddress', 'field_name': 'warehouse_to_sgm_plant', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块模式/海运FCL/海运LCL/空运',
             'in_header': 'get_inboundoperationalmode_ckd_logistics_mode', 'model_name': 'inboundoperationalmode',
             'field_name': 'ckd_logistics_mode', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块模式/规划模式（A/B/C/自制/进口）',
             'in_header': 'get_inboundoperationalmode_planned_logistics_mode', 'model_name': 'inboundoperationalmode',
             'field_name': 'planned_logistics_mode', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块模式/是否供应商排序(JIT)',
             'in_header': 'get_inboundoperationalmode_if_supplier_seq', 'model_name': 'inboundoperationalmode',
             'field_name': 'if_supplier_seq', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块模式/结费模式（2A/2B）以此为准',
             'in_header': 'get_inboundoperationalmode_payment_mode', 'model_name': 'inboundoperationalmode',
             'field_name': 'payment_mode', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终模式/运输条款', 'in_header': 'get_inboundmode_logistics_incoterm_mode',
             'model_name': 'inboundmode', 'field_name': 'logistics_incoterm_mode', 'skip': False,
             'match_display': True},
            {'r_offset': 0, 'ex_header': '最终模式/入厂物流模式', 'in_header': 'get_inboundmode_operation_mode',
             'model_name': 'inboundmode', 'field_name': 'operation_mode', 'skip': False, 'match_display': True},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装PK NAME', 'in_header': 'get_inboundtcspackage_supplier_pkg_name',
             'model_name': 'inboundtcspackage', 'field_name': 'supplier_pkg_name', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装PKPCS', 'in_header': 'get_inboundtcspackage_supplier_pkg_pcs',
             'model_name': 'inboundtcspackage', 'field_name': 'supplier_pkg_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装PL', 'in_header': 'get_inboundtcspackage_supplier_pkg_length',
             'model_name': 'inboundtcspackage', 'field_name': 'supplier_pkg_length', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装PW', 'in_header': 'get_inboundtcspackage_supplier_pkg_width',
             'model_name': 'inboundtcspackage', 'field_name': 'supplier_pkg_width', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装PH', 'in_header': 'get_inboundtcspackage_supplier_pkg_height',
             'model_name': 'inboundtcspackage', 'field_name': 'supplier_pkg_height', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装折叠率',
             'in_header': 'get_inboundtcspackage_supplier_pkg_folding_rate', 'model_name': 'inboundtcspackage',
             'field_name': 'supplier_pkg_folding_rate', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装CUBIC/PCS',
             'in_header': 'get_inboundtcspackage_supplier_pkg_cubic_pcs', 'model_name': 'inboundtcspackage',
             'field_name': 'supplier_pkg_cubic_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/供应商出厂包装CUBIC/VEH',
             'in_header': 'get_inboundtcspackage_supplier_pkg_cubic_veh', 'model_name': 'inboundtcspackage',
             'field_name': 'supplier_pkg_cubic_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装PK NAME', 'in_header': 'get_inboundtcspackage_sgm_pkg_name',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装PKPCS', 'in_header': 'get_inboundtcspackage_sgm_pkg_pcs',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装PL', 'in_header': 'get_inboundtcspackage_sgm_pkg_length',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_length', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装PW', 'in_header': 'get_inboundtcspackage_sgm_pkg_width',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_width', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装PH', 'in_header': 'get_inboundtcspackage_sgm_pkg_height',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_height', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': 'TCS包装/先期规划包装折叠率', 'in_header': 'get_inboundtcspackage_sgm_pkg_folding_rate',
             'model_name': 'inboundtcspackage', 'field_name': 'sgm_pkg_folding_rate', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装PK NAME',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_name', 'model_name': 'inboundoperationalpackage',
             'field_name': 'supplier_pkg_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装PKPCS',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_pcs', 'model_name': 'inboundoperationalpackage',
             'field_name': 'supplier_pkg_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装PL',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_length',
             'model_name': 'inboundoperationalpackage', 'field_name': 'supplier_pkg_length', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装PW',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_width', 'model_name': 'inboundoperationalpackage',
             'field_name': 'supplier_pkg_width', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装PH',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_height',
             'model_name': 'inboundoperationalpackage', 'field_name': 'supplier_pkg_height', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/供应商包装折叠率',
             'in_header': 'get_inboundoperationalpackage_supplier_pkg_folding_rate',
             'model_name': 'inboundoperationalpackage', 'field_name': 'supplier_pkg_folding_rate', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装PK NAME',
             'in_header': 'get_inboundoperationalpackage_sgm_pkg_name', 'model_name': 'inboundoperationalpackage',
             'field_name': 'sgm_pkg_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装PKPCS', 'in_header': 'get_inboundoperationalpackage_sgm_pkg_pcs',
             'model_name': 'inboundoperationalpackage', 'field_name': 'sgm_pkg_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装PL', 'in_header': 'get_inboundoperationalpackage_sgm_pkg_length',
             'model_name': 'inboundoperationalpackage', 'field_name': 'sgm_pkg_length', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装PW', 'in_header': 'get_inboundoperationalpackage_sgm_pkg_width',
             'model_name': 'inboundoperationalpackage', 'field_name': 'sgm_pkg_width', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装PH', 'in_header': 'get_inboundoperationalpackage_sgm_pkg_height',
             'model_name': 'inboundoperationalpackage', 'field_name': 'sgm_pkg_height', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '运作功能块包装/SGM包装折叠率',
             'in_header': 'get_inboundoperationalpackage_sgm_pkg_folding_rate',
             'model_name': 'inboundoperationalpackage', 'field_name': 'sgm_pkg_folding_rate', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装PK NAME', 'in_header': 'get_inboundpackage_supplier_pkg_name',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装PKPCS', 'in_header': 'get_inboundpackage_supplier_pkg_pcs',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装PL', 'in_header': 'get_inboundpackage_supplier_pkg_length',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_length', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装PW', 'in_header': 'get_inboundpackage_supplier_pkg_width',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_width', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装PH', 'in_header': 'get_inboundpackage_supplier_pkg_height',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_height', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装折叠率', 'in_header': 'get_inboundpackage_supplier_pkg_folding_rate',
             'model_name': 'inboundpackage', 'field_name': 'supplier_pkg_folding_rate', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装CUBIC/PCS',
             'in_header': 'get_inboundpackage_supplier_pkg_cubic_pcs', 'model_name': 'inboundpackage',
             'field_name': 'supplier_pkg_cubic_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/供应商包装CUBIC/VEH',
             'in_header': 'get_inboundpackage_supplier_pkg_cubic_veh', 'model_name': 'inboundpackage',
             'field_name': 'supplier_pkg_cubic_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装PK NAME', 'in_header': 'get_inboundpackage_sgm_pkg_name',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_name', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装PKPCS', 'in_header': 'get_inboundpackage_sgm_pkg_pcs',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装PL', 'in_header': 'get_inboundpackage_sgm_pkg_length',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_length', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装PW', 'in_header': 'get_inboundpackage_sgm_pkg_width',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_width', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装PH', 'in_header': 'get_inboundpackage_sgm_pkg_height',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_height', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装折叠率', 'in_header': 'get_inboundpackage_sgm_pkg_folding_rate',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_folding_rate', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装CUBIC/PCS', 'in_header': 'get_inboundpackage_sgm_pkg_cubic_pcs',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_cubic_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/SGM包装CUBIC/VEH', 'in_header': 'get_inboundpackage_sgm_pkg_cubic_veh',
             'model_name': 'inboundpackage', 'field_name': 'sgm_pkg_cubic_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '最终包装信息/体积放大系数', 'in_header': 'get_inboundpackage_cubic_matrix',
             'model_name': 'inboundpackage', 'field_name': 'cubic_matrix', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/DDP运费/PCS', 'in_header': 'get_inboundcalculation_ddp_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'ddp_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/干线去程/PCS', 'in_header': 'get_inboundcalculation_linehaul_oneway_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_oneway_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/干线VMI/PCS', 'in_header': 'get_inboundcalculation_linehaul_vmi_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_vmi_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/干线返程/PCS', 'in_header': 'get_inboundcalculation_linehaul_backway_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_backway_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内陆运/PCS', 'in_header': 'get_inboundcalculation_dom_truck_ttl_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_truck_ttl_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内水运-去程/PCS', 'in_header': 'get_inboundcalculation_dom_water_oneway_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_water_oneway_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内CC操作费/PCS', 'in_header': 'get_inboundcalculation_dom_cc_operation_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_cc_operation_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内水运-返程/PCS', 'in_header': 'get_inboundcalculation_dom_water_backway_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_water_backway_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内水运/PCS', 'in_header': 'get_inboundcalculation_dom_water_ttl_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_water_ttl_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/海外段内陆运输/PCS', 'in_header': 'get_inboundcalculation_oversea_inland_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_inland_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/海外CC操作费/PCS', 'in_header': 'get_inboundcalculation_oversea_cc_op_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_cc_op_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国际海运费/PCS', 'in_header': 'get_inboundcalculation_international_ocean_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'international_ocean_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/国内拉动费/PCS', 'in_header': 'get_inboundcalculation_dom_pull_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'dom_pull_pcs', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单证费/PCS', 'in_header': 'get_inboundcalculation_certificate_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'certificate_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/进口海运/PCS', 'in_header': 'get_inboundcalculation_oversea_ocean_ttl_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_ocean_ttl_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/进口空运/PCS', 'in_header': 'get_inboundcalculation_oversea_air_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_air_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/IB COST', 'in_header': 'get_inboundcalculation_inbound_ttl_pcs',
             'model_name': 'inboundcalculation', 'field_name': 'inbound_ttl_pcs', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 DDP运费/VEH', 'in_header': 'get_inboundcalculation_ddp_veh',
             'model_name': 'inboundcalculation', 'field_name': 'ddp_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 干线去程/VEH', 'in_header': 'get_inboundcalculation_linehaul_oneway_veh',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_oneway_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 干线VMI/VEH', 'in_header': 'get_inboundcalculation_linehaul_vmi_veh',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_vmi_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 干线返程/VEH', 'in_header': 'get_inboundcalculation_linehaul_backway_veh',
             'model_name': 'inboundcalculation', 'field_name': 'linehaul_backway_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内陆运/VEH', 'in_header': 'get_inboundcalculation_dom_truck_ttl_veh',
             'model_name': 'inboundcalculation', 'field_name': 'dom_truck_ttl_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内海运-去程/VEH',
             'in_header': 'get_inboundcalculation_dom_water_oneway_veh', 'model_name': 'inboundcalculation',
             'field_name': 'dom_water_oneway_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内CC操作费/VEH',
             'in_header': 'get_inboundcalculation_dom_cc_operation_veh', 'model_name': 'inboundcalculation',
             'field_name': 'dom_cc_operation_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内海运-返程/VEH',
             'in_header': 'get_inboundcalculation_dom_water_backway_veh', 'model_name': 'inboundcalculation',
             'field_name': 'dom_water_backway_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内海运/VEH', 'in_header': 'get_inboundcalculation_dom_water_ttl_veh',
             'model_name': 'inboundcalculation', 'field_name': 'dom_water_ttl_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 海外段内陆运输/VEH',
             'in_header': 'get_inboundcalculation_oversea_inland_veh', 'model_name': 'inboundcalculation',
             'field_name': 'oversea_inland_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 海外CC操作费/VEH', 'in_header': 'get_inboundcalculation_oversea_cc_op_veh',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_cc_op_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国际海运费/VEH',
             'in_header': 'get_inboundcalculation_international_ocean_veh', 'model_name': 'inboundcalculation',
             'field_name': 'international_ocean_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 国内拉动费/VEH', 'in_header': 'get_inboundcalculation_dom_pull_veh',
             'model_name': 'inboundcalculation', 'field_name': 'dom_pull_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 单证费/VEH', 'in_header': 'get_inboundcalculation_certificate_veh',
             'model_name': 'inboundcalculation', 'field_name': 'certificate_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 进口海运/VEH',
             'in_header': 'get_inboundcalculation_oversea_ocean_ttl_veh', 'model_name': 'inboundcalculation',
             'field_name': 'oversea_ocean_ttl_veh', 'skip': False, 'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 进口空运/VEH', 'in_header': 'get_inboundcalculation_oversea_air_veh',
             'model_name': 'inboundcalculation', 'field_name': 'oversea_air_veh', 'skip': False,
             'match_display': False},
            {'r_offset': 0, 'ex_header': '计算/单车费用 TTL IB COST', 'in_header': 'get_inboundcalculation_inbound_ttl_veh',
             'model_name': 'inboundcalculation', 'field_name': 'inbound_ttl_veh', 'skip': False, 'match_display': False}
        ]

        # cursor
        for i in range(len(matrix)):
            all_header_found = True

            # all header field found
            for dict_obj in WIDE_HEADER:
                if 'col' not in dict_obj:
                    all_header_found = False
                    break

            if all_header_found:
                break

            row = matrix[i]

            for j in range(len(row)):
                cell = str(row[j])

                for k in range(len(WIDE_HEADER)):
                    if cell.strip().upper() == WIDE_HEADER[k]['ex_header']:
                        WIDE_HEADER[k]['col'] = j
                        WIDE_HEADER[k]['row'] = i

        # check header row
        data_row = None

        for dict_obj in WIDE_HEADER:
            if 'col' not in dict_obj or 'row' not in dict_obj:
                raise Http404(f'数据列{dict_obj["ex_header"]}没有找到')
            else:
                if data_row is not None:
                    if dict_obj['row'] - dict_obj['r_offset'] != data_row:
                        raise Http404('Excel 格式不正确.')
                else:
                    data_row = dict_obj['row'] + dict_obj['r_offset']

        # start parsing row
        start_row = data_row + 1

        # look up field
        lookup_col = None

        for dict_obj in WIDE_HEADER:
            if dict_obj['in_header'].upper() == 'part_number'.upper():
                lookup_col = dict_obj['col']
                break

        assert lookup_col

        # params context
        model_params = dict()

        for dict_obj in WIDE_HEADER:
            if dict_obj['model_name'] not in model_params:
                model_params[dict_obj['model_name']] = dict()

        print(model_params)

        # parse list of list
        for row in matrix[start_row:]:
            lookup_value = row[lookup_col]

            # if no actual value
            if lookup_value == '':
                continue

            # parse row cells
            model_params_instance = model_params

            for dict_obj in WIDE_HEADER:
                if not dict_obj['skip'] and dict_obj['col'] != lookup_col:

                    if not dict_obj['match_display']:
                        model_params_instance[dict_obj['model_name']][dict_obj['field_name']] = row[dict_obj['col']]

                    else:
                        choice = getattr(
                            apps.get_model('costsummary', dict_obj['model_name']),
                            dict_obj['field_name'] + '_choice'
                        )

                        for int_val, str_val in choice:
                            if row[dict_obj['col']].strip().upper() == str_val.upper():
                                model_params_instance[dict_obj['model_name']][dict_obj['field_name']] = int_val
                                break

            # match ebom object
            ebom_objects = models.Ebom.objects.filter(part_number=lookup_value)

            if not ebom_objects:
                new_ebom_object = models.Ebom(
                    label=None,
                    part_number=lookup_value
                )
                new_ebom_object.save()

                ebom_objects = [new_ebom_object]

            # save ebom object and related objects
            for ebom_object in ebom_objects:

                # ebom object
                native_params = model_params_instance['ebom']
                model_params_instance.pop('ebom')

                for attribute in native_params:
                    if native_params[attribute] == '':
                        native_params[attribute] = None
                    setattr(ebom_object, attribute, native_params[attribute])

                ebom_object.save()

                # related object


@admin.register(models.Constants)
class ConstantsAdmin(admin.ModelAdmin):
    """ Constants """
    list_display = (
        'constant_key',
        'constant_value_float'
    )

    search_fields = [
        'constant_key'
    ]


@admin.register(models.InboundOverseaRate)
class InboundOverseaRateAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'region',
        'base',
        'cc',
        'export_harbor',
        'definition_harbor',
        'os_dm_rate',
        'cc_rate',
        'euro_doc_rate',
        'os_40h_rate',
        'os_40h_danger_rate',
        'inter_40h_rate',
        'inter_40h_danger_rate',
        'dm_40h_rate',
        'dm_40h_danger_rate',
        'delegate',
        'delegate_danger',
        'vol_40h',
        'load_rate',
        'cpc',
        'cpc_danger',
    )

    search_fields = [
        'region',
        'base',
        'cc',
    ]


@admin.register(models.InboundCcLocations)
class InboundCcLocationsAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'cc_group',
        'cn_location_name',
        'en_location_name',
        'currency_unit',
        'per_cbm',
        'cc'
    )

    search_fields = [
        'cc_group',
        'cn_location_name',
        'en_location_name',
        'cc'
    ]


@admin.register(models.InboundCcOperation)
class InboundCcOperationAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'cc',
        'cbm_in_usd',
        'load_ratio',
    )


@admin.register(models.InboundDangerPackage)
class InboundCcDangerAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'from_to_type',
        'from_one',
        'to_one',
        'standard',
        'danger',
    )

    list_filter = (
        'from_to_type',
        'from_one',
        'to_one'
    )


@admin.register(models.InboundCCSupplierRate)
class InboundCCSupplierRateAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'supplier_duns',
        'supplier_name',
        'pick_up_location',
        'state',
        'city',
        'zip_code',
        'kilometers',
        'rate',
        'cpc',
    )

    list_filter = (
        'supplier_duns',
        'supplier_name',
    )


@admin.register(models.InboundSupplierRate)
class InboundSupplierRateAdmin(admin.ModelAdmin):
    """ Oversea rate. """
    list_display = (
        'supplier',
        'base',
        'pickup_location',
        'duns',
        'forward_rate',
        'backward_rate',
        'manage_ratio',
        'vmi_rate',
        'oneway_km',
        'address',
    )

    list_filter = (
        'base',
    )


@admin.register(models.TruckRate)
class TruckRateAdmin(admin.ModelAdmin):
    """ Truck rate admin class """
    list_display = (
        'name',
        'cube',
        'loading_ratio',
        'capable_cube',
        'avg_speed',
        'load_time',
        'oil_price',
        'charter_price',
        'overdue_price',
        'rate_per_km'
    )

    search_fields = [
        'name'
    ]

    list_filter = (
        'cube',
        'loading_ratio',
        'capable_cube',
        'avg_speed',
        'load_time'
    )


@admin.register(models.RegionRouteRate)
class RegionRouteRateAdmin(admin.ModelAdmin):
    """ Region route rate admin class """
    list_display = (
        'region_or_route',
        'related_base',
        'parent_region',
        'km',
        'price_per_cube',
        'reference',
    )

    search_fields = [
        'region_or_route',
    ]

    list_filter = (
        'related_base',
        'parent_region',
        'reference',
    )


@admin.register(models.UnsortedInboundBuyer)
class UnsortedInboundBuyer(admin.ModelAdmin):
    list_display = (
        'part_number',
        'part_name',
        'duns',
        'supplier_name',
        'buyer',
        'measure_unit',
        'currency_unit',
        'area',
        'inner_pkg_cost',
        'inner_pkg_owner',
        'outer_pkg_cost',
        'outer_pkg_owner',
        'carrier',
        'transport_cost',
        'transport_mode',
        'whether_seq',
        'seq_cost',
        'location',
        'bidderlist_no',
        'project',
    )

    search_fields = [
        'part_number',
        'duns',
        'buyer',
    ]

    list_filter = [
        'area',
    ]
