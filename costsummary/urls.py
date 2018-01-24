from django.conf.urls import url

from . import views


urlpatterns = [
    # mute these after deployment
    url(r'^initialize/tecnum$', views.initialize_data, {'data': 'tec-num'}),
    url(r'^initialize/nl$', views.initialize_data, {'data': 'nl'}),
    url(r'^initialize/supplier', views.initialize_data, {'data': 'supplier'}),

    url(r'^sheet/tcs$', views.download_sheet_template, {'sheet': 'tcs'}),
    url(r'^sheet/buyer$', views.download_sheet_template, {'sheet': 'buyer'}),

    url(r'^entry$', views.group_ebom_by_label, name='entry')
]
