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


@admin.register(models.Ebom)
class EbomAdmin(admin.ModelAdmin):
    """ EBOM admin. """
    change_list_template = 'costsummary/change_list.html'

    list_per_page = 8

    list_display = (
        'part_number',
        'label',
        'upc',
        'fna',
        'structure_node',
        'description_en',
        'description_cn',
        'header_part_number',
        'ar_em_material_indicator',
        'work_shop',
        'duns',
        'vendor_duns_number',
        'supplier_name',
        'model_and_option',
        'vpps',
        'get_inboundaddress_fu_address', 'get_inboundaddress_mr_address', 'get_inboundaddress_property',
        'get_inboundaddress_region_division', 'get_inboundaddress_country',
        'get_inboundaddress_province', 'get_inboundaddress_city', 'get_inboundaddress_mfg_location',
        'get_inboundaddress_distance_to_sgm_plant',
        'get_inboundaddress_distance_to_shanghai_cc', 'get_inboundaddress_warehouse_address',
        'get_inboundbuyer_buyer', 'get_inboundbuyer_contract_incoterm',
        'get_inboundbuyer_contract_supplier_transportation_cost', 'get_inboundbuyer_contract_supplier_pkg_cost',
        'get_inboundbuyer_contract_supplier_seq_cost', 'get_inboundheaderpart_head_part_number',
        'get_inboundheaderpart_assembly_supplier', 'get_inboundheaderpart_color',
        'get_inboundmode_logistics_incoterm_mode', 'get_inboundmode_operation_mode',
        'get_inboundoperationalmode_ckd_logistics_mode', 'get_inboundoperationalmode_planned_logistics_mode',
        'get_inboundoperationalmode_if_supplier_seq', 'get_inboundoperationalmode_payment_mode',
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
        'get_inboundpackage_sgm_pkg_cubic_veh', 'get_inboundpackage_cubic_matrix', 'get_inboundtcs_bidder_list_number',
        'get_inboundtcs_program', 'get_inboundtcs_supplier_ship_from_address', 'get_inboundtcs_process',
        'get_inboundtcs_suggest_delivery_method', 'get_inboundtcs_sgm_transport_duty',
        'get_inboundtcs_supplier_transport_duty', 'get_inboundtcs_sgm_returnable_duty',
        'get_inboundtcs_supplier_returnable_duty', 'get_inboundtcs_consignment_mode', 'get_inboundtcs_comments',
        'get_inboundtcspackage_supplier_pkg_name', 'get_inboundtcspackage_supplier_pkg_pcs',
        'get_inboundtcspackage_supplier_pkg_length', 'get_inboundtcspackage_supplier_pkg_width',
        'get_inboundtcspackage_supplier_pkg_height', 'get_inboundtcspackage_supplier_pkg_folding_rate',
        'get_inboundtcspackage_supplier_pkg_cubic_pcs', 'get_inboundtcspackage_supplier_pkg_cubic_veh',
        'get_inboundtcspackage_sgm_pkg_name', 'get_inboundtcspackage_sgm_pkg_pcs',
        'get_inboundtcspackage_sgm_pkg_length', 'get_inboundtcspackage_sgm_pkg_width',
        'get_inboundtcspackage_sgm_pkg_height', 'get_inboundtcspackage_sgm_pkg_folding_rate',
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
        InboundHeaderPartInline,
        InboundTCSInline,
        InboundBuyerInline,
        InboundAddressInline,
        InboundTCSPackageInline,
        InboundOperationalModeInline,
        InboundModeInline,
        InboundOperationalPackageInline,
        InboundPackageInline,
    ]

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
                return rel_obj.property

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
                return rel_obj.logistics_incoterm_mode

        return None

    get_inboundmode_logistics_incoterm_mode.short_description = '最终模式/运输条款'

    def get_inboundmode_operation_mode(self, obj):
        """ 最终模式梳理 信息, 入厂物流模式 """
        _ = self

        if hasattr(obj, 'rel_mode'):
            rel_obj = obj.rel_mode

            if hasattr(rel_obj, 'operation_mode'):
                return rel_obj.operation_mode

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
                return rel_obj.process

        return None

    get_inboundtcs_process.short_description = 'TCS 物流跟踪/报价条款'

    def get_inboundtcs_suggest_delivery_method(self, obj):
        """ TCS 物流跟踪 信息, 运输模式 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'suggest_delivery_method'):
                return rel_obj.suggest_delivery_method

        return None

    get_inboundtcs_suggest_delivery_method.short_description = 'TCS 物流跟踪/运输模式'

    def get_inboundtcs_sgm_transport_duty(self, obj):
        """ TCS 物流跟踪 信息, SGM运输责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'sgm_transport_duty'):
                return rel_obj.sgm_transport_duty

        return None

    get_inboundtcs_sgm_transport_duty.short_description = 'TCS 物流跟踪/SGM运输责任'

    def get_inboundtcs_supplier_transport_duty(self, obj):
        """ TCS 物流跟踪 信息, 供应商运输责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'supplier_transport_duty'):
                return rel_obj.supplier_transport_duty

        return None

    get_inboundtcs_supplier_transport_duty.short_description = 'TCS 物流跟踪/供应商运输责任'

    def get_inboundtcs_sgm_returnable_duty(self, obj):
        """ TCS 物流跟踪 信息, SGM外包装责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'sgm_returnable_duty'):
                return rel_obj.sgm_returnable_duty

        return None

    get_inboundtcs_sgm_returnable_duty.short_description = 'TCS 物流跟踪/SGM外包装责任'

    def get_inboundtcs_supplier_returnable_duty(self, obj):
        """ TCS 物流跟踪 信息, 供应商外包装责任 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'supplier_returnable_duty'):
                return rel_obj.supplier_returnable_duty

        return None

    get_inboundtcs_supplier_returnable_duty.short_description = 'TCS 物流跟踪/供应商外包装责任'

    def get_inboundtcs_consignment_mode(self, obj):
        """ TCS 物流跟踪 信息, 外协加工业务模式 """
        _ = self

        if hasattr(obj, 'rel_tcs'):
            rel_obj = obj.rel_tcs

            if hasattr(rel_obj, 'consignment_mode'):
                return rel_obj.consignment_mode

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

                        # header part object
                        if not hasattr(ebom_object, 'rel_package'):
                            pkg_object = models.InboundPackage(
                                bom=ebom_object
                            )
                            pkg_object.save()

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
