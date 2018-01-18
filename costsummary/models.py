from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class TecCore(models.Model):
    """ Tec id & part name (English). """
    tec_id = models.IntegerField(primary_key=True, verbose_name='TEC No.')
    common_part_name = models.CharField(unique=True, max_length=128, verbose_name='Common Part Name')

    class Meta:
        verbose_name = 'TEC Part Name'
        verbose_name_plural = 'TEC Part Name'

    def __str__(self):
        return self.common_part_name

    def save(self, *args, **kwargs):
        """ Override default save action. """
        self.common_part_name = self.common_part_name.upper()  # upper case.
        super().save(self, *args, **kwargs)


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

    class Meta:
        verbose_name = 'EBOM 数据'
        verbose_name_plural = 'EBOM 数据'

    def __str__(self):
        return self.part_number


class EbomConfiguration(models.Model):
    """ Configuration of EBOM """
    bom = models.ForeignKey(Ebom, on_delete=models.CASCADE)

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

    user = models.ForeignKey(User, null=True, blank=True, default=None)
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
    bom = models.OneToOneField(Ebom, on_delete=models.CASCADE)

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
        verbose_name = 'TCS定点 信息'
        verbose_name_plural = 'TCS定点 信息'

    def __str__(self):
        return str(self.bom)


# test models for excel output
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    slug = models.CharField(max_length=10, unique=True,
                            default="question")

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
