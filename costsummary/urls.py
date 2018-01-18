from django.conf.urls import url

from . import views


urlpatterns = [
    # mute these after deployment
    url(r'^initialize/tecnum$', views.initialize_data, {'data': 'tec-num'}),
    url(r'^initialize/nl$', views.initialize_data, {'data': 'nl'}),

    url(r'^entry$', views.group_ebom_by_label, name='entry'),

    # test functions
    url(r'^test/upload$', views.test_upload),
    url(r'^test/import/', views.import_data, name="import"),
    url(r'^test/handson_view/', views.handson_table, name="handson_view"),
]
