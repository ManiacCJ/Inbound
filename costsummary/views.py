# from django.shortcuts import Http404
from django.http import HttpResponse

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
