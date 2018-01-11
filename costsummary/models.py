from django.db import models


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
    ar_em_material_indicator = models.NullBooleanField(verbose_name='AR/EM Material Indicator')

    work_shop = models.CharField(max_length=16, null=True, blank=True, verbose_name='Work Shop')
    vendor_duns_number = models.CharField(max_length=32, null=True, blank=True, verbose_name='Duns / vendor number')
    supplier_name = models.CharField(max_length=128, verbose_name='Supplier Name')
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

    def __str__(self):
        return self.concat()
