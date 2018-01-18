from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import connection as RawConnection
from django import forms

import django_excel

from . import models
from .dumps import InitializeData


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


class TestUploadFileForm(forms.Form):
    """ Single file field form. """
    file = forms.FileField()


def test_upload(request):
    """ Test upload view for excel files. """
    if request.method == "POST":
        form = TestUploadFileForm(request.POST, request.FILES)

        if form.is_valid():

            file_handler = request.FILES['file']
            return django_excel.make_response(file_handler.get_sheet(), "xlsx", file_name="download")
    else:
        form = TestUploadFileForm()

    context = {
        'form': form,
        'title': 'Excel file upload and download example',
        'header': 'Please choose any excel file from your cloned repository:'
    }

    return render(request, 'costsummary/test_upload_form.html', context)


def import_data(request):
    if request.method == "POST":
        form = TestUploadFileForm(request.POST, request.FILES)

        def choice_func(row):
            q = models.Question.objects.filter(slug=row[0])[0]
            row[0] = q
            return row
        if form.is_valid():
            request.FILES['file'].save_book_to_database(
                models=[models.Question, models.Choice],
                initializers=[None, choice_func],
                mapdicts=[
                    ['question_text', 'pub_date', 'slug'],
                    ['question', 'choice_text', 'votes']]
            )
            return redirect('handson_view')
        else:
            return HttpResponseBadRequest()
    else:
        form = TestUploadFileForm()
    return render(
        request,
        'costsummary/test_upload_form.html',
        {
            'form': form,
            'title': 'Import excel data into database example',
            'header': 'Please upload sample-data.xls:'
        })


def handson_table(request):
    return django_excel.make_response_from_tables(
        [models.Question, models.Choice], 'test_handsontable.html')


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
