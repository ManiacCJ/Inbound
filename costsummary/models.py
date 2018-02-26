from datetime import timedelta, date

from django.db import models
from django.contrib.auth.models import User

# constants
BASE_CHOICE = (
    (0, 'JQ'),
    (1, 'DY'),
    (3, 'NS'),
    (4, 'WH'),
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
        return self.get_base_display()


class NominalLabelMapping(models.Model):
    """ Map book, plant code, model to vehicle label. """
    value = models.CharField(max_length=128, verbose_name='车型名称')

    # composite primary keys
    book = models.CharField(max_length=4, verbose_name='车系')
    plant_code = models.CharField(max_length=8, verbose_name='分厂')
    model = models.CharField(max_length=64, verbose_name='模型')

    class Meta:
        verbose_name = '车型映射'
        verbose_name_plural = '车型映射'

        # composite primary key constraints
        unique_together = ("book", "plant_code", "model")

    def __str__(self):
        return "{0}({1}, {2}, {3})".format(self.value, self.book, self.plant_code, self.model)


class Ebom(models.Model):
    """ EBOM data. """
    label = models.ForeignKey(NominalLabelMapping, null=True, on_delete=models.CASCADE, verbose_name='车型')

    # other fields
    upc = models.CharField(max_length=20, verbose_name='UPC')
    fna = models.CharField(max_length=20, verbose_name='FNA')

    structure_node = models.CharField(max_length=64, null=True, blank=True,
                                      default=None, verbose_name='Structure Node')

    part_number = models.CharField(max_length=32, verbose_name='P/N-Part Number')
    description_en = models.CharField(max_length=128, verbose_name='Description EN')
    description_cn = models.CharField(max_length=128, null=True, blank=True, verbose_name='Description CN')

    header_part_number = models.CharField(max_length=32, null=True, blank=True, verbose_name='Header Part Number')

    ar_em_choices = ((True, 'AR'), (False, 'EM'))
    ar_em_material_indicator = models.NullBooleanField(verbose_name='AR/EM Material Indicator', choices=ar_em_choices)

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

    def __str__(self):
        return self.part_number

    def save(self, *args, **kwargs):
        if self.vendor_duns_number:
            _duns = self.vendor_duns_number.split('_')

            try:
                self.duns = int(_duns[0])

            except ValueError as e:
                print(e)
                self.duns = None

        if self.description_en:
            self.tec = TecCore.objects.filter(mgo_part_name_list__contains=self.description_en.upper()).first()

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
                                                  verbose_name='SGM PLANT', on_delete=None)

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
        # match supplier
        if self.supplier_matched:
            if self.supplier_matched.region and self.supplier_matched.region[0: 2] in [
                '江浙',
                '华中',
                '华北',
                '东北',
                '华南',
                '西南',
                '华中',
                '西北',
                '华东',
                '中国',
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
        self.head_part_number = self.bom.header_part_number

        if not self.assembly_supplier:
            duns_supplier_list = []
            for ebom_object in Ebom.objects.filter(part_number=self.head_part_number):
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

    def calc_ddp_pcs(self):
        """ Calculate ddp_pcs field. """
        if hasattr(self.bom, 'rel_buyer'):
            return self.bom.rel_buyer.contract_supplier_pkg_cost
        else:
            return None

    # def calc_dom_truck_ttl_pcs(self):
    #     """ Calculate dom_truck_ttl_pcs field. """

    def save(self, *args, **kwargs):
        """ Calculation when saving. """
        for calculable_field in self._meta.get_fields():
            if isinstance(calculable_field, models.FloatField):

                # if manually set, skip calculation
                if getattr(self, calculable_field.name) is None:
                    if hasattr(self, 'calc_' + calculable_field.name):

                        calc_func = getattr(self, 'calc_' + calculable_field.name)

                        setattr(
                            self,
                            calculable_field.name,
                            calc_func()
                        )

        super().save(*args, **kwargs)
