import os
import inspect

from django.http import HttpResponse
from django.db import connection as RawConnection
from django.db.models import Model
from django.shortcuts import Http404, redirect, reverse
from django.contrib.admin import site as wide_table_dummy_param
from django.apps import apps

import django_excel

from . import models
from .dumps import InitializeData, PERSISTENCE_DIR
from .admin import EbomAdmin as WideTable


# Create your views here.
def initialize_data(request, data):
    """ Load initial csv-formatted data. """
    # call dump functions
    row_count = None

    if data == 'tec-num':
        row_count = InitializeData.load_initial_tec_num()

    elif data == 'nl':
        row_count = InitializeData.load_initial_nl_mapping()

    elif data == 'supplier':
        row_count = InitializeData.load_initial_distance()

    elif data == 'osrate':
        row_count = InitializeData.load_initial_os_rate()

    elif data == 'cclocation':
        row_count = InitializeData.load_initial_cc_location()

    return HttpResponse(
        "The initial %s data have been loaded. There are totally %d rows." % (data, row_count))


def group_ebom_by_label(request):
    """ Group ebom data by label. """

    with RawConnection.cursor() as cursor:
        cursor.execute("""
            SELECT model_year, book, plant_code, model, count(1) FROM ta_ebom 
              GROUP BY model_year, book, plant_code, model
        """)

        index = 0

        for row in cursor.fetchall():
            label = models.NominalLabelMapping.objects.filter(
                book=row[1], plant_code=row[2], model=row[3]
            ).first()

            entry = models.AEbomEntry(
                model_year=row[0],
                label=label,
                row_count=row[4]
            )

            entry.save()

            index += 1

        return HttpResponse(f'{index} entries generated.')


def download_sheet_template(request, sheet):
    """ Download sheet template. """
    dst_file = None

    if sheet == 'tcs':
        dst_file = os.path.join(PERSISTENCE_DIR, 'sheets/tcs.xls')
    elif sheet == 'buyer':
        dst_file = os.path.join(PERSISTENCE_DIR, 'sheets/buyer.xls')
    elif sheet == 'wide':
        dst_file = os.path.join(PERSISTENCE_DIR, 'sheets/wide.xls')

    if not dst_file:
        raise Http404('未知文件模板.')

    with open(dst_file, 'rb') as xl_handler:
        response = HttpResponse(xl_handler, content_type='application/vnd.ms-excel')
        return response


def dsl_list_display_foreign_fields(request):
    """ Generate py codes to show all related fields in EBOM admin class. """
    # dependent field template
    dep_field_makeup = '''
def get_{model_name}_{field_name}(self, obj):
    """ {model_verbose_name}, {field_verbose_name} """
    _ = self

    if hasattr(obj, '{rel_name}'):
        rel_obj = obj.{rel_name}

        if hasattr(rel_obj, '{field_name}'):
            return rel_obj.{field_name}

    return None

get_{model_name}_{field_name}.short_description = '{model_verbose_name}/{field_verbose_name}'

'''
    dsl_str = ''
    list_display_fields = []

    # specify model
    sp_model_name = request.GET.get('mn')

    def match_sp_model_name(_name: str):
        if not sp_model_name:
            return True
        else:
            if sp_model_name.upper() == _name.upper():
                return True
            else:
                return False

    # get all inbound models
    for name, ib_model in inspect.getmembers(models):
        if inspect.isclass(ib_model) and name[0: 7] == 'Inbound' and match_sp_model_name(name):

            # get meta class
            meta_cls = getattr(ib_model, '_meta')

            # all fields
            fields = meta_cls.get_fields()

            # related query name
            rel_name = meta_cls.get_field('bom').related_query_name()

            # makeup dsl string
            for field in fields:
                field_name = field.name

                if field_name not in ('id', 'bom') and field_name[1] != '_':
                    list_display_fields.append(
                        f'get_{meta_cls.model_name}_{field_name}'
                    )

                    context = {
                        'model_name': meta_cls.model_name,
                        'model_verbose_name': meta_cls.verbose_name,
                        'field_name': field_name,
                        'field_verbose_name': field.verbose_name,
                        'rel_name': rel_name,
                    }

                    dsl_str += dep_field_makeup.format(**context)

    dsl_str += str(list_display_fields)

    return HttpResponse(dsl_str, content_type='text/plain')


def download_wide_table(request, nl_mapping_id):
    """ Download wide table. """
    all_fields = WideTable.list_display
    concerned_fields = [e for e in all_fields if e not in ('label',)]

    # native fields are ones of Ebom class
    is_native = []
    header = []
    ebom_fields = dict([
        (e.name, e.verbose_name if hasattr(e, 'verbose_name') else e.name)
        for e in models.Ebom._meta.get_fields()
    ])

    for field in concerned_fields:
        if not hasattr(WideTable, field):
            if field in ebom_fields:
                is_native.append(True)
                header.append(ebom_fields[field])
        else:
            _method = getattr(WideTable, field)

            if field[0: 4] == 'get_' and callable(_method):
                is_native.append(False)
                header.append(_method.short_description)

    assert len(concerned_fields) == len(is_native)

    # initialize a wide table object
    wide_table_object = WideTable(models.Ebom, wide_table_dummy_param)

    # export two-dimensional array
    wide_table_matrix = [header]
    ebom_objects = models.Ebom.objects.filter(label__id=nl_mapping_id)

    for ebom_object in ebom_objects:
        # a row for wide table
        wide_table_row = []
        index = 0

        for field in concerned_fields:
            if is_native[index]:
                field_or_fk = getattr(ebom_object, field)

                if isinstance(field_or_fk, Model):
                    wide_table_row.append(str(field_or_fk))
                else:
                    wide_table_row.append(field_or_fk)

            else:
                method = getattr(wide_table_object, field)
                wide_table_row.append(method(ebom_object))

            index += 1

        wide_table_matrix.append(wide_table_row)

    # download file name
    label = models.NominalLabelMapping.objects.get(pk=nl_mapping_id)

    return django_excel.make_response_from_array(wide_table_matrix, 'xls', file_name=str(label))


def clear_label_session(request):
    """ Clear session of label. """
    if 'label' in request.session:
        request.session.pop('label')

    return redirect(reverse(f'admin:costsummary_{models.Ebom._meta.model_name}_changelist'))


def dsl_parse_wide_schema(request):
    """ Schema to parse wide table. """
    # generate header
    all_fields = WideTable.list_display
    concerned_fields = [e for e in all_fields if e not in ('label',)]

    # native fields are ones of Ebom class
    is_native = []
    header = []
    ebom_fields = dict([
        (e.name, e.verbose_name if hasattr(e, 'verbose_name') else e.name)
        for e in models.Ebom._meta.get_fields()
    ])

    for field in concerned_fields:
        if not hasattr(WideTable, field):
            if field in ebom_fields:
                is_native.append(True)
                header.append(ebom_fields[field])
        else:
            _method = getattr(WideTable, field)

            if field[0: 4] == 'get_' and callable(_method):
                is_native.append(False)
                header.append(_method.short_description)

    assert len(concerned_fields) == len(is_native)

    # wide table header
    WIDE_HEADER = []

    for i in range(len(concerned_fields)):
        skip = False

        if is_native[i]:
            model_name = 'ebom'
            field_name = concerned_fields[i]
        else:
            model_field_name = concerned_fields[i][4:]

            if model_field_name[0: 7] == 'inbound':
                model_name = model_field_name[0: model_field_name.find('_')]
                field_name = model_field_name[model_field_name.find('_') + 1:]
            else:
                model_name = 'ebom'
                field_name = model_field_name
                skip = True

        model_class = apps.get_model('costsummary', model_name)
        if hasattr(model_class, f'{field_name}_choice'):
            match_display = True
        else:
            match_display = False

        WIDE_HEADER.append({
            'r_offset': 0,
            'ex_header': header[i],
            'in_header': concerned_fields[i],
            'model_name': model_name,
            'field_name': field_name,
            'skip': skip,
            'match_display': match_display
        })

    # print(WIDE_HEADER)
    for i in range(len(WIDE_HEADER)):
        WIDE_HEADER[i]['ex_header'] = WIDE_HEADER[i]['ex_header'].upper()  # upper-case

    output_str = ', \n'.join([str(e) for e in WIDE_HEADER])

    return HttpResponse(output_str, content_type='text/plain')
