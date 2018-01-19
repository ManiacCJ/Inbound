import os

from django.http import HttpResponse
from django.db import connection as RawConnection

from . import models
from .dumps import InitializeData, PERSISTENCE_DIR


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
    if sheet == 'tcs':
        dst_file = os.path.join(PERSISTENCE_DIR, 'sheets/tcs.xls')

    with open(dst_file, 'rb') as xl_handler:
        response = HttpResponse(xl_handler, content_type='application/vnd.ms-excel')
        return response
