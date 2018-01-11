from django.shortcuts import render
from django.http import HttpResponse
from django import forms

import django_excel

from .dumps import InitializeData


# Create your views here.
def initialize_data(request, data):
    """ Load initial csv-formatted data. """
    # call dump functions
    row_count = None

    if data == 'tec-num':
        row_count = InitializeData.load_initial_tec_num()

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
