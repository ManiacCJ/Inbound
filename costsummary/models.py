from datetime import timedelta, date
import math

from django.db import models
from django.contrib.auth.models import User

# constants
BASE_CHOICE = (
    (0, 'JQ'),
    (1, 'DY'),
    (3, 'NS'),
    (4, 'WH'),
    (10, 'PT'),
    (-1, '3rd Party')
)


# Create your models here.
class TecCore(models.Model):
    """ Tec id & part name (English). """
    tec_id = models.IntegerField(primary_key=True, verbose_name='TEC No.')
    common_part_name = models.CharField(unique=True, max_length=128, verbose_name='Common Part Name')
    mgo_part_name_list = models.CharField(max_length=512, verbose_name='MGO Part Name & Tech Example DMU')

    class Meta:
        verbose_name = 'TEC Part Name'
        verbose_name_plural = 'TEC Part Name'

    def __str__(self):
        return str(self.tec_id)

    def save(self, *args, **kwargs):
        """ Override default save action. """
        self.common_part_name = self.common_part_name.upper()  # upper case.
        self.mgo_part_name = self.mgo_part_name_list.upper()

        super().save(self, *args, **kwargs)


class Supplier(models.Model):
    """ Supplier information. Corresponding sheet: MR大合集"""
    original_source = models.CharField(max_length=64, null=True, blank=True, verbose_name='数据来源')

    is_mono_address = models.NullBooleanField(verbose_name='是否唯一出货地址')
    is_promised_address = models.NullBooleanField(verbose_name='是否承诺地址')

    duns = models.CharField(max_length=32, verbose_name='DUNS编码')
    name = models.CharField(max_length=64, verbose_name='取货供应商')
    address = models.CharField(max_length=64, verbose_name='取货地址')

    post_code = models.CharField(max_length=16, verbose_name='邮编')
    region = models.CharField(max_length=16, verbose_name='区域划分')
    province = models.CharField(max_length=16, verbose_name='省份')
    district = models.CharField(max_length=16, verbose_name='区域')

    comment = models.TextField(null=True, blank=True, verbose_name='备注(生产零件,项目等)')
    is_removable = models.NullBooleanField(verbose_name='后续是否去除')

    class Meta:
        verbose_name = '供应商'
        verbose_name_plural = '供应商'

    def __str__(self):
        return self.name + ' -- ' + self.address


class SupplierDistance(models.Model):
    """ The distances from supplier to bases. """
    base = models.IntegerField(choices=BASE_CHOICE)
    distance = models.FloatField(null=True, blank=True)

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    comment = models.CharField(max_length=16, null=True, blank=True, verbose_name='线路备注')

    class Meta:
        verbose_name = '供应商距离'
        verbose_name_plural = '供应商距离'

    def __str__(self):
        return '供应商 %s 到 %s 基地距离' % (self.supplier.duns, self.get_base_display())


class NominalLabelMapping(models.Model):
    """ Map book, plant code, model to vehicle label. """
    value = models.CharField(max_length=128, verbose_name='车型名称')

    # composite primary keys
    book = models.CharField(max_length=4, verbose_name='车系', null=True, blank=True)
    plant_code = models.CharField(max_length=8, verbose_name='分厂', null=True, blank=True)
    model = models.CharField(max_length=64, verbose_name='模型', null=True, blank=True)

    class Meta:
        verbose_name = '车型映射'
        verbose_name_plural = '车型映射'

    def __str__(self):
        if self.model is not None:
            return "{0}({1}, {2}, {3})".format(self.value, self.book, self.plant_code, self.model)
        else:
            return self.value


class Ebom(models.Model):
    """ EBOM data. """
    label = models.ForeignKey(NominalLabelMapping, null=True, on_delete=models.CASCADE, verbose_name='车型')
    conf = models.CharField(max_length=64, default=None, null=True, blank=True, verbose_name='配置')
    veh_pt_choice = ((1, 'VEH'), (2, 'PT'))
    veh_pt = models.IntegerField(verbose_name='VEH or PT', default=1, choices=veh_pt_choice)

    # other fields
    upc = models.CharField(max_length=20, verbose_name='UPC')
    fna = models.CharField(max_length=20, verbose_name='FNA')

    structure_node = models.CharField(max_length=64, null=True, blank=True,
                                      default=None, verbose_name='Structure Node')

    part_number = models.CharField(max_length=32, verbose_name='P/N-Part Number')
    description_en = models.CharField(max_length=128, verbose_name='Description EN')
    description_cn = models.CharField(max_length=128, null=True, blank=True, verbose_name='Description CN')

    header_part_number = models.CharField(max_length=32, null=True, blank=True, verbose_name='Header Part Number')
    quantity = models.IntegerField(null=True, blank=True, verbose_name='Quantity')

    ar_em_material_indicator = models.CharField(max_length=16, null=True, blank=True,
                                                verbose_name='AR/EM Material Indicator')

    work_shop = models.CharField(max_length=16, null=True, blank=True, verbose_name='Work Shop')
    vendor_duns_number = models.CharField(max_length=32, null=True, blank=True, verbose_name='Duns / vendor number')
    supplier_name = models.CharField(max_length=128, null=True, blank=True, verbose_name='Supplier Name')
    ewo_number = models.CharField(max_length=20, null=True, blank=True, verbose_name='Ewo Number')
    model_and_option = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Model & Option')
    vpps = models.CharField(max_length=60, null=True, blank=True, verbose_name='VPPS')

    # dependent field
    duns = models.CharField(max_length=32, null=True, blank=True, editable=False)
    tec = models.ForeignKey(TecCore, null=True, blank=True, verbose_name='TEC No.', on_delete=None)

    class Meta:
        verbose_name = 'EBOM 数据'
        verbose_name_plural = 'EBOM 数据'

        indexes = [
            models.Index(fields=['conf', 'part_number', 'duns'])
        ]

    def __str__(self):
        return str(self.part_number)

    def save(self, *args, **kwargs):
        if self.vendor_duns_number:
            try:
                self.duns = int(self.vendor_duns_number)

            except ValueError:
                try:
                    _duns = self.vendor_duns_number.split('_')
                    self.duns = int(_duns[0])

                except ValueError as e:
                    print(e)
                    self.duns = None

        if self.description_en:
            self.tec = TecCore.objects.filter(
                models.Q(mgo_part_name_list__contains=self.description_en.upper()) | models.Q(
                    common_part_name__contains=self.description_en.upper())).first()

        super().save(*args, **kwargs)


class EbomConfiguration(models.Model):
    """ Configuration of EBOM """
    bom = models.ForeignKey(Ebom, on_delete=models.CASCADE, related_name='rel_configuration')

    package = models.CharField(null=True, blank=True, max_length=64)
    order_sample = models.CharField(null=True, blank=True, max_length=16)
    quantity = models.IntegerField(default=0, verbose_name='Quantity')

    def concat(self):
        """ Configuration string """
        conf_items = []

        label = self.bom.label
        conf_items.append(label.model if label else '')
        conf_items += [self.package if self.package else ''] * 2
        conf_items.append(self.order_sample if self.order_sample else '')

        return '-'.join(conf_items)

    class Meta:
        verbose_name = 'EBOM 配置数据'
        verbose_name_plural = 'EBOM 配置数据'

        # composite primary key constraints
        # unique_together = ("bom", "package", "order_sample")

    def __str__(self):
        return self.concat()


class AEbomEntry(models.Model):
    """ Entry to load raw ebom data. """
    label = models.ForeignKey(NominalLabelMapping, null=True, on_delete=models.CASCADE, verbose_name='车型')
    model_year = models.IntegerField(null=True, blank=True)

    row_count = models.IntegerField(null=True, blank=True)

    user = models.ForeignKey(User, null=True, blank=True, default=None, on_delete=None)
    whether_loaded = models.BooleanField(default=False, verbose_name='是否已加载')
    etl_time = models.DateField(auto_now_add=True)
    loaded_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'EBOM 入口'
        verbose_name_plural = 'EBOM 入口'

    def __str__(self):
        return str(self.label)

    def save(self, *args, **kwargs):
        # if not loaded, set loaded time to null
        if not self.whether_loaded:
            self.loaded_time = None
            self.user = None

        super().save(*args, **kwargs)


class UnsortedInboundTCS(models.Model):
    """ TCS data. """
    part_number = models.CharField(max_length=32, verbose_name='零件号')
    duns = models.CharField(max_length=32, null=True, blank=True, verbose_name='DUNS')

    bidder_list_number = models.CharField(max_length=64, null=True, blank=True, verbose_name='Bidder号')
    program = models.CharField(max_length=64, null=True, blank=True, verbose_name='定点项目')
    supplier_ship_from_address = models.CharField(max_length=128, null=True, blank=True, verbose_name='供应商发货地址')

    process_choice = (
        (0, 'Dom_FCA_MfgLoc'),
        (1, 'Dom_DDP_Plant'),
        (2, 'Dom_FCA_MfgLoc_with_SEQ'),
        (3, 'Dom_DDP_Plant_with_SEQ'),
        (4, 'Dom_DDP_Seq_Supplier_with_SEQ'),
        (5, 'Dom_DDP_Consignee'),
        (6, 'Dom_FCA_Supplier_Warehouse'),
        (7, 'Int_FCA_Country_of_Origin'),
        (8, 'Int_EXW_MfgLoc'),
        (9, 'Int_FOB_port_of_shipment'),
        (10, 'Dom_DDP_Plant_with_SEQ___FCA_MfgLoc_before_SEQ'),
        (11, 'Dom_DDP_Tier_1___Applied_Tier_2'),

    )
    process = models.IntegerField(null=True, blank=True, verbose_name='报价条款', choices=process_choice)

    suggest_delivery_method_choice = (
        (0, '由SGM-Milkrun上门提货'),
        (1, '由供应商直运到SGM指定生产厂区'),
        (2, '供应商排序后由SGM-Milkrun上门提货'),
        (3, '由供应商排序后直运到SGM指定生产厂区'),
        (4, '由供应商负责直运至排序供应商处，SGM负责从排序供应商处运至SGM工厂'),
        (5, '由供应商直运到SGM指定第三方装配商处'),
        (6, '由供应商自运至中转库，SGM-Milkrun至中转库提货'),
        (7, 'SGM Overseas 3rd party logistics provider pick up parts at supplier\'s location'),
        (8, 'SGM Overseas 3rd party logistics provider pick up parts at supplier\'s location'),
        (9, 'SGM Overseas 3rd party logistics provider pick up parts at port of shipment'),
        (10, '由SGM负责直运至排序供应商处,排序后由供应商负责从排序供应商处至SGM工厂'),
        (11, '由供应商直运到SGM指定一级供应商处'),
        (100, '由Milkrun上门提货至集散中心，SGM水运至异地厂区'),
        (200, '由SGM上门提货,干线运输(陆运)'),
        (300, '由SGM上门提货,干线运输(烟大线)'),
        (400, 'SGM负责整集装箱上门提货，水运至异地厂区'),
        (102, '由Milkrun直运到排序供应商处,排序后由Milkrun运到SGM指定生产厂区'),
        (105, '包装形式和交货频次最终由供应商与第三方装配商协商确定'),
        (106, '供应商负责包括但不限于：生产地至中转库(SGM认可供应商园区)运输、外包装、中转库(含/不含翻包装)。'
              'SGM负责中转库后运输和外包装××(LL*WW*HH mm，**pcs/pac)。')
    )
    suggest_delivery_method = models.IntegerField(null=True, blank=True, verbose_name='运输模式',
                                                  choices=suggest_delivery_method_choice)

    sgm_transport_duty_choice = (
        (0, '从供应商处至SGM厂区'),
        (1, '无'),
        (2, '从排序商至SGM厂区'),
        (3, '从供应商处至第三方装配商'),
        (4, '从中转库处至第三方装配商'),
        (5, '从中转库至SGM厂区'),
        (6, 'from Overseas supplier Loc. to SGM plant'),
        (7, 'from port of shipment to SGM plant'),
        (8, '从供应商处至排序供应商处'),
    )
    sgm_transport_duty = models.IntegerField(null=True, blank=True, verbose_name='SGM运输责任',
                                             choices=sgm_transport_duty_choice)

    supplier_transport_duty_choice = (
        (0, '无'),
        (1, '从供应商处至SGM厂区'),
        (2, '从供应商至排序商处'),
        (3, '从供应商处至排序供应商处，从排序供应商处至SGM厂区'),
        (4, '从供应商处至SGM指定第三方装配商处'),
        (5, '从供应商处至中转库'),
        (6, 'No'),
        (7, '从供应商处至SGM指定一级供应商处'),
        (8, '从排序供应商处至SGM厂区'),
    )
    supplier_transport_duty = models.IntegerField(null=True, blank=True, verbose_name='供应商运输责任',
                                                  choices=supplier_transport_duty_choice)

    sgm_returnable_duty_choice = (
        (0, 'SGM负责全程外包装'),
        (1, '无'),
        (2, 'SGM负责翻包装后外包装'),
        (3, 'SGM负责排序点后排序外包装'),
        (4, 'SGM负责中转库后外包装'),
        (5, 'No'),
    )
    sgm_returnable_duty = models.IntegerField(null=True, blank=True, verbose_name='SGM外包装责任',
                                              choices=sgm_returnable_duty_choice)

    supplier_returnable_duty_choice = (
        (0, '无'),
        (1, '供应商负责全程外包装'),
        (2, '供应商负责翻包装前外包装'),
        (3, '供应商负责排序点前运输外包装'),
        (4, '供应商负责从供应商处至中转库前的外包装'),
        (5, 'Supplier be responsible for expendable packaging'),
    )
    supplier_returnable_duty = models.IntegerField(null=True, blank=True, verbose_name='供应商外包装责任',
                                                   choices=supplier_returnable_duty_choice)

    consignment_mode_choice = ((0, 'CSMT 2B'), (1, 'CSMT 2A'), (2, 'Not Apply'))
    consignment_mode = models.IntegerField(null=True, blank=True, verbose_name='外协加工业务模式',
                                           choices=consignment_mode_choice)

    comments = models.TextField(null=True, blank=True, verbose_name='备注')

    supplier_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='供应商包装PK Name')
    supplier_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='供应商包装PKPCS')
    supplier_pkg_length = models.FloatField(null=True, blank=True, verbose_name='供应商包装PL')
    supplier_pkg_width = models.FloatField(null=True, blank=True, verbose_name='供应商包装PW')
    supplier_pkg_height = models.FloatField(null=True, blank=True, verbose_name='供应商包装PH')

    sgm_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='SGM包装PK Name')
    sgm_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='SGM包装PKPCS')
    sgm_pkg_length = models.FloatField(null=True, blank=True, verbose_name='SGM包装PL')
    sgm_pkg_width = models.FloatField(null=True, blank=True, verbose_name='SGM包装PW')
    sgm_pkg_height = models.FloatField(null=True, blank=True, verbose_name='SGM包装PH')

    class Meta:
        verbose_name = '物流跟踪 信息'
        verbose_name_plural = '物流跟踪 信息'

        indexes = [
            models.Index(fields=['part_number', 'duns'])
        ]

    def __str__(self):
        return '零件 %s' % str(self.part_number)


class InboundTCS(models.Model):
    """ TCS data. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_tcs')

    bidder_list_number = models.CharField(max_length=64, null=True, blank=True, verbose_name='Bidder号')
    program = models.CharField(max_length=64, null=True, blank=True, verbose_name='定点项目')
    supplier_ship_from_address = models.CharField(max_length=128, null=True, blank=True, verbose_name='供应商发货地址')

    process_choice = (
        (0, 'Dom_FCA_MfgLoc'),
        (1, 'Dom_DDP_Plant'),
        (2, 'Dom_FCA_MfgLoc_with_SEQ'),
        (3, 'Dom_DDP_Plant_with_SEQ'),
        (4, 'Dom_DDP_Seq_Supplier_with_SEQ'),
        (5, 'Dom_DDP_Consignee'),
        (6, 'Dom_FCA_Supplier_Warehouse'),
        (7, 'Int_FCA_Country_of_Origin'),
        (8, 'Int_EXW_MfgLoc'),
        (9, 'Int_FOB_port_of_shipment'),
        (10, 'Dom_DDP_Plant_with_SEQ___FCA_MfgLoc_before_SEQ'),
        (11, 'Dom_DDP_Tier_1___Applied_Tier_2'),

    )
    process = models.IntegerField(null=True, blank=True, verbose_name='报价条款', choices=process_choice)

    suggest_delivery_method_choice = (
        (0, '由SGM-Milkrun上门提货'),
        (1, '由供应商直运到SGM指定生产厂区'),
        (2, '供应商排序后由SGM-Milkrun上门提货'),
        (3, '由供应商排序后直运到SGM指定生产厂区'),
        (4, '由供应商负责直运至排序供应商处，SGM负责从排序供应商处运至SGM工厂'),
        (5, '由供应商直运到SGM指定第三方装配商处'),
        (6, '由供应商自运至中转库，SGM-Milkrun至中转库提货'),
        (7, 'SGM Overseas 3rd party logistics provider pick up parts at supplier\'s location'),
        (8, 'SGM Overseas 3rd party logistics provider pick up parts at supplier\'s location'),
        (9, 'SGM Overseas 3rd party logistics provider pick up parts at port of shipment'),
        (10, '由SGM负责直运至排序供应商处,排序后由供应商负责从排序供应商处至SGM工厂'),
        (11, '由供应商直运到SGM指定一级供应商处'),
        (100, '由Milkrun上门提货至集散中心，SGM水运至异地厂区'),
        (200, '由SGM上门提货,干线运输(陆运)'),
        (300, '由SGM上门提货,干线运输(烟大线)'),
        (400, 'SGM负责整集装箱上门提货，水运至异地厂区'),
        (102, '由Milkrun直运到排序供应商处,排序后由Milkrun运到SGM指定生产厂区'),
        (105, '包装形式和交货频次最终由供应商与第三方装配商协商确定'),
        (106, '供应商负责包括但不限于：生产地至中转库(SGM认可供应商园区)运输、外包装、中转库(含/不含翻包装)。'
              'SGM负责中转库后运输和外包装××(LL*WW*HH mm，**pcs/pac)。')
    )
    suggest_delivery_method = models.IntegerField(null=True, blank=True, verbose_name='运输模式',
                                                  choices=suggest_delivery_method_choice)

    sgm_transport_duty_choice = (
        (0, '从供应商处至SGM厂区'),
        (1, '无'),
        (2, '从排序商至SGM厂区'),
        (3, '从供应商处至第三方装配商'),
        (4, '从中转库处至第三方装配商'),
        (5, '从中转库至SGM厂区'),
        (6, 'from Overseas supplier Loc. to SGM plant'),
        (7, 'from port of shipment to SGM plant'),
        (8, '从供应商处至排序供应商处'),
    )
    sgm_transport_duty = models.IntegerField(null=True, blank=True, verbose_name='SGM运输责任',
                                             choices=sgm_transport_duty_choice)

    supplier_transport_duty_choice = (
        (0, '无'),
        (1, '从供应商处至SGM厂区'),
        (2, '从供应商至排序商处'),
        (3, '从供应商处至排序供应商处，从排序供应商处至SGM厂区'),
        (4, '从供应商处至SGM指定第三方装配商处'),
        (5, '从供应商处至中转库'),
        (6, 'No'),
        (7, '从供应商处至SGM指定一级供应商处'),
        (8, '从排序供应商处至SGM厂区'),
    )
    supplier_transport_duty = models.IntegerField(null=True, blank=True, verbose_name='供应商运输责任',
                                                  choices=supplier_transport_duty_choice)

    sgm_returnable_duty_choice = (
        (0, 'SGM负责全程外包装'),
        (1, '无'),
        (2, 'SGM负责翻包装后外包装'),
        (3, 'SGM负责排序点后排序外包装'),
        (4, 'SGM负责中转库后外包装'),
        (5, 'No'),
    )
    sgm_returnable_duty = models.IntegerField(null=True, blank=True, verbose_name='SGM外包装责任',
                                              choices=sgm_returnable_duty_choice)

    supplier_returnable_duty_choice = (
        (0, '无'),
        (1, '供应商负责全程外包装'),
        (2, '供应商负责翻包装前外包装'),
        (3, '供应商负责排序点前运输外包装'),
        (4, '供应商负责从供应商处至中转库前的外包装'),
        (5, 'Supplier be responsible for expendable packaging'),
    )
    supplier_returnable_duty = models.IntegerField(null=True, blank=True, verbose_name='供应商外包装责任',
                                                   choices=supplier_returnable_duty_choice)

    consignment_mode_choice = ((0, 'CSMT 2B'), (1, 'CSMT 2A'), (2, 'Not Apply'))
    consignment_mode = models.IntegerField(null=True, blank=True, verbose_name='外协加工业务模式',
                                           choices=consignment_mode_choice)

    comments = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = 'TCS 物流跟踪 信息'
        verbose_name_plural = 'TCS 物流跟踪 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        if self.bom.duns is not None:
            matched_object: UnsortedInboundTCS = UnsortedInboundTCS.objects.filter(
                part_number=self.bom.part_number, duns=self.bom.duns).order_by('-id').first()

            if matched_object:
                for field in matched_object._meta.get_fields():
                    if field.name == 'id':
                        continue

                    if hasattr(self, field.name):
                        field_val = getattr(self, field.name)

                        if field_val is None:
                            setattr(self, field.name, getattr(matched_object, field.name))

        super().save(*args, **kwargs)


class UnsortedInboundBuyer(models.Model):
    """ Buyer not related to bom. """
    part_number = models.CharField(max_length=32, verbose_name='零件号')
    part_name = models.CharField(max_length=128, verbose_name='零件名称')
    duns = models.CharField(max_length=16, verbose_name='合同DUNS')
    supplier_name = models.CharField(max_length=128, verbose_name='合同供应商名称', null=True, blank=True)
    buyer = models.CharField(max_length=64, null=True, blank=True, verbose_name='采购员')
    measure_unit = models.CharField(max_length=8, null=True, blank=True, verbose_name='计量单位')
    currency_unit = models.CharField(max_length=8, null=True, blank=True, verbose_name='货币单位')
    area = models.IntegerField(null=True, blank=True, choices=BASE_CHOICE, verbose_name='台账区域')
    inner_pkg_cost = models.FloatField(null=True, blank=True, verbose_name='内包装费用')
    inner_pkg_owner = models.CharField(null=True, blank=True, max_length=16, verbose_name='内包装所有者')
    outer_pkg_cost = models.FloatField(null=True, blank=True, verbose_name='外包装费用')
    outer_pkg_owner = models.CharField(null=True, blank=True, max_length=16, verbose_name='外包装所有者')
    carrier = models.CharField(null=True, blank=True, max_length=64, verbose_name='运输方')
    transport_cost = models.FloatField(null=True, blank=True, verbose_name='运输费')
    transport_mode = models.CharField(null=True, blank=True, max_length=16, verbose_name='运输模式')
    whether_seq = models.NullBooleanField(verbose_name='运输是否排序')
    seq_cost = models.FloatField(null=True, blank=True, verbose_name='排序费用')
    location = models.CharField(null=True, blank=True, max_length=64, verbose_name='LOCATION')
    bidderlist_no = models.CharField(null=True, blank=True, max_length=32, verbose_name='Bidderlist No')
    project = models.CharField(null=True, blank=True, max_length=64, verbose_name='项目名')

    class Meta:
        verbose_name = '采购台账 信息'
        verbose_name_plural = '采购台账 信息'
        indexes = [
            models.Index(fields=['area', 'part_number', 'duns'])
        ]

    def __str__(self):
        return self.part_number


class InboundBuyer(models.Model):
    """ Buyer data. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_buyer')

    buyer = models.CharField(max_length=64, null=True, blank=True, verbose_name='采购员')
    contract_incoterm = models.CharField(max_length=64, null=True, blank=True, verbose_name='合同条款')
    contract_supplier_transportation_cost = models.FloatField(null=True, blank=True, verbose_name='供应商运费')
    contract_supplier_pkg_cost = models.FloatField(null=True, blank=True, verbose_name='供应商外包装费')
    contract_supplier_seq_cost = models.FloatField(null=True, blank=True, verbose_name='供应商排序费')

    class Meta:
        verbose_name = '采购 信息'
        verbose_name_plural = '采购 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        if self.bom.duns is not None:
            matched_buyer_object: UnsortedInboundBuyer = UnsortedInboundBuyer.objects.filter(
                part_number=self.bom.part_number, duns=self.bom.duns).first()

            if matched_buyer_object:
                self.buyer = matched_buyer_object.buyer
                self.contract_incoterm = matched_buyer_object.transport_mode
                self.contract_supplier_transportation_cost = matched_buyer_object.transport_cost
                self.contract_supplier_pkg_cost = matched_buyer_object.outer_pkg_cost
                self.contract_supplier_seq_cost = matched_buyer_object.seq_cost

        super().save(*args, **kwargs)


class InboundAddress(models.Model):
    """ Inbound address. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_address')

    # operational address
    fu_address = models.CharField(max_length=128, null=True, blank=True, verbose_name='FU提供的原始地址信息')
    mr_address = models.CharField(max_length=128, null=True, blank=True, verbose_name='MR取货地址')

    property_choice = ((1, '国产'), (2, '进口'), (3, '自制'))
    property = models.IntegerField(choices=property_choice, null=True, blank=True, verbose_name='国产/进口/自制')

    supplier_matched = models.ForeignKey(Supplier, null=True, blank=True, verbose_name='供应商 (匹配DUNS)',
                                         on_delete=None)

    region_division = models.CharField(max_length=64, null=True, blank=True, verbose_name='区域划分')
    country = models.CharField(max_length=64, null=True, blank=True, verbose_name='国家')
    province = models.CharField(max_length=64, null=True, blank=True, verbose_name='省')
    city = models.CharField(max_length=64, null=True, blank=True, verbose_name='市')
    mfg_location = models.CharField(max_length=128, null=True, blank=True, verbose_name='生产地址')

    supplier_distance_matched = models.ForeignKey(SupplierDistance, null=True, blank=True,
                                                  verbose_name='选择到某个基地的距离', on_delete=None)

    distance_to_sgm_plant = models.FloatField(null=True, blank=True, verbose_name='运输距离-至生产厂区')
    distance_to_shanghai_cc = models.FloatField(null=True, blank=True, verbose_name='运输距离-金桥C类')
    warehouse_address = models.CharField(max_length=32, null=True, blank=True, verbose_name='中转库地址')
    warehouse_to_sgm_plant = models.FloatField(null=True, blank=True, verbose_name='中转库运输距离')

    class Meta:
        verbose_name = '运作功能块地址 & 最终地址梳理'
        verbose_name_plural = '运作功能块地址 & 最终地址梳理'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        if not self.supplier_matched:
            if self.bom.duns:
                _suppliers = Supplier.objects.filter(duns=self.bom.duns)

                if _suppliers.count() == 1:
                    self.supplier_matched = _suppliers.first()
                    super().save(*args, **kwargs)

        # match supplier
        if self.supplier_matched:
            if self.supplier_matched.region and self.supplier_matched.region[0: 2] in [
                '江浙', '华中', '华北', '东北', '华南', '西南', '华中', '西北', '华东', '中国',
            ]:
                self.country = '中国'

            self.region_division = self.supplier_matched.region
            self.province = self.supplier_matched.province
            self.city = self.supplier_matched.district
            self.mfg_location = self.supplier_matched.address

        # match distance
        if self.supplier_distance_matched:
            self.distance_to_sgm_plant = self.supplier_distance_matched.distance

        if self.supplier_matched:
            jq_distance = SupplierDistance.objects.filter(supplier=self.supplier_matched, base=0).first()

            if jq_distance:
                self.distance_to_shanghai_cc = jq_distance.distance

        super().save(*args, **kwargs)


class InboundTCSPackage(models.Model):
    """ Inbound TCS package. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_tcs_package')

    supplier_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='供应商出厂包装PK Name')
    supplier_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='供应商出厂包装PKPCS')
    supplier_pkg_length = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装PL')
    supplier_pkg_width = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装PW')
    supplier_pkg_height = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装PH')
    supplier_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装折叠率')
    supplier_pkg_cubic_pcs = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装Cubic/Pcs')
    supplier_pkg_cubic_veh = models.FloatField(null=True, blank=True, verbose_name='供应商出厂包装Cubic/Veh')

    sgm_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='先期规划包装PK Name')
    sgm_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='先期规划包装PKPCS')
    sgm_pkg_length = models.FloatField(null=True, blank=True, verbose_name='先期规划包装PL')
    sgm_pkg_width = models.FloatField(null=True, blank=True, verbose_name='先期规划包装PW')
    sgm_pkg_height = models.FloatField(null=True, blank=True, verbose_name='先期规划包装PH')
    sgm_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='先期规划包装折叠率')

    class Meta:
        verbose_name = 'TCS包装 信息'
        verbose_name_plural = 'TCS包装 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        """ dependent fields """
        if not self.supplier_pkg_cubic_pcs:
            try:
                self.supplier_pkg_cubic_pcs = (self.supplier_pkg_length * self.supplier_pkg_height *
                                               self.supplier_pkg_width) / self.supplier_pkg_pcs / 1e9

            except (TypeError, ZeroDivisionError) as e:
                print(e)
                self.supplier_pkg_cubic_pcs = None

        super().save(*args, **kwargs)


class InboundHeaderPart(models.Model):
    """ Inbound header part. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_header')

    head_part_number = models.CharField(max_length=32, null=True, blank=True, verbose_name='头零件')
    assembly_supplier = models.CharField(max_length=128, null=True, blank=True, verbose_name='总成供应商')
    color = models.CharField(max_length=64, null=True, blank=True, verbose_name='颜色件')

    class Meta:
        verbose_name = '头零件 信息'
        verbose_name_plural = '头零件 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        """ match header part. """
        if not self.head_part_number:
            self.head_part_number = self.bom.header_part_number

        if not self.assembly_supplier:
            duns_supplier_list = []
            for ebom_object in Ebom.objects.filter(
                    part_number=self.head_part_number, label=self.bom.label, conf=self.bom.conf):
                if ebom_object.duns and ebom_object.supplier_name:
                    duns_supplier_list.append(f'{ebom_object.duns} - {ebom_object.supplier_name}')

            self.assembly_supplier = ','.join(duns_supplier_list)

        super().save(*args, **kwargs)


class InboundOperationalMode(models.Model):
    """ Inbound operation model """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_op_mode')

    ckd_logistics_mode = models.CharField(max_length=16, null=True, blank=True, verbose_name='海运FCL/海运LCL/空运')
    planned_logistics_mode = models.CharField(max_length=16, null=True, blank=True,
                                              verbose_name='规划模式（A/B/C/自制/进口）')
    if_supplier_seq = models.CharField(max_length=16, null=True, blank=True, verbose_name='是否供应商排序(JIT)')
    payment_mode = models.CharField(max_length=16, null=True, blank=True, verbose_name='结费模式（2A/2B）以此为准')

    class Meta:
        verbose_name = '运作功能块模式 信息'
        verbose_name_plural = '运作功能块模式 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)


class InboundMode(models.Model):
    """ Final mode. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_mode')

    logistics_incoterm_mode_choice = (
        (1, 'FCA'), (2, 'FCA Warehouse'), (3, 'DDP'), (4, 'Inhouse')
    )
    logistics_incoterm_mode = models.IntegerField(
        null=True, blank=True, verbose_name='运输条款', choices=logistics_incoterm_mode_choice)

    operation_mode_choice = (
        (1, 'MR A'),
        (2, 'MR C'),
        (3, 'B'),
        (4, 'JIT'),
        (5, '干线'),
        (6, '进口'),
        (7, '供应商自供自用'),
    )
    operation_mode = models.IntegerField(
        null=True, blank=True, verbose_name='入厂物流模式', choices=operation_mode_choice)

    class Meta:
        verbose_name = '最终模式梳理 信息'
        verbose_name_plural = '最终模式梳理 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)


class InboundOperationalPackage(models.Model):
    """ Inbound Operational package. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_op_package')

    supplier_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='供应商包装PK Name')
    supplier_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='供应商包装PKPCS')
    supplier_pkg_length = models.FloatField(null=True, blank=True, verbose_name='供应商包装PL')
    supplier_pkg_width = models.FloatField(null=True, blank=True, verbose_name='供应商包装PW')
    supplier_pkg_height = models.FloatField(null=True, blank=True, verbose_name='供应商包装PH')
    supplier_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='供应商包装折叠率')

    sgm_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='SGM包装PK Name')
    sgm_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='SGM包装PKPCS')
    sgm_pkg_length = models.FloatField(null=True, blank=True, verbose_name='SGM包装PL')
    sgm_pkg_width = models.FloatField(null=True, blank=True, verbose_name='SGM包装PW')
    sgm_pkg_height = models.FloatField(null=True, blank=True, verbose_name='SGM包装PH')
    sgm_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='SGM包装折叠率')

    class Meta:
        verbose_name = '运作功能块包装 信息'
        verbose_name_plural = '运作功能块包装 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)


class InboundPackage(models.Model):
    """ Inbound Final package. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_package')

    supplier_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='供应商包装PK Name')
    supplier_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='供应商包装PKPCS')
    supplier_pkg_length = models.FloatField(null=True, blank=True, verbose_name='供应商包装PL')
    supplier_pkg_width = models.FloatField(null=True, blank=True, verbose_name='供应商包装PW')
    supplier_pkg_height = models.FloatField(null=True, blank=True, verbose_name='供应商包装PH')
    supplier_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='供应商包装折叠率')
    supplier_pkg_cubic_pcs = models.FloatField(null=True, blank=True, verbose_name='供应商包装Cubic/Pcs')
    supplier_pkg_cubic_veh = models.FloatField(null=True, blank=True, verbose_name='供应商包装Cubic/Veh')

    sgm_pkg_name = models.CharField(max_length=16, null=True, blank=True, verbose_name='SGM包装PK Name')
    sgm_pkg_pcs = models.IntegerField(null=True, blank=True, verbose_name='SGM包装PKPCS')
    sgm_pkg_length = models.FloatField(null=True, blank=True, verbose_name='SGM包装PL')
    sgm_pkg_width = models.FloatField(null=True, blank=True, verbose_name='SGM包装PW')
    sgm_pkg_height = models.FloatField(null=True, blank=True, verbose_name='SGM包装PH')
    sgm_pkg_folding_rate = models.FloatField(null=True, blank=True, verbose_name='SGM包装折叠率')
    sgm_pkg_cubic_pcs = models.FloatField(null=True, blank=True, verbose_name='SGM包装Cubic/Pcs')
    sgm_pkg_cubic_veh = models.FloatField(null=True, blank=True, verbose_name='SGM包装Cubic/Veh')

    cubic_matrix = models.FloatField(null=True, blank=True, verbose_name='体积放大系数')

    class Meta:
        verbose_name = '最终包装信息梳理 信息'
        verbose_name_plural = '最终包装信息梳理 信息'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def save(self, *args, **kwargs):
        """ dependent fields """
        if self.bom.duns is not None:
            matched_object: UnsortedInboundTCS = UnsortedInboundTCS.objects.filter(
                part_number=self.bom.part_number, duns=self.bom.duns).order_by('-id').first()

            if matched_object:
                for field in matched_object._meta.get_fields():
                    if field.name == 'id':
                        continue

                    if hasattr(self, field.name):
                        field_val = getattr(self, field.name)

                        if field_val is None:
                            setattr(self, field.name, getattr(matched_object, field.name))

        if self.supplier_pkg_cubic_pcs is None:
            try:
                self.supplier_pkg_cubic_pcs = (self.supplier_pkg_length * self.supplier_pkg_height *
                                               self.supplier_pkg_width) / self.supplier_pkg_pcs / 1e9

            except (TypeError, ZeroDivisionError) as e:
                print(e)
                self.supplier_pkg_cubic_pcs = None

        if self.sgm_pkg_cubic_pcs is None:
            try:
                self.sgm_pkg_cubic_pcs = (self.sgm_pkg_length * self.sgm_pkg_height *
                                          self.sgm_pkg_width) / self.sgm_pkg_pcs / 1e9

            except (TypeError, ZeroDivisionError) as e:
                print(e)
                self.sgm_pkg_cubic_pcs = None

        if self.supplier_pkg_cubic_veh is None and self.supplier_pkg_cubic_pcs is not None:
            if self.bom.quantity is not None:
                self.supplier_pkg_cubic_veh = self.bom.quantity * self.supplier_pkg_cubic_pcs

        if self.sgm_pkg_cubic_veh is None and self.sgm_pkg_pcs is not None:
            if self.bom.quantity is not None:
                self.sgm_pkg_cubic_veh = self.bom.quantity * self.sgm_pkg_pcs

        super().save(*args, **kwargs)


class UploadHandler(models.Model):
    """ Upload files. """
    model_name_choice = (
        (1, InboundTCS._meta.verbose_name),
        (2, InboundBuyer._meta.verbose_name),
        (999, '宽表'),
    )
    model_name = models.IntegerField(choices=model_name_choice)

    file_to_be_uploaded = models.FileField(null=True, blank=True)
    upload_time = models.DateTimeField(auto_now=True, editable=False)

    label = models.ForeignKey(NominalLabelMapping, null=True, blank=True, default=None, on_delete=models.CASCADE,
                              verbose_name='车型')
    conf = models.CharField(max_length=64, null=True, blank=True, default=None, verbose_name='配置')
    veh_pt_choice = ((1, 'VEH'), (2, 'PT'))
    veh_pt = models.IntegerField(verbose_name='VEH or PT', default=1, choices=veh_pt_choice)

    class Meta:
        verbose_name = '上传文件暂存'
        verbose_name_plural = '上传文件暂存'

    def __str__(self):
        return str(self.upload_time)

    def save(self, *args, **kwargs):
        """ auto archive. """
        for old_object in UploadHandler.objects.filter(upload_time__lte=date.today() - timedelta(days=-1)):
            old_object.delete()

        super().save(*args, **kwargs)


class Constants(models.Model):
    constant_key = models.CharField(max_length=64, primary_key=True, verbose_name='constant name')

    value_type_choice = ((0, 'int'), (1, 'char'), (2, 'decimal'))
    value_type = models.IntegerField(verbose_name='值类型', choices=value_type_choice)
    constant_value_int = models.IntegerField(null=True, blank=True, verbose_name='值(整数)')
    constant_value_char = models.CharField(max_length=64, null=True, blank=True, verbose_name='值(字符)')
    constant_value_float = models.FloatField(null=True, blank=True, verbose_name='值(小数)')

    class Meta:
        verbose_name = '常数维护'
        verbose_name_plural = '常数维护'

    def __str__(self):
        return self.constant_key


class InboundOverseaRate(models.Model):
    """ Oversea rate. """
    region = models.CharField(max_length=64, verbose_name='区域')
    base = models.IntegerField(verbose_name='基地', choices=BASE_CHOICE)
    cc = models.CharField(max_length=64, verbose_name='CC')
    export_harbor = models.CharField(max_length=64, verbose_name='出口港')
    definition_harbor = models.CharField(max_length=64, verbose_name='目的港')

    os_dm_rate = models.FloatField(null=True, blank=True, verbose_name='海外段内陆运输单价')
    cc_rate = models.FloatField(null=True, blank=True, verbose_name='CC操作单价')
    euro_doc_rate = models.FloatField(null=True, blank=True, verbose_name='欧洲单证费')
    os_40h_rate = models.FloatField(null=True, blank=True, verbose_name='海外港口拉动 40H\'单箱价格')
    os_40h_danger_rate = models.FloatField(null=True, blank=True, verbose_name='海外港口拉动 40H\'单箱价格（危险）')
    inter_40h_rate = models.FloatField(null=True, blank=True, verbose_name='国际海运 40H\'单箱价格')
    inter_40h_danger_rate = models.FloatField(null=True, blank=True, verbose_name='国际海运 40H\'单箱价格（危险）')
    dm_40h_rate = models.FloatField(null=True, blank=True, verbose_name='国内拉动 40H\'单箱价格')
    dm_40h_danger_rate = models.FloatField(null=True, blank=True, verbose_name='国内拉动 40H\'单箱价格（危险）')
    delegate = models.FloatField(null=True, blank=True, verbose_name='代收代付')
    delegate_danger = models.FloatField(null=True, blank=True, verbose_name='代收代付（危险）')
    vol_40h = models.FloatField(null=True, blank=True, verbose_name='40H\'集箱容积')
    load_rate = models.FloatField(null=True, blank=True, verbose_name='装载率')
    cpc = models.FloatField(null=True, blank=True, verbose_name='CPC')
    cpc_danger = models.FloatField(null=True, blank=True, verbose_name='CPC（危险）')

    class Meta:
        verbose_name = '进口费率'
        verbose_name_plural = '进口费率'

    def __str__(self):
        return f'{self.region}/{self.get_base_display()}/{self.cc}'


class InboundCcLocations(models.Model):
    """ CC & locations."""
    cc_group_choice = ((1, 'KRCC'), (2, 'NACC'), (3, 'EUCC'))
    cc_group = models.IntegerField(choices=cc_group_choice)
    cn_location_name = models.CharField(max_length=64, verbose_name='中文名称')
    en_location_name = models.CharField(max_length=64, verbose_name='英文名称')

    currency_unit_choice = ((1, '$'), (2, '€'))
    currency_unit = models.IntegerField(choices=currency_unit_choice, verbose_name='货币单位')
    per_cbm = models.FloatField(null=True, blank=True)
    cc = models.CharField(max_length=64, verbose_name='CC')

    class Meta:
        verbose_name = '进口 CC Pickup Location'
        verbose_name_plural = '进口 CC Pickup Location'

    def __str__(self):
        return self.cn_location_name


class InboundCcOperation(models.Model):
    """ CC Operation cost. """
    cc = models.CharField(max_length=64, verbose_name='CC')
    cbm_in_usd = models.FloatField(verbose_name='USD/CBM')
    load_ratio = models.FloatField(verbose_name='装载率')

    class Meta:
        verbose_name = '进口 CC 操作'
        verbose_name_plural = '进口 CC 操作'

    def __str__(self):
        return self.cc


class InboundDangerPackage(models.Model):
    """ Danger package rate. """
    from_to_type_choice = ((1, 'CCto出口港'), (2, '出口港to目的港'), (3, '目的港toSGM'))
    from_to_type = models.IntegerField(choices=from_to_type_choice)
    from_one = models.CharField(max_length=64, verbose_name='from')
    to_one = models.CharField(max_length=64, verbose_name='to')
    standard = models.FloatField(null=True, blank=True, verbose_name='普货')
    danger = models.FloatField(null=True, blank=True, verbose_name='危险品')

    class Meta:
        verbose_name = '进口 危险品费率'
        verbose_name_plural = '进口 危险品费率'

    def __str__(self):
        return f'{self.from_one} -> {self.to_one}'


class InboundCCSupplierRate(models.Model):
    """ CC supplier rate. """
    supplier_duns = models.CharField(max_length=64, verbose_name='Supplier Duns')
    supplier_name = models.CharField(max_length=128, verbose_name='Supplier Name')
    pick_up_location = models.CharField(max_length=128, verbose_name='Pick Up Locaction')
    state = models.CharField(max_length=64, verbose_name='State')
    city = models.CharField(max_length=64, verbose_name='City')
    zip_code = models.CharField(max_length=64, verbose_name='ZIP CODE')
    kilometers = models.FloatField(verbose_name='Kilometers')
    rate = models.FloatField(verbose_name='Rate')
    cpc = models.FloatField(verbose_name='CPC')

    class Meta:
        verbose_name = '进口 CC Suppliers 费率'
        verbose_name_plural = '进口 CC Suppliers 费率'

    def __str__(self):
        return self.supplier_duns


class InboundSupplierRate(models.Model):
    """ Supplier rate. """
    base = models.IntegerField(choices=BASE_CHOICE)
    pickup_location = models.CharField(null=True, blank=True, max_length=128, verbose_name='取货地址')
    duns = models.CharField(max_length=64, null=True, blank=True)
    supplier = models.CharField(max_length=64, verbose_name='取货供应商')
    forward_rate = models.FloatField(null=True, blank=True, verbose_name='去程运输单价 (元/立方米*公里)')
    backward_rate = models.FloatField(null=True, blank=True, verbose_name='回程运输单价 (元/立方米*公里)')
    manage_ratio = models.FloatField(null=True, blank=True, verbose_name='管理费用 （%）')
    vmi_rate = models.FloatField(null=True, blank=True, verbose_name='VMI 中转库运作价格 (元/立方米)')
    oneway_km = models.FloatField(null=True, blank=True, verbose_name='单程公里数')
    address = models.CharField(null=True, blank=True, max_length=128, verbose_name='取货供应商')

    class Meta:
        verbose_name = '供应商 费率'
        verbose_name_plural = '供应商 费率'

    def __str__(self):
        return self.supplier

    def save(self, *args, **kwargs):
        """ Override supplier save method. """
        self.supplier = self.supplier.replace('（', '(').replace('）', ')')

        if not self.duns:
            s = Supplier.objects.filter(
                models.Q(address=self.address) | models.Q(name__contains=self.supplier)
            ).first()

            if s and s.duns:
                self.duns = s.duns
        super().save(*args, **kwargs)


class TruckRate(models.Model):
    """ The cost rate of trucks. """
    name = models.CharField(max_length=16, unique=True, verbose_name='卡车车型')

    cube = models.FloatField(verbose_name='车辆立方')
    loading_ratio = models.FloatField(verbose_name='装载率')
    capable_cube = models.FloatField(verbose_name='车辆可装载立方')
    avg_speed = models.FloatField(verbose_name='车辆行驶平均速度')
    load_time = models.FloatField(verbose_name='装卸时间')
    oil_price = models.FloatField(null=True, blank=True, verbose_name='油价联动')
    charter_price = models.FloatField(null=True, blank=True, verbose_name='包车价')
    overdue_price = models.FloatField(null=True, blank=True, verbose_name='超时价')
    rate_per_km = models.FloatField(null=True, blank=True, verbose_name='公里数单价')

    base = models.IntegerField(verbose_name='基地', choices=BASE_CHOICE)

    class Meta:
        verbose_name = '卡车费率'
        verbose_name_plural = '卡车费率'

    def __str__(self):
        return self.name


class RegionRouteRate(models.Model):
    """ The cost rate of route by region or route. """
    related_base = models.IntegerField(verbose_name='基地', choices=BASE_CHOICE)
    region_or_route = models.CharField(max_length=8, unique=True, verbose_name='区域/线路')
    parent_region = models.CharField(max_length=8, null=True, blank=True, verbose_name='父级区域')
    km = models.FloatField(verbose_name='公里数')
    price_per_cube = models.FloatField(verbose_name='立方单价')
    reference = models.CharField(max_length=8, verbose_name='参考就近区域')

    class Meta:
        verbose_name = '区域/线路费率'
        verbose_name_plural = '区域/线路费率'

    def __str__(self):
        return self.region_or_route


class VMIRate(models.Model):
    """ VMI rate """
    base = models.IntegerField(choices=BASE_CHOICE)
    whether_repacking = models.BooleanField()
    rate = models.FloatField()

    class Meta:
        verbose_name = 'VMI 费率'
        verbose_name_plural = 'VMI 费率'

    def __str__(self):
        return self.get_base_display() + ' ' + 'Repacking' if self.whether_repacking else ''


class WaterwayRate(models.Model):
    """ Water way rate. """
    start_base = models.IntegerField(choices=BASE_CHOICE)
    destination_base = models.IntegerField(choices=BASE_CHOICE)
    rate = models.FloatField()

    class Meta:
        verbose_name = '水运费率'
        verbose_name_plural = '水运费率'

    def __str__(self):
        return '%s -> %s' % (self.get_start_base_display(), self.get_destination_base_display())


class InboundCalculation(models.Model):
    """ Fields to be calculated. """
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE, related_name='rel_calc')

    ddp_pcs = models.FloatField(null=True, blank=True, verbose_name='DDP运费/pcs')

    linehaul_oneway_pcs = models.FloatField(null=True, blank=True, verbose_name='干线去程/pcs')
    linehaul_vmi_pcs = models.FloatField(null=True, blank=True, verbose_name='干线VMI/pcs')
    linehaul_backway_pcs = models.FloatField(null=True, blank=True, verbose_name='干线返程/pcs')

    dom_truck_ttl_pcs = models.FloatField(null=True, blank=True, verbose_name='国内陆运/pcs')

    dom_water_oneway_pcs = models.FloatField(null=True, blank=True, verbose_name='国内水运-去程/pcs')
    dom_cc_operation_pcs = models.FloatField(null=True, blank=True, verbose_name='国内CC操作费/pcs')
    dom_water_backway_pcs = models.FloatField(null=True, blank=True, verbose_name='国内水运-返程/pcs')

    dom_water_ttl_pcs = models.FloatField(null=True, blank=True, verbose_name='国内水运/pcs')

    oversea_inland_pcs = models.FloatField(null=True, blank=True, verbose_name='海外段内陆运输/pcs')
    oversea_cc_op_pcs = models.FloatField(null=True, blank=True, verbose_name='海外CC操作费/pcs')
    international_ocean_pcs = models.FloatField(null=True, blank=True, verbose_name='国际海运费/pcs')
    dom_pull_pcs = models.FloatField(null=True, blank=True, verbose_name='国内拉动费/pcs')
    certificate_pcs = models.FloatField(null=True, blank=True, verbose_name='单证费/pcs')

    oversea_ocean_ttl_pcs = models.FloatField(null=True, blank=True, verbose_name='进口海运/pcs')
    oversea_air_pcs = models.FloatField(null=True, blank=True, verbose_name='进口空运/pcs')
    inbound_ttl_pcs = models.FloatField(null=True, blank=True, verbose_name='IB Cost')

    ddp_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 DDP运费/veh')
    linehaul_oneway_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 干线去程/veh')
    linehaul_vmi_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 干线VMI/veh')
    linehaul_backway_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 干线返程/veh')

    dom_truck_ttl_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内陆运/veh')
    dom_water_oneway_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内海运-去程/veh')
    dom_cc_operation_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内CC操作费/veh')
    dom_water_backway_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内海运-返程/veh')

    dom_water_ttl_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内海运/veh')
    oversea_inland_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 海外段内陆运输/veh')
    oversea_cc_op_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 海外CC操作费/veh')
    international_ocean_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国际海运费/veh')
    dom_pull_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 国内拉动费/veh')
    certificate_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 单证费/veh')

    oversea_ocean_ttl_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 进口海运/veh')
    oversea_air_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 进口空运/veh')
    inbound_ttl_veh = models.FloatField(null=True, blank=True, verbose_name='单车费用 TTL IB Cost')

    class Meta:
        verbose_name = 'Cost Summary'
        verbose_name_plural = 'Cost Summary'

    def __str__(self):
        return '零件 %s' % str(self.bom)

    def calculate_veh_fields(self):
        """ Calculate veh fields according to pcs fields. """
        if self.bom.quantity is None:
            return

        for calculable_field in self._meta.get_fields():
            if isinstance(calculable_field, models.FloatField):

                if calculable_field.name[-4:] == '_veh':  # vehicle fields

                    # if manually set, skip calculation
                    if getattr(self, calculable_field.name) is None:
                        if getattr(self, calculable_field.name[: -4] + '_pcs'):

                            setattr(
                                self,
                                calculable_field.name,
                                getattr(self, calculable_field.name[: -4] + '_pcs') * self.bom.quantity
                            )

    @property
    def base_prop(self):
        label = self.bom.label

        if label is None:
            return None

        else:
            plant_code = self.bom.label.plant_code

            if plant_code is None:
                return None

            else:
                if plant_code[0: 2] == 'SH':
                    base = 0
                elif plant_code[0: 2] == 'DY':
                    base = 1
                elif plant_code[0: 2] == 'NS':
                    base = 3
                elif plant_code[0: 2] == 'WH':
                    base = 4
                else:
                    base = -1

                return base

    def calculate_ddp_pcs(self, mode: InboundMode):
        if self.ddp_pcs is not None:
            return

        if mode.logistics_incoterm_mode in (2, 3):  # DDP or FCA Warehouse
            if hasattr(self.bom, 'rel_buyer'):
                self.ddp_pcs = self.bom.rel_buyer.contract_supplier_transportation_cost

    def calculate_linehaul_oneway_pcs(self, mode: InboundMode, single_part_vol, distance,
                                      supplier_rate_object: InboundSupplierRate, linehual_manage_ratio):
        if self.linehaul_oneway_pcs is not None:
            return

        if mode.operation_mode == 5 and mode.logistics_incoterm_mode in (1, 2):  # 干线, (FCA, FCA Warehouse)
            if single_part_vol is None or distance is None:
                return

            # get oneway rate
            if supplier_rate_object is None:
                return

            oneway_rate = supplier_rate_object.forward_rate
            self.linehaul_oneway_pcs = oneway_rate * single_part_vol * distance * (1.0 + linehual_manage_ratio)

    def calculate_linehaul_backway_pcs(self, mode: InboundMode, single_part_vol, distance,
                                       supplier_rate_object: InboundSupplierRate, linehual_manage_ratio,
                                       sgm_pkg_folding_rate):
        if self.linehaul_oneway_pcs is not None:
            return

        if mode.operation_mode == 5 and mode.logistics_incoterm_mode in (1, 2):  # 干线, (FCA, FCA Warehouse)
            if single_part_vol is None or distance is None:
                return

            # get backway rate
            if supplier_rate_object is None or sgm_pkg_folding_rate is None:
                return

            backway_rate = supplier_rate_object.backward_rate
            self.linehaul_oneway_pcs = backway_rate * single_part_vol * distance * sgm_pkg_folding_rate * (
                    1.0 + linehual_manage_ratio)

    def calculate_linehaul_vmi_pcs(self, mode: InboundMode, single_part_vol, repacking: bool):
        if self.linehaul_vmi_pcs is not None:
            return

        if mode.operation_mode == 5 and mode.logistics_incoterm_mode in (1, 2):  # 干线, (FCA, FCA Warehouse)
            if single_part_vol is None or repacking is None:
                return

            vmi_rate: VMIRate = VMIRate.objects.filter(base=self.base_prop, whether_repacking=repacking).first()
            if vmi_rate is None or vmi_rate.rate is None:
                return

            self.linehaul_vmi_pcs = vmi_rate.rate * single_part_vol

    @property
    def repacking_prop(self):
        if not hasattr(self.bom, 'rel_package'):
            return None

        package_object = self.bom.rel_package
        need_repacking = False

        for _field in ('pcs', 'length', 'height', 'width', 'folding_rate'):
            supplier_field = getattr(package_object, 'supplier_pkg_' + _field)
            sgm_field = getattr(package_object, 'sgm_pkg_' + _field)

            if supplier_field is not None and sgm_field is not None:
                res = (supplier_field == sgm_field)
                if not res:
                    need_repacking = True
                    break

        return need_repacking

    def calculate_dom_water_oneway_pcs(self, mode: InboundMode, single_part_vol, cc_container_vol, liquid_load_ratio):
        if self.dom_water_oneway_pcs is not None:
            return

        if mode.operation_mode == 2 and mode.logistics_incoterm_mode in (1, 2):  # MR C, (FCA, FCA Warehouse)

            waterway_rate_object = WaterwayRate.objects.filter(start_base=self.base_prop, destination_base=0).first()
            if waterway_rate_object is None:
                return

            try:
                self.dom_water_oneway_pcs = waterway_rate_object.rate / math.floor(
                    cc_container_vol * liquid_load_ratio / single_part_vol)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                self.dom_water_oneway_pcs = None

    def calculate_dom_cc_operation_pcs(self, mode: InboundMode, single_part_vol, cc_container_packing_rate,
                                       cc_container_vol, liquid_load_ratio):
        if self.dom_cc_operation_pcs is not None:
            return

        if mode.operation_mode == 2 and mode.logistics_incoterm_mode in (1, 2):  # MR C, (FCA, FCA Warehouse)

            try:
                self.dom_cc_operation_pcs = cc_container_packing_rate / math.floor(
                    cc_container_vol * liquid_load_ratio / single_part_vol)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                self.dom_cc_operation_pcs = None

    def calculate_dom_water_backway_pcs(self, mode: InboundMode, sgm_pkg_folding_rate):
        if self.dom_water_backway_pcs is not None:
            return

        if mode.operation_mode == 2 and mode.logistics_incoterm_mode in (1, 2):  # MR C, (FCA, FCA Warehouse)
            if self.dom_water_oneway_pcs is not None and sgm_pkg_folding_rate is not None:
                self.dom_water_backway_pcs = self.dom_water_oneway_pcs * sgm_pkg_folding_rate

    def calculate_dom_water_ttl_pcs(self, mode: InboundMode):
        if self.dom_water_ttl_pcs is not None:
            return

        if mode.operation_mode in (2, 3) and mode.logistics_incoterm_mode in (1, 2):  # (MR C, B), (FCA, FCA Warehouse)
            if self.dom_water_oneway_pcs is not None and self.dom_water_backway_pcs is not None:
                self.dom_water_ttl_pcs = self.dom_water_oneway_pcs + self.dom_water_backway_pcs

    def calculate_oversea_inland_pcs(self, mode: InboundMode, single_part_vol):
        if self.oversea_inland_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            if self.bom.duns is None:
                return

            oversea_supplier_object: InboundCCSupplierRate = InboundCCSupplierRate.objects.filter(
                supplier_duns=self.bom.duns).first()

            if oversea_supplier_object is None or oversea_supplier_object.cpc is None or single_part_vol is None:
                return

            self.oversea_inland_pcs = oversea_supplier_object.cpc * single_part_vol

    def calculate_oversea_cc_op_pcs(self, mode: InboundMode, single_part_vol, usd_exchange_rate, district):
        if self.oversea_cc_op_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            state = None

            if district is not None:
                state = district

            if self.bom.duns is not None:
                oversea_supplier_object: InboundCCSupplierRate = InboundCCSupplierRate.objects.filter(
                    supplier_duns=self.bom.duns).first()

                if oversea_supplier_object is not None and oversea_supplier_object.state is not None:
                    state = oversea_supplier_object.state

            if state is None:
                return

            cc_location_object: InboundCcLocations = InboundCcLocations.objects.filter(
                en_location_name=state.upper()).first()

            if cc_location_object is None or cc_location_object.cc is None:
                return

            cc_object: InboundCcOperation = InboundCcOperation.objects.filter(cc=cc_location_object.cc).first()

            if cc_object is None:
                return

            self.oversea_cc_op_pcs = cc_object.cbm_in_usd * single_part_vol * usd_exchange_rate

    def calculate_international_ocean_pcs(self, mode: InboundMode, single_part_vol, district):
        if self.international_ocean_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            state = None

            if district is not None:
                state = district

            if self.bom.duns is not None:
                oversea_supplier_object: InboundCCSupplierRate = InboundCCSupplierRate.objects.filter(
                    supplier_duns=self.bom.duns).first()

                if oversea_supplier_object is not None and oversea_supplier_object.state is not None:
                    state = oversea_supplier_object.state

            if state is None:
                return

            rate_object: InboundOverseaRate = InboundOverseaRate.objects.filter(
                region=state.upper(), base=self.base_prop).first()

            if rate_object is None:
                return

            try:
                self.international_ocean_pcs = rate_object.inter_40h_rate * single_part_vol / (
                        rate_object.vol_40h * rate_object.load_rate)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                self.international_ocean_pcs = None

    def calculate_dom_pull_pcs(self, mode: InboundMode, single_part_vol, district):
        if self.dom_pull_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            state = None

            if district is not None:
                state = district

            if self.bom.duns is not None:
                oversea_supplier_object: InboundCCSupplierRate = InboundCCSupplierRate.objects.filter(
                    supplier_duns=self.bom.duns).first()

                if oversea_supplier_object is not None and oversea_supplier_object.state is not None:
                    state = oversea_supplier_object.state

            if state is None:
                return

            rate_object: InboundOverseaRate = InboundOverseaRate.objects.filter(
                region=state.upper(), base=self.base_prop).first()

            if rate_object is None:
                return

            try:
                self.dom_pull_pcs = rate_object.dm_40h_rate * single_part_vol / (
                        rate_object.vol_40h * rate_object.load_rate)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                self.dom_pull_pcs = None

    def calculate_certificate_pcs(self, mode: InboundMode):
        if self.certificate_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            if self.oversea_inland_pcs is not None and self.oversea_cc_op_pcs is not None:
                self.certificate_pcs = (self.oversea_inland_pcs + self.oversea_cc_op_pcs) / 9.0

    def calculate_oversea_ocean_ttl_pcs(self, mode: InboundMode):
        if self.oversea_ocean_ttl_pcs is not None:
            return

        if mode.operation_mode == 6 and mode.logistics_incoterm_mode == 1:  # 进口, FCA
            _total = 0.0
            _total += self.oversea_inland_pcs if self.oversea_inland_pcs else 0.0
            _total += self.oversea_cc_op_pcs if self.oversea_cc_op_pcs else 0.0
            _total += self.international_ocean_pcs if self.international_ocean_pcs else 0.0
            _total += self.dom_pull_pcs if self.dom_pull_pcs else 0.0
            _total += self.certificate_pcs if self.certificate_pcs else 0.0

            self.oversea_ocean_ttl_pcs = _total

    def calculate_jq_dom_truck_ttl_pcs(self, distance, milkrun_manage_ratio, single_part_vol, district):
        if distance is None or milkrun_manage_ratio is None or single_part_vol is None:
            return

        truck: TruckRate = TruckRate.objects.filter(name='上海12米卡车').first()
        if truck is None:
            return

        if distance <= 25:  # within 25km
            try:
                rate_lt_25km = truck.oil_price * truck.charter_price / 9.0 * (
                        distance * 2.0 / truck.avg_speed + truck.load_time)

                self.dom_truck_ttl_pcs = rate_lt_25km / math.floor(
                    truck.cube * truck.loading_ratio / single_part_vol
                ) * (1 + milkrun_manage_ratio)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                return

        else:  # greater than 25km
            if district is None:
                return

            tri_r_object: RegionRouteRate = RegionRouteRate.objects.filter(region_or_route=district).first()
            if tri_r_object is None:
                return

            try:
                rate_gt_25km = tri_r_object.km * tri_r_object.price_per_cube * truck.oil_price
                self.dom_truck_ttl_pcs = rate_gt_25km * single_part_vol * (
                        1 + milkrun_manage_ratio)

            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(e)
                return

    def calculate_dy_dom_truck_ttl_pcs(self, distance, milkrun_manage_ratio, single_part_vol, district):
        if distance is None or milkrun_manage_ratio is None or single_part_vol is None:
            return

        truck: TruckRate = TruckRate.objects.filter(name='东岳12米卡车').first()
        if truck is None:
            return

        try:
            if distance <= 25:  # within 25km
                km_rate = truck.oil_price * truck.charter_price / 9.0 * (
                        distance * 2.0 / truck.avg_speed + truck.load_time)

            else:  # greater than 25km
                km_rate = distance * truck.oil_price * truck.rate_per_km * 2.0

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

        # qingdao line rate
        tri_r_object = RegionRouteRate.objects.filter(region_or_route='青岛线').first()
        if tri_r_object is None:
            return

        try:
            qingdao_line_rate = tri_r_object.km * tri_r_object.price_per_cube * truck.oil_price

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

        # cost
        if district is None:
            return

        try:
            if district == '青岛':
                self.dom_truck_ttl_pcs = qingdao_line_rate / math.floor(
                    truck.cube * truck.loading_ratio / single_part_vol
                ) * (1 + milkrun_manage_ratio)

            else:
                self.dom_truck_ttl_pcs = km_rate / math.floor(
                    truck.cube * truck.loading_ratio / single_part_vol
                ) * (1 + milkrun_manage_ratio)

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

    def calculate_ns_dom_truck_ttl_pcs(self, distance, milkrun_manage_ratio, single_part_vol, district):
        if distance is None or milkrun_manage_ratio is None or single_part_vol is None:
            return

        truck: TruckRate = TruckRate.objects.filter(name='北盛12米卡车').first()
        if truck is None:
            return

        try:
            if distance <= 25:  # within 25km
                km_rate = truck.oil_price * truck.charter_price / 9.0 * (
                        distance * 2.0 / truck.avg_speed + truck.load_time)

            else:  # greater than 25km
                km_rate = distance * truck.oil_price * truck.rate_per_km * 2.0

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

        # changchun line rate
        tri_r_object = RegionRouteRate.objects.filter(region_or_route='长春1').first()
        if tri_r_object is None:
            return

        try:
            changchun_line_rate = tri_r_object.km * tri_r_object.price_per_cube * truck.oil_price

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

        # cost
        if district is None:
            return

        try:
            if district == '长春':
                self.dom_truck_ttl_pcs = changchun_line_rate / math.floor(
                    truck.cube * truck.loading_ratio / single_part_vol
                ) * (1 + milkrun_manage_ratio)

            else:
                self.dom_truck_ttl_pcs = km_rate / math.floor(
                    truck.cube * truck.loading_ratio / single_part_vol
                ) * (1 + milkrun_manage_ratio)

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

    @staticmethod
    def wh_cubic_rate(distance):
        if distance:
            if distance <= 10.0:
                return 3.89
            elif distance <= 20:
                return 6.51
            elif distance <= 30:
                return 11.66
            elif distance <= 40:
                return 16.52
            elif distance <= 50:
                return 23.32
            elif distance <= 60:
                return 27.2
            elif distance <= 70:
                return 36.92
            else:
                return 47
        else:
            return None

    def calculate_wh_dom_truck_ttl_pcs(self, distance, milkrun_manage_ratio, single_part_vol, district):
        if distance is None or milkrun_manage_ratio is None or single_part_vol is None:
            return

        if district and district in ['武汉园区', 'Milkrun武汉园区']:
            km_rate = Constants.objects.get(
                constant_key='Milkrun武汉园区费率').constant_value_float

        else:
            km_rate = self.wh_cubic_rate(distance)

        try:
            self.dom_truck_ttl_pcs = km_rate * single_part_vol * (1 + milkrun_manage_ratio)

        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(e)
            return

    def calculate_dom_truck_ttl_pcs(self, mode: InboundMode, distance, milkrun_manage_ratio, single_part_vol, district):
        if self.dom_truck_ttl_pcs is not None:
            return

        if mode.logistics_incoterm_mode in (1, 2):  # MR C, (FCA, FCA Warehouse)

            if mode.operation_mode == 1:  # MR A
                if distance is None or milkrun_manage_ratio is None or single_part_vol is None:
                    return

                if self.base_prop == 0:  # JQ
                    self.calculate_jq_dom_truck_ttl_pcs(distance, milkrun_manage_ratio, single_part_vol, district)

                elif self.base_prop == 1:  # DY
                    self.calculate_dy_dom_truck_ttl_pcs(distance, milkrun_manage_ratio, single_part_vol, district)

                elif self.base_prop == 3:  # NS
                    self.calculate_ns_dom_truck_ttl_pcs(distance, milkrun_manage_ratio, single_part_vol, district)

                elif self.base_prop == 4:  # WH
                    self.calculate_wh_dom_truck_ttl_pcs(distance, milkrun_manage_ratio, single_part_vol, district)

                else:
                    return

            elif mode.operation_mode == 2:  # MR C
                self.calculate_jq_dom_truck_ttl_pcs(distance, milkrun_manage_ratio, single_part_vol, district)

            elif mode.operation_mode == 5:  # 干线
                if (self.linehaul_oneway_pcs is None or self.linehaul_vmi_pcs is None or
                        self.linehaul_backway_pcs is None):
                    return

                self.dom_truck_ttl_pcs = self.linehaul_oneway_pcs + self.linehaul_vmi_pcs + self.linehaul_backway_pcs

            else:
                return

    def calculate_inbound_ttl_pcs(self):
        # if self.inbound_ttl_pcs is not None:
        #     return

        _total = 0.0
        _total += self.ddp_pcs if self.ddp_pcs else 0.0
        _total += self.dom_truck_ttl_pcs if self.dom_truck_ttl_pcs else 0.0
        _total += self.dom_water_ttl_pcs if self.dom_water_ttl_pcs else 0.0
        _total += self.oversea_ocean_ttl_pcs if self.oversea_ocean_ttl_pcs else 0.0
        _total += self.oversea_air_pcs if self.oversea_air_pcs else 0.0

        self.inbound_ttl_pcs = _total

    @property
    def veh_pt_prop(self):
        return self.bom.veh_pt

    def save(self, *args, **kwargs):
        """ Calculation when saving. """
        for calculable_field in self._meta.get_fields():
            if isinstance(calculable_field, models.FloatField):

                if not hasattr(self, calculable_field.name):
                    setattr(self, calculable_field.name, None)

        if not hasattr(self.bom, 'rel_mode'):  # no mode
            super().save(*args, **kwargs)
            return

        if not self.bom.label:  # no base
            super().save(*args, **kwargs)
            return

        # reusable object & constants
        mode_object = self.bom.rel_mode

        if hasattr(self.bom, 'rel_package'):
            single_part_vol = self.bom.rel_package.sgm_pkg_cubic_pcs
            sgm_pkg_folding_rate = self.bom.rel_package.sgm_pkg_folding_rate
        else:
            single_part_vol = None
            sgm_pkg_folding_rate = None

        if hasattr(self.bom, 'rel_address'):
            distance = self.bom.rel_address.distance_to_sgm_plant
            district = self.bom.rel_address.region_division
        else:
            distance = None
            district = None

        linehual_manage_ratio = Constants.objects.get(constant_key='干线管理费系数').constant_value_float
        cc_container_vol = Constants.objects.get(constant_key='国内CC集装箱容积').constant_value_float

        if self.veh_pt_prop == 2:  # pt
            liquid_load_ratio = Constants.objects.get(constant_key='国内CCPT液体装载率').constant_value_float
        else:  # veh
            liquid_load_ratio = Constants.objects.get(constant_key='国内CC整车液体装载率').constant_value_float

        cc_container_packing_rate = Constants.objects.get(constant_key='国内CC单箱操作费').constant_value_float
        usd_exchange_rate = Constants.objects.get(constant_key='美元汇率').constant_value_float
        milkrun_manage_ratio = Constants.objects.get(constant_key='Milkrun管理费系数').constant_value_float

        if self.bom.duns is None:
            supplier_rate_object = None
        else:
            supplier_rate_object = InboundSupplierRate.objects.filter(
                duns=self.bom.duns, base=self.base_prop).first()

        # calculate pcs fields
        self.calculate_ddp_pcs(mode_object)
        self.calculate_linehaul_oneway_pcs(mode_object, single_part_vol, distance,
                                           supplier_rate_object, linehual_manage_ratio)
        self.calculate_linehaul_backway_pcs(mode_object, single_part_vol, distance,
                                            supplier_rate_object, linehual_manage_ratio, sgm_pkg_folding_rate)
        self.calculate_linehaul_vmi_pcs(mode_object, single_part_vol, self.repacking_prop)

        self.calculate_dom_water_oneway_pcs(mode_object, single_part_vol, cc_container_vol, liquid_load_ratio)
        self.calculate_dom_cc_operation_pcs(mode_object, single_part_vol, cc_container_packing_rate,
                                            cc_container_vol, liquid_load_ratio)
        self.calculate_dom_water_backway_pcs(mode_object, sgm_pkg_folding_rate)
        self.calculate_dom_water_ttl_pcs(mode_object)

        self.calculate_oversea_inland_pcs(mode_object, single_part_vol)
        self.calculate_oversea_cc_op_pcs(mode_object, single_part_vol, usd_exchange_rate, district)
        self.calculate_international_ocean_pcs(mode_object, single_part_vol, district)
        self.calculate_dom_pull_pcs(mode_object, single_part_vol, district)
        self.calculate_certificate_pcs(mode_object)
        self.calculate_oversea_ocean_ttl_pcs(mode_object)

        self.calculate_dom_truck_ttl_pcs(mode_object, distance, milkrun_manage_ratio, single_part_vol, district)

        self.calculate_inbound_ttl_pcs()

        # calculate veh fields by pcs fields
        self.calculate_veh_fields()

        super().save(*args, **kwargs)
